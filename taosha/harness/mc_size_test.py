"""ADJ-BMP 零假设蒙特卡洛尺寸检验(附录 E3;验收证据必备)。

设计:合成**无效应(真实 AR 期望=0)、截面相关的聚集事件**样本——同行业、同事件日,
注入行业共同因子 f_t(市场模型只回归市场、不含 f → 残差保留 f → 截面相关)。
每次模拟在事件日 τ=0 算 朴素 BMP 与 ADJ-BMP,按 t_{0.975,N-1} 双侧 α=0.05 判拒。

证据要求(E3):朴素 BMP 拒绝率 **> α**(截面相关下假阳性复现);ADJ-BMP 拒绝率 **≈ α**。
一次性模拟(确定性种子)。纯 stdlib。
"""
from __future__ import annotations

import argparse
import json
import math
import random

from taosha.compute.market_model import sim_fit
from taosha.compute import abnormal_tests as AT

# t_{0.975, df} 双侧 α=0.05 临界值(估计窗残差 → estudy2 用 t 分布;此处按截面 df=N-1)
_T_CRIT = {14: 2.144787, 19: 2.093024, 24: 2.063899, 29: 2.045230, 49: 2.009575}


def one_sim(rng: random.Random, n_sec: int, est_len: int,
            sigma_f: float, sigma_e: float) -> tuple[float, float, float]:
    """单次模拟 → (naive_bmp, adj_bmp, rho_bar) 于事件日 τ=0。无注入效应(null)。"""
    total = est_len + 1                       # 估计窗 + 1 事件日
    rm = [rng.gauss(0.0004, 0.011) for _ in range(total)]
    f = [rng.gauss(0.0, sigma_f) for _ in range(total)]   # 行业共同因子(全证券共享)
    est_mask = [t < est_len for t in range(total)]

    events = []
    for i in range(n_sec):
        beta = 0.8 + 0.4 * (i / max(n_sec - 1, 1))         # β∈[0.8,1.2]
        r = [beta * rm[t] + f[t] + rng.gauss(0.0, sigma_e) for t in range(total)]
        fit = sim_fit(r, rm, est_mask)                     # 市场模型只回归 rm,不含 f
        est_ar_by_date = {t: fit.abnormal[t] for t in range(total)
                          if est_mask[t] and fit.abnormal[t] is not None}
        events.append(AT.SecurityEvent(
            est_ar_sd=fit.est_ar_sd, L=fit.delta, x_bar=fit.x_bar, sxx=fit.sxx,
            event_market=[rm[est_len]], event_abnormal=[fit.abnormal[est_len]],
            industry="同行业", est_ar_by_date=est_ar_by_date))

    naive = AT.bmp_by_tau(events)[0]["bmp"]
    adj = AT.adj_bmp_by_tau(events)
    return naive, adj["rows"][0]["adj_bmp"], adj["rho"]["rho_bar"]


def run(n_sec=20, est_len=160, n_sim=2000, sigma_f=0.005, sigma_e=0.0087,
        seed=20260707) -> dict:
    df = n_sec - 1
    tcrit = _T_CRIT.get(df)
    if tcrit is None:
        raise ValueError(f"无 df={df} 的 t 临界值,请在 _T_CRIT 补录(n_sec={n_sec})")
    rng = random.Random(seed)
    naive_rej = adj_rej = 0
    rho_sum = 0.0
    n_valid = 0
    for s in range(n_sim):
        nb, ab, rho = one_sim(rng, n_sec, est_len, sigma_f, sigma_e)
        if nb is None or ab is None:
            continue
        n_valid += 1
        rho_sum += rho
        if abs(nb) > tcrit:
            naive_rej += 1
        if abs(ab) > tcrit:
            adj_rej += 1
    return {
        "n_sec": n_sec, "est_len": est_len, "n_sim": n_sim, "n_valid": n_valid,
        "sigma_f": sigma_f, "sigma_e": sigma_e, "seed": seed,
        "t_crit(df=%d)" % df: tcrit, "alpha": 0.05,
        "rho_bar_mean": rho_sum / n_valid if n_valid else None,
        "naive_bmp_reject_rate": naive_rej / n_valid if n_valid else None,
        "adj_bmp_reject_rate": adj_rej / n_valid if n_valid else None,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-sec", type=int, default=20)
    ap.add_argument("--est-len", type=int, default=160)
    ap.add_argument("--n-sim", type=int, default=2000)
    ap.add_argument("--sigma-f", type=float, default=0.005)
    ap.add_argument("--sigma-e", type=float, default=0.0087)
    ap.add_argument("--seed", type=int, default=20260707)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    res = run(a.n_sec, a.est_len, a.n_sim, a.sigma_f, a.sigma_e, a.seed)
    # 判定:朴素 BMP 显著过度拒绝(>α),ADJ-BMP 回到 α 附近(±0.02 容差)
    res["verdict"] = {
        "naive_over_rejects": res["naive_bmp_reject_rate"] > 0.05 * 1.5,
        "adj_near_alpha": abs(res["adj_bmp_reject_rate"] - 0.05) <= 0.02,
    }
    res["verdict"]["PASS"] = all(res["verdict"].values())
    print(json.dumps(res, ensure_ascii=False, indent=2))
    if a.out:
        json.dump(res, open(a.out, "w"), ensure_ascii=False, indent=2)
