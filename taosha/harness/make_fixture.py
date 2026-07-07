"""对台 fixture 生成器(确定性种子)。产出估计窗/事件窗齐备的合成价格,供 estudy2 与我方同读。

设计要点(服务 item 2/3/5/6):
  - N 只证券 + 1 市场指数,~320 交易日(真实业务日,estudy2 需 Date)。
  - 收益 r_i = α_i + β_i·r_m + ε_i(SIM 真结构);价格 P_t = P_{t-1}·exp(r_t)(对数收益可精确回收)。
  - 单只证券注入**停牌缺口**(连续 NA)→ 测 multi_day 跨缺口对齐(item 3)+ 覆盖计数(item 6)。
  - 全部证券**共享同一事件日**(聚集)→ 测 BMP 截面(item 2);分两行业 → 供 ρ̄ 行业内估计(口径④)。
  - 事件日注入已知异常收益 → 双跑 AR/BMP 有信号可比。
输出 CSV:prices(date,MKT,S1..SN)+ meta(event_start/end, est_start/end 日期, 行业, 缺口位置)。
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import random

# ── 冻结的窗口几何(对齐 spec §5 估计窗;fixture 可用真实 160 日窗)──────────────
EST_OFF_START, EST_OFF_END = -250, -91      # 前250至前91(含)=160 日
N_DAYS = 340
EVENT_IDX = 300                              # 事件日索引(前有 ≥250 交易日)
EVENT_LEN = 6                                # 事件窗 τ=0..+5([0,+5] 稳健窗)
GAP_SEC, GAP_START, GAP_LEN = "S3", 130, 3   # S3 在索引130起停牌3日(落估计窗内)


def _biz_days(start: dt.date, n: int) -> list[dt.date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def generate(n_sec: int = 6, seed: int = 20260707) -> dict:
    rng = random.Random(seed)
    dates = _biz_days(dt.date(2022, 1, 3), N_DAYS)

    # 市场对数收益
    rm = [rng.gauss(0.0004, 0.011) for _ in range(N_DAYS)]

    # 两行业各半,β/σ 逐只不同;行业注入共同因子 → 截面相关(供 ρ̄/尺寸检验的对台侧也有相关)
    industries = ["银行" if i < n_sec // 2 else "地产" for i in range(n_sec)]
    ind_factor = {ind: [rng.gauss(0, 0.004) for _ in range(N_DAYS)] for ind in set(industries)}

    secs: dict[str, list] = {}
    for i in range(n_sec):
        name = f"S{i+1}"
        beta = 0.8 + 0.1 * i
        alpha = 0.0
        sigma = 0.008 + 0.001 * i
        f = ind_factor[industries[i]]
        r = [alpha + beta * rm[t] + f[t] + rng.gauss(0, sigma) for t in range(N_DAYS)]
        # 事件日注入已知异常收益 +3%(τ=0),使 BMP 有信号
        r[EVENT_IDX] += 0.03
        # 价格 = 累乘 exp(对数收益);首日基准价 100
        px = [100.0]
        for t in range(N_DAYS):
            px.append(px[-1] * math.exp(r[t]))
        px = px[1:]                          # 长度 N_DAYS,与 dates 对齐
        secs[name] = px

    # 市场价格
    mkt_px, p = [], 100.0
    for t in range(N_DAYS):
        p *= math.exp(rm[t])
        mkt_px.append(p)

    # S3 停牌缺口:置 NA(空串)
    for t in range(GAP_START, GAP_START + GAP_LEN):
        secs[GAP_SEC][t] = None

    meta = {
        "seed": seed, "n_days": N_DAYS, "n_sec": n_sec,
        "event_idx": EVENT_IDX, "event_len": EVENT_LEN,
        "date_est_start": dates[EVENT_IDX + EST_OFF_START].isoformat(),
        "date_est_end": dates[EVENT_IDX + EST_OFF_END].isoformat(),
        "date_event_start": dates[EVENT_IDX].isoformat(),
        "date_event_end": dates[EVENT_IDX + EVENT_LEN - 1].isoformat(),
        "industries": {f"S{i+1}": industries[i] for i in range(n_sec)},
        "gap": {"sec": GAP_SEC, "start_idx": GAP_START, "len": GAP_LEN},
        "injected_ar_tau0": 0.03,
    }
    return {"dates": dates, "market": mkt_px, "secs": secs, "meta": meta}


def write_csv(data: dict, prices_path: str, meta_path: str) -> None:
    dates, mkt, secs = data["dates"], data["market"], data["secs"]
    sec_names = list(secs)
    with open(prices_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "MKT"] + sec_names)
        for t, d in enumerate(dates):
            row = [d.isoformat(), f"{mkt[t]:.10f}"]
            for s in sec_names:
                v = secs[s][t]
                row.append("" if v is None else f"{v:.10f}")
            w.writerow(row)
    with open(meta_path, "w") as fh:
        json.dump(data["meta"], fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--seed", type=int, default=20260707)
    ap.add_argument("--n-sec", type=int, default=6)
    a = ap.parse_args()
    d = generate(n_sec=a.n_sec, seed=a.seed)
    write_csv(d, a.prices, a.meta)
    print(f"fixture written: {a.prices} ({d['meta']['n_days']} 日 × {a.n_sec} 证券) meta={a.meta}")
    print("窗口:", json.dumps(d["meta"], ensure_ascii=False))
