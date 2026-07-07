"""淘沙 · compute · Corrado(1989) 秩检验(切片2 稳健性一,spec §6;S2-Q 裁决补建)。

非参数秩检验,对非正态与事件诱发方差稳健。与 BMP/ADJ-BMP(参数、截面)互补;
spec §6"三法方向一致才确认效应",本模块供"方向"之一。

方法(Corrado 1989 / Corrado & Zivney 1992 标准式):
  1. 每证券 i 在**组合样本**(估计窗 ∪ 事件窗)上对 AR 排名 rank_it(平均秩处理并列)。
     标准化秩 K_it = rank_it / (T_i + 1)  ∈(0,1),零假设下 E[K]=0.5。
  2. 逐相对位置 p 的截面均值偏差 Kbar_p = mean_i(K_ip − 0.5)(仅计有效证券)。
  3. 尺度 S_K = sqrt( (1/L) Σ_p Kbar_p² ),p 遍历全组合位置 L(估计窗+事件窗)。
  4. 单日:t_rank_τ = Kbar_{eventτ} / S_K;窗口累计:Σ_τ Kbar_τ / (S_K·√W)。

红线:纯函数;禁零填充(缺项不入排名/不入截面);无 estudy2 对台(item2 只锚 BMP),
自检以手算复核 + 已知构造验证。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

Num = Optional[float]


@dataclass
class RankSecurity:
    """单证券秩检验输入。est_ar 按相对位置(-250..-91)排;event_ar 按 τ=0..W 排;None=缺。"""
    est_ar: Sequence[Num]
    event_ar: Sequence[Num]


def _avg_ranks(vals: list[float]) -> list[float]:
    """平均秩(并列取均值),秩从 1 起。"""
    order = sorted(range(len(vals)), key=lambda k: vals[k])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + 1 + j + 1) / 2.0        # 1-based 平均秩
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def corrado_rank(securities: Sequence[RankSecurity], main_len: int, robust_len: int) -> dict:
    """Corrado 秩检验。返回 per-τ t_rank + 主/稳健窗累计 t_rank + 方向。"""
    n_event = robust_len
    # 每证券:组合样本排名 → K−0.5,按位置存(est 段 + event 段)
    est_len = len(securities[0].est_ar) if securities else 0
    total_pos = est_len + n_event
    # Kbar 累加器:位置 → [和, 计数]
    acc = [[0.0, 0] for _ in range(total_pos)]
    for s in securities:
        combined = list(s.est_ar) + list(s.event_ar)
        idx_valid = [p for p, v in enumerate(combined) if v is not None]
        if len(idx_valid) < 2:
            continue
        vals = [combined[p] for p in idx_valid]
        ranks = _avg_ranks(vals)
        ti = len(vals)
        for p, r in zip(idx_valid, ranks):
            k = r / (ti + 1) - 0.5
            acc[p][0] += k
            acc[p][1] += 1
    kbar = [(a[0] / a[1]) if a[1] > 0 else None for a in acc]
    # 尺度 S_K:全组合位置的 Kbar² 均值(仅计有位置)
    present = [kb for kb in kbar if kb is not None]
    if len(present) < 2:
        return {"s_k": None, "by_tau": [], "main": None, "robust": None}
    s_k = (sum(kb * kb for kb in present) / len(present)) ** 0.5
    # 事件窗位置 = est_len + τ
    by_tau = []
    for tau in range(n_event):
        kb = kbar[est_len + tau]
        t = (kb / s_k) if (kb is not None and s_k > 0) else None
        by_tau.append({"tau": tau, "kbar": kb, "t_rank": t})

    def _cum(win_len):
        kbs = [kbar[est_len + tau] for tau in range(win_len)]
        if any(kb is None for kb in kbs) or s_k <= 0:
            return None
        return sum(kbs) / (s_k * win_len ** 0.5)

    main = _cum(main_len)
    robust = _cum(robust_len)
    return {"s_k": s_k, "by_tau": by_tau,
            "main": {"t_rank": main, "direction": _sign(main)},
            "robust": {"t_rank": robust, "direction": _sign(robust)}}


def _sign(x):
    if x is None:
        return 0
    return 1 if x > 0 else (-1 if x < 0 else 0)


if __name__ == "__main__":
    # 自检1:构造 τ=0 全证券 AR 显著高于估计窗 → τ=0 秩偏高、t_rank>0、方向 +1。
    import random
    rng = random.Random(7)
    secs = []
    for _ in range(20):
        est = [rng.gauss(0, 0.01) for _ in range(160)]
        ev = [0.05] + [rng.gauss(0, 0.01) for _ in range(5)]   # τ=0 大正 AR
        secs.append(RankSecurity(est, ev))
    r = corrado_rank(secs, main_len=3, robust_len=6)
    assert r["by_tau"][0]["t_rank"] > 2.0, r["by_tau"][0]        # τ=0 显著正
    assert r["main"]["direction"] == 1, r["main"]
    # 自检2:无效应尺寸检验(单次 |t| 天然有尾;用 300 次拒绝率≈α 验尺寸,确定性)
    reps, rej = 300, 0
    for _ in range(reps):
        s0 = [RankSecurity([rng.gauss(0, 0.01) for _ in range(160)],
                           [rng.gauss(0, 0.01) for _ in range(6)]) for _ in range(25)]
        t0 = corrado_rank(s0, 3, 6)["by_tau"][0]["t_rank"]
        if abs(t0) > 1.96:
            rej += 1
    size = rej / reps
    assert 0.02 <= size <= 0.11, f"秩检验 τ=0 尺寸失准: {size}"    # ≈0.05,容采样
    # 自检3:平均秩并列
    assert _avg_ranks([3.0, 1.0, 1.0, 2.0]) == [4.0, 1.5, 1.5, 3.0]
    # 自检4:禁零填充——缺项不入排名(T_i 减少),不制造 0 收益
    s = RankSecurity([None] * 100 + [0.01] * 60, [0.05] + [0.0] * 5)
    r4 = corrado_rank([s] * 5, 3, 6)
    assert r4["s_k"] is not None
    print("rank_test.py 自检 OK:τ=0 显著正(t_rank>2)/ 无效应≈0 / 平均秩并列 / 禁零填充")
