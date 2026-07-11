"""淘沙 · compute · 策略版 BHAR 截面检验(附录B B2 + ADJ-BMP 四件套框架;exp_id 3)。

附录B B2(冻结):策略版收益同样过 ADJ-BMP(以路径净收益替代固定窗 CAR)、样本量闸与门槛校正。
ADJ-BMP 四件套框架(人给,随附录G 执行指令 2026-07-11,STATE 留痕):
  ① 超额 = 路径净收益 − b1 池同跨度买入持有(BHAR;数据组装在 engine/drawdown_strategy);
  ② 标准化 = 估计窗日波动 × √持有日数:SBHAR_i = BHAR_i / (est_ar_sd_i·√H_i)
     (est_ar_sd = SIM 估计窗 AR 日 sd,ADJ-BMP 预置框架同一分母;H = 持有日历交易日数,
     与超额收益累计跨度同轴);截面统计量 = BMP 式 mean/sd·√N,再乘 KP2010 因子
     (=ADJ-BMP;ρ̄ 行业内口径④,因子复用 abnormal_tests.kp2010_factor 单一来源);
  ③ BHAR 右偏 → 附 skewness-adjusted t 稳健项(Hall 1992 变换;Lyon–Barber–Tsai 1999 采用):
     t_sa = √n·(S + γ̂S²/3 + γ̂²S³/27 + γ̂/(6n)),S = x̄/s(s=ddof1),γ̂ = Σ(x−x̄)³/(n·s³);
  ④ 判决权归事件版:本模块只产统计量,不产 verdict 终态(组装侧登记 authority)。

红线:纯函数、纯 stdlib;禁零填充(缺项 None 不入截面);不发明口径。
"""
from __future__ import annotations

import math
from typing import Optional

Num = Optional[float]


def sbhar(bhar: Num, est_ar_sd: Num, h_days: int) -> Num:
    """标准化 BHAR(四件套②):BHAR/(σ_i·√H)。缺项/σ≤0/H<1 → None(禁零填充)。"""
    if bhar is None or est_ar_sd is None or est_ar_sd <= 0 or h_days < 1:
        return None
    return bhar / (est_ar_sd * math.sqrt(h_days))


def _mean_sd(xs: list) -> tuple:
    n = len(xs)
    m = sum(xs) / n
    if n < 2:
        return m, None
    return m, math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def cross_test(sbhars: list, rho_bar: float, kp_factor_fn) -> dict:
    """SBHAR 截面检验(四件套②):z = mean/sd·√N(BMP 式),adj_z = z × KP2010 因子。

    kp_factor_fn = abnormal_tests.kp2010_factor(单一来源注入,compute 内不复制公式)。
    None 项不入截面;n<2 → 统计量 None。"""
    xs = [x for x in sbhars if x is not None]
    n = len(xs)
    if n < 2:
        return {"n": n, "mean": (xs[0] if n else None), "sd": None,
                "z": None, "kp_factor": None, "adj_z": None}
    m, s = _mean_sd(xs)
    z = (m / s * math.sqrt(n)) if s and s > 0 else None
    kp = kp_factor_fn(rho_bar, n) if z is not None else None
    return {"n": n, "mean": m, "sd": s, "z": z, "kp_factor": kp,
            "adj_z": (z * kp) if z is not None else None}


def skewness(xs: list) -> Num:
    """γ̂ = Σ(x−x̄)³/(n·s³),s=ddof1(LBT 1999 口径)。n<3 或 s=0 → None。"""
    n = len(xs)
    if n < 3:
        return None
    m, s = _mean_sd(xs)
    if not s:
        return None
    return sum((x - m) ** 3 for x in xs) / (n * s ** 3)


