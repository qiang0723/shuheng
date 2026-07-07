"""对台我方侧 + 比对:我方 compute 跑同一 fixture,与 estudy2 dump 逐点比对。

对齐规则(get_rates_from_prices.R:164):Close 口径第 i 行收益(0基)贴 dates[i+1](到达日),
跨缺口收益落恢复日。据此我方定位数组 rates[i] ↔ estudy2 日期 dates[i+1]。

比对:收益序列(item3 跨缺口)、SIM α/β/delta、事件窗 AR、BMP(=boehmer);
我方 ADJ-BMP + 手算复核 KP 因子(estudy2 无 KP,附录 E)。输出 max|diff| 与判定。
用法: python -m taosha.harness.run_double <prices.csv> <meta.json> <estudy2_dir> [out.json]
"""
from __future__ import annotations

import csv
import json
import math
import sys

from taosha.compute.returns import log_rates_from_prices
from taosha.compute.market_model import sim_fit
from taosha.compute import abnormal_tests as AT

TOL_RATE = 1e-8
TOL_COEF = 1e-7
TOL_AR = 1e-7
TOL_BMP = 1e-5


def _read_prices(path):
    with open(path) as fh:
        r = csv.reader(fh)
        header = next(r)
        cols = {c: [] for c in header}
        dates = []
        for row in r:
            for c, v in zip(header, row):
                if c == "date":
                    dates.append(v)
                else:
                    cols[c].append(None if v == "" else float(v))
    sec_names = [c for c in header if c not in ("date", "MKT")]
    return dates, cols["MKT"], {s: cols[s] for s in sec_names}, sec_names


