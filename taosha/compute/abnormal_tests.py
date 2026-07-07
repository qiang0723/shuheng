"""淘沙 · compute · BMP + ADJ-BMP(KP2010)截面检验(切片2 item 2,主检验)。

spec §6 主检验(冻结原文):
  **ADJ-BMP(Kolari–Pynnönen 2010)= BMP × √[(1−ρ̄)/(1+(n−1)ρ̄)];ρ̄ 按行业内估计。**
口径④(人拍 2026-07-07):ρ̄ 行业分组键 = entity_master 的 tushare industry。

两段:
  (A) BMP(=estudy2 `boehmer`)——**对台锚定**,逐点对齐 estudy2 0.10.0 parametric_tests.R:
      SAR_iτ = AR_iτ / [ sd(估计窗AR_i) × √(1 + 1/L_i + (rm_iτ − x̄_i)² / Sxx_i) ]   (:904-908)
      BMP_τ  = mean_i(SAR_iτ) / sd_i(SAR_iτ, ddof=1) × √N_τ                          (:931-933)
      (sd 均 ddof=1;N_τ=当日非缺证券数)。
  (B) ADJ-BMP(KP2010)——**我方扩展**(estudy2 0.10.0 无 KP 实现,只到 BMP);
      adj_stat = BMP × √[(1−ρ̄)/(1+(n−1)ρ̄)],ρ̄=同行业证券对估计窗 AR 的平均 Pearson 相关。
      对台:estudy2 帮不上 → 手算复核(item 2/4)。

红线:纯函数;禁零填充(缺项 None,不入截面);不发明口径。
⚠ spec 行88"R estudy2(含KP实现)"与 estudy2 0.10.0 实物(无 KP)打架,已上报待裁;
  在裁定前,ADJ-BMP 对台以手算复核为准(不以 estudy2 为 KP 参照)。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Hashable, Optional, Sequence

Num = Optional[float]


@dataclass
class SecurityEvent:
    """单证券的事件观测(供 BMP/ADJ-BMP)。所有序列按事件时 τ 对齐、等长。"""
    est_ar_sd: float                      # sd(估计窗AR,ddof=1)= market_model.SimFit.est_ar_sd
    L: int                                # 估计样本数(delta)
    x_bar: float                          # 估计窗 regressor 均值
    sxx: float                            # Σ(x−x̄)² 于估计窗
    event_market: Sequence[Num]           # regressor 收益 per τ
    event_abnormal: Sequence[Num]         # AR per τ
    industry: Hashable                    # tushare industry(ρ̄ 分组键,口径④)
    est_ar_by_date: dict = field(default_factory=dict)  # {日期: 估计窗AR},供 ρ̄ 同日对齐


def standardized_ar(ev: SecurityEvent) -> list[Num]:
    """SAR per τ(parametric_tests.R:904-908)。est_ar_sd=0 或缺项 → None。"""
    out: list[Num] = []
    for rm, ar in zip(ev.event_market, ev.event_abnormal):
        if ar is None or rm is None or ev.est_ar_sd == 0 or ev.sxx == 0:
            out.append(None)
            continue
        fe = math.sqrt(1.0 + 1.0 / ev.L + (rm - ev.x_bar) ** 2 / ev.sxx)  # 预测误差修正
        out.append(ar / (ev.est_ar_sd * fe))
    return out


def _mean_sd(vals: Sequence[float]) -> tuple[float, float, int]:
    """样本均值、sd(ddof=1)、个数;n<2 时 sd=nan。"""
    n = len(vals)
    m = sum(vals) / n
    if n < 2:
        return m, float("nan"), n
    var = sum((v - m) ** 2 for v in vals) / (n - 1)
    return m, math.sqrt(var), n


def bmp_by_tau(events: Sequence[SecurityEvent]) -> list[dict]:
    """逐 τ 的 BMP 统计量(=estudy2 boehmer bh_stat)。返回每 τ 一个 dict。"""
    sars = [standardized_ar(ev) for ev in events]
    n_tau = len(sars[0]) if sars else 0
    rows = []
    for t in range(n_tau):
        col = [s[t] for s in sars if s[t] is not None]
        if len(col) == 0:
            rows.append({"tau": t, "n": 0, "bmp": None})
            continue
        m, sd, n = _mean_sd(col)
        stat = (m / sd * math.sqrt(n)) if (n >= 2 and sd > 0) else None
        rows.append({"tau": t, "n": n, "sar_mean": m, "sar_sd": sd, "bmp": stat})
    return rows


def rho_bar_within_industry(events: Sequence[SecurityEvent]) -> dict:
    """ρ̄ = 同行业证券对估计窗 AR 的平均 Pearson 相关(spec:'ρ̄ 按行业内估计')。

    仅同行业对入池;每对在两者估计窗日期交集上算相关(需≥3 共同日);跨行业对不计。
    返回 {rho_bar, n_pairs, n_securities, note}。
    """
    n_sec = len(events)
    # 按行业分组
    groups: dict = {}
    for i, ev in enumerate(events):
        groups.setdefault(ev.industry, []).append(i)

    corrs: list[float] = []
    for _ind, idxs in groups.items():
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                ei, ej = events[idxs[a]], events[idxs[b]]
                common = sorted(set(ei.est_ar_by_date) & set(ej.est_ar_by_date))
                if len(common) < 3:
                    continue
                xs = [ei.est_ar_by_date[d] for d in common]
                ys = [ej.est_ar_by_date[d] for d in common]
                r = _pearson(xs, ys)
                if r is not None:
                    corrs.append(r)
    rho_bar = sum(corrs) / len(corrs) if corrs else 0.0
    note = ("ρ̄=同行业对估计窗AR平均Pearson相关(≥3共同日);无同行业有效对→ρ̄=0("
            "退化为未校正BMP,报告须注明)") if not corrs else "ρ̄按行业内估计(口径④:tushare industry)"
    return {"rho_bar": rho_bar, "n_pairs": len(corrs), "n_securities": n_sec, "note": note}


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy)


def kp2010_factor(rho_bar: float, n: int) -> float:
    """KP2010 校正因子 √[(1−ρ̄)/(1+(n−1)ρ̄)](spec §6 冻结)。"""
    denom = 1.0 + (n - 1) * rho_bar
    if denom <= 0:
        raise ValueError(f"KP2010 因子分母非正(1+(n−1)ρ̄={denom},ρ̄={rho_bar},n={n})")
    return math.sqrt((1.0 - rho_bar) / denom)


def adj_bmp_by_tau(events: Sequence[SecurityEvent]) -> dict:
    """ADJ-BMP:对每 τ 的 BMP 乘 KP2010 因子。ρ̄ 按行业内估计,n=当 τ 参与证券数。"""
    bmp = bmp_by_tau(events)
    rho = rho_bar_within_industry(events)
    rho_bar = rho["rho_bar"]
    rows = []
    for r in bmp:
        if r["bmp"] is None or r["n"] < 1:
            rows.append({**r, "kp_factor": None, "adj_bmp": None})
            continue
        f = kp2010_factor(rho_bar, r["n"])
        rows.append({**r, "kp_factor": f, "adj_bmp": r["bmp"] * f})
    return {"rho": rho, "rows": rows}


if __name__ == "__main__":
    # ── 自检(全手算可复核)──────────────────────────────────────────────────
    # 构造 3 证券、单 τ,直接给定使 SAR 已知的参数:令 est_ar_sd=1, L 极大, x̄=0, sxx 极大
    # → 预测误差修正 ≈ 1,故 SAR ≈ AR。取 AR = [1.0, 2.0, 3.0]。
    big = 1e12
    def mk(ar, ind, estar):
        return SecurityEvent(est_ar_sd=1.0, L=int(big), x_bar=0.0, sxx=big,
                             event_market=[0.0], event_abnormal=[ar], industry=ind,
                             est_ar_by_date=estar)
    evs = [mk(1.0, "A", {1: 0.1, 2: -0.1, 3: 0.2, 4: -0.2}),
           mk(2.0, "A", {1: 0.1, 2: -0.1, 3: 0.2, 4: -0.2}),   # 与上完全相关 → r=1
           mk(3.0, "B", {1: 0.0, 2: 0.05, 3: -0.05, 4: 0.1})]
    b = bmp_by_tau(evs)
    # SAR≈AR=[1,2,3]; mean=2, sd(ddof1)=1, N=3 → BMP=2/1*√3=2√3
    assert b[0]["n"] == 3 and abs(b[0]["bmp"] - 2 * math.sqrt(3)) < 1e-6, b
    # ρ̄:同行业对仅 (A,A) 一对,AR 序列完全相同 → r=1;B 组单只不成对 → ρ̄=1.0
    rho = rho_bar_within_industry(evs)
    assert rho["n_pairs"] == 1 and abs(rho["rho_bar"] - 1.0) < 1e-12, rho
    # KP 因子:ρ̄=1 → √[(1−1)/(1+2·1)] = 0 → adj_bmp=0(极端聚集完全相关,校正到 0)
    adj = adj_bmp_by_tau(evs)
    assert abs(adj["rows"][0]["adj_bmp"] - 0.0) < 1e-12, adj["rows"][0]
    # ρ̄=0.5,n=4 手算:√[(1−.5)/(1+3·.5)] = √(.5/2.5)=√.2
    assert abs(kp2010_factor(0.5, 4) - math.sqrt(0.2)) < 1e-12
    print("abnormal_tests.py 自检 OK:BMP=2√3 / ρ̄行业内(A对=1) / KP因子手算一致(ρ̄=1→0, ρ̄=.5,n4→√.2)")