def skew_adjusted_t(vals: list) -> dict:
    """skewness-adjusted t(四件套③稳健项;Hall 1992 / LBT 1999):
       t_sa = √n·(S + γ̂S²/3 + γ̂²S³/27 + γ̂/(6n)),S = x̄/s。
    对原始 BHAR 截面(非标准化)——BHAR 右偏(有限强平下限×无界上尾)使普通 t 偏定,此为文献修正。
    None 项不入截面;n<3/s=0 → t_sa None。附普通 t(=√n·S)对照。"""
    xs = [x for x in vals if x is not None]
    n = len(xs)
    if n < 3:
        return {"n": n, "s_stat": None, "skew": None, "t_plain": None, "t_sa": None}
    m, s = _mean_sd(xs)
    if not s:
        return {"n": n, "s_stat": None, "skew": None, "t_plain": None, "t_sa": None}
    S = m / s
    g = skewness(xs)
    t_sa = math.sqrt(n) * (S + g * S ** 2 / 3.0 + g ** 2 * S ** 3 / 27.0 + g / (6.0 * n))
    return {"n": n, "s_stat": S, "skew": g, "t_plain": math.sqrt(n) * S, "t_sa": t_sa}


if __name__ == "__main__":
    from taosha.compute.abnormal_tests import kp2010_factor

    # ── sbhar:手算 0.05/(0.02·√25)=0.5;缺项/σ0/H0 → None ─────────────────────
    assert abs(sbhar(0.05, 0.02, 25) - 0.5) < 1e-15
    assert sbhar(None, 0.02, 5) is None and sbhar(0.05, 0.0, 5) is None
    assert sbhar(0.05, None, 5) is None and sbhar(0.05, 0.02, 0) is None

    # ── cross_test:sbhars=[1,2,3] → mean2 sd1 z=2√3;ρ̄=0 → kp=1、adj=z ─────────
    ct = cross_test([1.0, 2.0, 3.0, None], 0.0, kp2010_factor)
    assert ct["n"] == 3 and abs(ct["z"] - 2 * math.sqrt(3)) < 1e-12
    assert abs(ct["kp_factor"] - 1.0) < 1e-12 and abs(ct["adj_z"] - ct["z"]) < 1e-12
    # ρ̄=0.5,n=3:factor=√[(1−.5)/(1+2·.5)]=√.25=.5 → adj=z/2(手算)
    ct2 = cross_test([1.0, 2.0, 3.0], 0.5, kp2010_factor)
    assert abs(ct2["kp_factor"] - 0.5) < 1e-12 and abs(ct2["adj_z"] - ct2["z"] * 0.5) < 1e-12
    # n<2 → None(不出统计量)
    assert cross_test([1.0], 0.0, kp2010_factor)["z"] is None

    # ── skewness:对称样本 γ̂=0;右偏样本 γ̂>0(手算 [0,0,3]:m=1,s=√3,γ̂=(−1−1+8)/(3·3√3))──
    assert abs(skewness([-1.0, 0.0, 1.0])) < 1e-15
    g = skewness([0.0, 0.0, 3.0])
    assert abs(g - 6.0 / (3 * 3 * math.sqrt(3))) < 1e-12 and g > 0

    # ── skew_adjusted_t:γ̂=0(对称)→ t_sa==t_plain;右偏且 S>0 → t_sa>t_plain(Hall 方向)──
    st = skew_adjusted_t([-1.0, 0.0, 1.0])
    assert abs(st["t_sa"] - st["t_plain"]) < 1e-12  # γ̂=0 → 修正项全零
    st2 = skew_adjusted_t([0.0, 0.1, 0.1, 0.2, 1.6])   # 右偏、均值>0
    assert st2["skew"] > 0 and st2["t_sa"] > st2["t_plain"]
    # 手算一例:xs=[0,0,3] → m=1,s=√3,S=1/√3,γ̂=6/(3·3√3)=2/(3√3);t_sa=√3(S+γS²/3+γ²S³/27+γ/(6·3))
    xs = [0.0, 0.0, 3.0]
    S = (1.0) / math.sqrt(3.0)
    gg = 2.0 / (3.0 * math.sqrt(3.0))
    exp_tsa = math.sqrt(3) * (S + gg * S ** 2 / 3 + gg ** 2 * S ** 3 / 27 + gg / 18.0)
    st3 = skew_adjusted_t(xs)
    assert abs(st3["t_sa"] - exp_tsa) < 1e-12, (st3, exp_tsa)
    # n<3 → None
    assert skew_adjusted_t([1.0, 2.0])["t_sa"] is None

    print("bhar_tests.py 自检 OK:sbhar手算/截面z=2√3+KP(ρ̄=.5,n3→.5)/γ̂手算/"
          "Hall t_sa(γ̂=0→=t_plain,右偏→>t_plain,手算例一致)")
