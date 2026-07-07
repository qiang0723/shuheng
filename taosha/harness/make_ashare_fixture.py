"""A股口径合成 fixture 生成器(确定性种子)· 切片2 item 7/8。

与对台 fixture(make_fixture.py,锚 estudy2、不动)**分家**:此 fixture 服务 A股口径件——
产出《explore_reader 列契约》同形状的 prices.csv + events.csv,供 SyntheticReader 读、引擎跑。

刻意注入(供 item 6/7/8 验收):
  - **≥30 事件**(48 证券×1 事件),否则样本量闸恒 INSUFFICIENT。
  - **跨年**(事件散布 2020–2023)→ 剔除率按年份可分解(item 7)。
  - **跨越 2020-08-24**:含创业板事件在 regime 前/后各若干 → 边界处理(item 8)。
  - **四行业**(供 ρ̄ 行业内估计,口径④);四板块(main/chinext/star/ST)。
  - **停牌**:①部分证券估计窗内停牌缺口(multi_day 跨缺口 + 覆盖计数 item 6);
    ②指定子集事件落停牌期(item 7 剔除,散布多年);③一字板 T+1(item 8 顺延)。
  - **覆盖不足**:1–2 证券估计窗长停牌 → 覆盖门槛剔除(item 6/7)。
  - 事件日注入已知异常收益 +3%(τ=0=T+1)→ BMP 有信号。

价格 P_t = P_{t-1}·exp(r_t),SIM 真结构 r=α+β·rm+行业因子+ε(对数收益可精确回收)。
全期 < holdout 2024-07-01(合成域验收,holdout 隔离归 Q3/切片3)。
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import random

CAL_START = dt.date(2019, 1, 2)   # 早开 → 2020 年事件也有 ≥250 日估计窗
N_TRADING = 1270                  # ≈5 年交易日,末端仍 < 2024-07-01
N_SEC = 48
EST_BACK_FAR, EST_BACK_NEAR = 250, 91   # 估计窗 [T-250, T-91]
EVENT_TAIL = 8                    # 事件后需 ≥8 交易日(容一字板顺延 + 稳健窗 T+6)
INJECT_AR_TAU0 = 0.03            # τ=0(T+1)注入异常收益
INDUSTRIES = ("银行", "地产", "医药", "科技")


def _biz_days(start: dt.date, n: int) -> list[dt.date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def _assign_board(i: int) -> tuple[str, bool]:
    """板块 + ST 分配:混合 main/chinext/star,末尾几只 ST(主板)。返回 (board, is_st)。"""
    if i >= N_SEC - 6:
        return "main", True           # 末 6 只 ST(主板)
    r = i % 5
    if r in (0, 1):
        return "main", False
    if r in (2, 3):
        return "chinext", False       # 创业板占比高 → 供 regime straddle
    return "star", False


def generate(seed: int = 20260707) -> dict:
    rng = random.Random(seed)
    dates = _biz_days(CAL_START, N_TRADING)
    date_idx = {d: k for k, d in enumerate(dates)}
    regime_date = dt.date(2020, 8, 24)

    # 市场对数收益(全市场等权基准的近似 driver;引擎另按池/全市场等权算真基准)
    rm = [rng.gauss(0.0003, 0.011) for _ in range(N_TRADING)]
    ind_factor = {ind: [rng.gauss(0, 0.004) for _ in range(N_TRADING)] for ind in INDUSTRIES}

    # 事件位置:散布于 [260, N_TRADING-EVENT_TAIL];按年份轮转以覆盖 2020–2023。
    # 先按 board 分配,创业板证券事件优先落在 regime 前后以制造 straddle。
    lo, hi = EST_BACK_FAR + 12, N_TRADING - EVENT_TAIL
    idx_by_year: dict[int, list[int]] = {}
    for k in range(lo, hi):
        idx_by_year.setdefault(dates[k].year, []).append(k)
    years = sorted(y for y in idx_by_year if y >= 2020)

    secs: dict[str, dict] = {}
    events: list[dict] = []
    # 指定注入子集(确定性)
    suspend_at_event = set(range(6))          # 前 6 只:事件落停牌期 → item7 剔除(散布多年)
    one_word_at_event = {6, 7}                # 2 只:T+1 一字板 → item8 顺延
    coverage_short = {8}                      # 1 只:估计窗长停牌 → 覆盖不足剔除
    est_gap = set(range(10, 30))              # 一批:估计窗内短停牌缺口(跨缺口 + 覆盖计数)

    regime_idx = date_idx.get(regime_date) or next(k for k, d in enumerate(dates) if d >= regime_date)

    for i in range(N_SEC):
        name = f"A{i+1:02d}"
        board, is_st = _assign_board(i)
        ind = INDUSTRIES[i % len(INDUSTRIES)]
        beta = 0.7 + 0.02 * i
        sigma = 0.008 + 0.0005 * (i % 7)
        f = ind_factor[ind]
        r = [0.0 + beta * rm[t] + f[t] + rng.gauss(0, sigma) for t in range(N_TRADING)]

        # 事件位置:创业板 straddle → 交替落 regime 前/后;其余按年份轮转
        if board == "chinext":
            evk = (regime_idx - 40 - i) if (i % 2 == 0) else (regime_idx + 30 + i)
            evk = max(lo, min(hi - 1, evk))
        else:
            yr = years[i % len(years)]
            pool = idx_by_year[yr]
            evk = pool[(i * 7) % len(pool)]
        # 注入 τ=0=T+1 异常收益(evk+1)
        if evk + 1 < N_TRADING:
            r[evk + 1] += INJECT_AR_TAU0

        # 价格累乘
        px = [100.0]
        for t in range(N_TRADING):
            px.append(px[-1] * math.exp(r[t]))
        px = px[1:]
        close: list = list(px)
        suspended = [False] * N_TRADING
        limit_status = ["none"] * N_TRADING

        # 估计窗内短停牌缺口(index evk-200..evk-197)→ 跨缺口 + 覆盖计数
        if i in est_gap:
            for t in range(evk - 200, evk - 197):
                close[t], suspended[t] = None, True
        # 覆盖不足:估计窗内长停牌(60 日)→ 有效日 < 112
        if i in coverage_short:
            for t in range(evk - 230, evk - 170):
                close[t], suspended[t] = None, True
        # 事件落停牌期:[T, T+2] 停牌 → item7 剔除
        if i in suspend_at_event:
            for t in range(evk, evk + 3):
                if t < N_TRADING:
                    close[t], suspended[t] = None, True
        # 一字板 T+1:limit_status=one_word(不可成交)→ item8 顺延
        if i in one_word_at_event and evk + 1 < N_TRADING:
            limit_status[evk + 1] = "one_word"

        secs[name] = {"close": close, "suspended": suspended, "limit": limit_status,
                      "board": board, "is_st": is_st, "industry": ind}
        events.append({
            "ts_code": name, "event_id": f"E{i+1:04d}",
            "first_ann_date": dates[evk].isoformat(),
            "event_type_layer": "预喜" if i % 3 else "预亏",
            "snapshot_batch": "SYNTH",
        })

    # 市场价格(供参考;引擎不直接用,基准另算)
    mkt_px, p = [], 100.0
    for t in range(N_TRADING):
        p *= math.exp(rm[t]); mkt_px.append(p)

    meta = {
        "seed": seed, "n_trading": N_TRADING, "n_sec": N_SEC, "n_events": len(events),
        "cal_start": CAL_START.isoformat(), "cal_end": dates[-1].isoformat(),
        "regime_date": regime_date.isoformat(),
        "inject": {"suspend_at_event": sorted(suspend_at_event),
                   "one_word_at_event": sorted(one_word_at_event),
                   "coverage_short": sorted(coverage_short),
                   "est_gap": sorted(est_gap), "ar_tau0": INJECT_AR_TAU0},
    }
    return {"dates": dates, "market": mkt_px, "secs": secs, "events": events, "meta": meta}


def write_csv(data: dict, prices_path: str, events_path: str, meta_path: str) -> None:
    dates, secs = data["dates"], data["secs"]
    with open(prices_path, "w", newline="") as fh:
        w = csv.writer(fh)
        # 契约 §1 列序
        w.writerow(["ts_code", "trade_date", "close", "is_suspended",
                    "limit_status", "board", "is_st", "industry"])
        for name, s in secs.items():
            for t, d in enumerate(dates):
                c = s["close"][t]
                w.writerow([name, d.isoformat(), "" if c is None else f"{c:.10f}",
                            int(s["suspended"][t]), s["limit"][t], s["board"],
                            int(s["is_st"]), s["industry"]])
    with open(events_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ts_code", "event_id", "first_ann_date", "event_type_layer", "snapshot_batch"])
        for e in data["events"]:
            w.writerow([e["ts_code"], e["event_id"], e["first_ann_date"],
                        e["event_type_layer"], e["snapshot_batch"]])
    with open(meta_path, "w") as fh:
        json.dump(data["meta"], fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--seed", type=int, default=20260707)
    a = ap.parse_args()
    d = generate(seed=a.seed)
    write_csv(d, a.prices, a.events, a.meta)
    m = d["meta"]
    print(f"A股 fixture: {m['n_sec']} 证券 × {m['n_trading']} 交易日,{m['n_events']} 事件 "
          f"({m['cal_start']}..{m['cal_end']});regime={m['regime_date']}")
    print("注入:", json.dumps(m["inject"], ensure_ascii=False))