def _read_csv_rows(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def _rate_series(prices, dates):
    """我方对数收益 → {到达日: rate}(定位 rates[i]↔dates[i+1])。"""
    rates = log_rates_from_prices(prices, quote="Close", multi_day=True)
    return {dates[i + 1]: rates[i] for i in range(len(rates))}


def run(prices_path, meta_path, estudy2_dir, out_path=None):
    dates, mkt_px, secs_px, sec_names = _read_prices(prices_path)
    meta = json.load(open(meta_path))
    est_s, est_e = meta["date_est_start"], meta["date_est_end"]
    ev_s, ev_e = meta["date_event_start"], meta["date_event_end"]
    industries = meta["industries"]

    # 我方收益(按到达日)
    mkt_r = _rate_series(mkt_px, dates)
    rate_dates = sorted(mkt_r)                                  # 有序到达日列表
    sec_r = {s: _rate_series(secs_px[s], dates) for s in sec_names}

    # ── 比对1:收益序列(与 estudy2 rates_all)────────────────────────────────
    est_rates = {(row["date"]): row for row in _read_csv_rows(f"{estudy2_dir}/rates_estudy2.csv")}
    max_rate_diff = 0.0
    for d in rate_dates:
        er = est_rates.get(d)
        if er is None:
            continue
        for s in ["MKT"] + sec_names:
            ours = (mkt_r if s == "MKT" else sec_r[s]).get(d)
            theirs = er[s]
            theirs = None if theirs in ("", "NA") else float(theirs)
            if ours is None or theirs is None:
                assert ours is None and theirs is None, f"NA 不一致 {s}@{d}: 我={ours} 彼={theirs}"
                continue
            max_rate_diff = max(max_rate_diff, abs(ours - theirs))

    # ── 我方 SIM 拟合 + 事件结构 ─────────────────────────────────────────────
    est_coef = {r["security"]: r for r in _read_csv_rows(f"{estudy2_dir}/coef_estudy2.csv")}
    est_ar = {}
    for r in _read_csv_rows(f"{estudy2_dir}/abnormal_estudy2.csv"):
        est_ar.setdefault(r["security"], {})[r["date"]] = float(r["abnormal"])

    max_coef_diff = 0.0
    max_ar_diff = 0.0
    events = []
    for s in sec_names:
        mkt_arr = [mkt_r[d] for d in rate_dates]
        sec_arr = [sec_r[s].get(d) for d in rate_dates]
        est_mask = [est_s <= d <= est_e for d in rate_dates]
        fit = sim_fit(sec_arr, mkt_arr, est_mask)
        # α/β/delta 比对
        ec = est_coef[s]
        max_coef_diff = max(max_coef_diff, abs(fit.alpha - float(ec["alpha"])),
                            abs(fit.beta - float(ec["beta"])))
        assert fit.delta == int(ec["delta"]), f"delta 不一致 {s}: 我={fit.delta} 彼={ec['delta']}"
        # 事件窗 AR 比对
        ev_idx = [j for j, d in enumerate(rate_dates) if ev_s <= d <= ev_e]
        for j in ev_idx:
            d = rate_dates[j]
            if fit.abnormal[j] is not None and d in est_ar.get(s, {}):
                max_ar_diff = max(max_ar_diff, abs(fit.abnormal[j] - est_ar[s][d]))
        # 组装 SecurityEvent(BMP/ADJ-BMP)
        ev_market = [mkt_arr[j] for j in ev_idx]
        ev_abn = [fit.abnormal[j] for j in ev_idx]
        est_ar_by_date = {rate_dates[j]: fit.abnormal[j]
                          for j, d in enumerate(rate_dates)
                          if est_mask[j] and fit.abnormal[j] is not None}
        events.append(AT.SecurityEvent(
            est_ar_sd=fit.est_ar_sd, L=fit.delta, x_bar=fit.x_bar, sxx=fit.sxx,
            event_market=ev_market, event_abnormal=ev_abn,
            industry=industries[s], est_ar_by_date=est_ar_by_date))

    # ── 比对2:BMP(与 estudy2 boehmer)──────────────────────────────────────
    ev_dates = [d for d in rate_dates if ev_s <= d <= ev_e]
    our_bmp = AT.bmp_by_tau(events)
    est_bmp = {r["date"]: float(r["bh_stat"]) for r in _read_csv_rows(f"{estudy2_dir}/bmp_estudy2.csv")
               if r["bh_stat"] not in ("", "NA")}
    max_bmp_diff = 0.0
    bmp_rows = []
    for t, d in enumerate(ev_dates):
        ours = our_bmp[t]["bmp"]
        theirs = est_bmp.get(d)
        if ours is not None and theirs is not None:
            max_bmp_diff = max(max_bmp_diff, abs(ours - theirs))
        bmp_rows.append({"date": d, "our_bmp": ours, "estudy2_bmp": theirs})

    # ── 我方 ADJ-BMP + 手算复核 KP 因子 ─────────────────────────────────────
    adj = AT.adj_bmp_by_tau(events)
    rho_bar = adj["rho"]["rho_bar"]
    n = adj["rho"]["n_securities"]
    kp_manual = math.sqrt((1 - rho_bar) / (1 + (n - 1) * rho_bar))
    kp_code = AT.kp2010_factor(rho_bar, n)
    kp_ok = abs(kp_manual - kp_code) < 1e-12

    result = {
        "max_rate_diff": max_rate_diff, "max_coef_diff": max_coef_diff,
        "max_ar_diff": max_ar_diff, "max_bmp_diff": max_bmp_diff,
        "bmp_rows": bmp_rows,
        "rho_bar": rho_bar, "n_sec": n, "kp_factor": kp_code,
        "kp_manual_check": kp_ok,
        "adj_bmp_rows": [{"date": ev_dates[i], "adj_bmp": r["adj_bmp"]}
                         for i, r in enumerate(adj["rows"])],
        "verdict": {
            "rates_align": max_rate_diff < TOL_RATE,
            "coef_align": max_coef_diff < TOL_COEF,
            "ar_align": max_ar_diff < TOL_AR,
            "bmp_align": max_bmp_diff < TOL_BMP,
            "kp_manual_check": kp_ok,
        },
    }
    result["verdict"]["ALL_PASS"] = all(result["verdict"].values())

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    if out_path:
        json.dump(result, open(out_path, "w"), ensure_ascii=False, indent=2, default=str)
    return result


if __name__ == "__main__":
    a = sys.argv[1:]
    r = run(a[0], a[1], a[2], a[3] if len(a) > 3 else None)
    sys.exit(0 if r["verdict"]["ALL_PASS"] else 1)
