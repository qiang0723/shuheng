"""淘沙 · compute · 精确 DSR(Deflated Sharpe Ratio)常设报告项(#2b 步③,exp_id 3)。

Bailey & López de Prado(2014)精确公式,策略版**常设报告项**(纯函数 + 单测,**报告项不进 verdict**,
铁律⑤:陈述统计事实,不下"有 alpha/建议买入"判断)。两块:
  · PSR(Probabilistic Sharpe Ratio)= 含偏度 γ3/峰度 γ4 修正的 Sharpe 显著性:
        PSR(SR_b) = Φ[ (SR_hat − SR_b)·√(n−1) / √(1 − γ3·SR_hat + (γ4−1)/4·SR_hat²) ]
  · DSR = PSR(SR*),SR* = 期望最大 Sharpe 缩水项(N 次独立试验的多重检验惩罚):
        SR* = √V · [ (1−γ_e)·Φ⁻¹(1−1/N) + γ_e·Φ⁻¹(1−1/(N·e)) ]   (γ_e = Euler–Mascheroni)
  独立试验数 **N = 族内 trial 计数**;#2b 取 **N=2**(事件版 + 策略版同族两次)。

⚠**统计口径待拍(红线①:不自定统计口径,实现到该分支上报人拍)**:SR* 需"试验间 SR 方差 V"。
  N=2 且**无可排序 trial-SR 集合**时 V 无数据可估。本件把 V 口径**参数化**(`v_mode`),默认取
  BLdP 退化路径的单 SR 抽样方差代理(mlfinlab 同做法),但**此默认是待人拍的建议、非既定口径**:
    · v_mode='proxy'(默认·待拍建议):V = Var[SR_hat] = (1 − γ3·SR_hat + (γ4−1)/4·SR_hat²)/(n−1);
    · v_mode='trial_var':V = N 次已实现 trial-SR 的总体方差(须传 trial_srs,即事件版/策略版两 SR);
    · v_mode='given':V = 调用方显式给定(留终裁口径落地位)。
  报告须登记所选口径 + PBO 不适用之结构理由(单条冻结规则无试验集合可排序);人裁前不锁默认为口径。

红线:纯 stdlib(math),无 scipy(与本层 returns/abnormal_tests 同);PSR/DSR 为报告项、不改 verdict。
"""
from __future__ import annotations

import math
from typing import Optional

EULER_MASCHERONI = 0.5772156649015329


# ── 正态分布辅助(纯 stdlib;本层无现成 Φ/Φ⁻¹,自带单一来源)──────────────────────
def norm_cdf(z: float) -> float:
    """标准正态 CDF Φ(z) = ½·erfc(−z/√2)(机器精度)。"""
    return 0.5 * math.erfc(-z / math.sqrt(2.0))


# Acklam 有理逼近系数(标准正态分位数 Φ⁻¹,相对误差 ~1e-9,再加一步 Halley 精化至机器精度)
_A = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
      1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
_B = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
      6.680131188771972e+01, -1.328068155288572e+01)
_C = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
      -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
_D = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
      3.754408661907416e+00)


def norm_ppf(p: float) -> float:
    """标准正态分位数 Φ⁻¹(p),p∈(0,1)。Acklam 逼近 + 一步 Halley 精化(≈机器精度)。"""
    if not (0.0 < p < 1.0):
        raise ValueError(f"norm_ppf 定义域 (0,1),得 {p}")
    plow, phigh = 0.02425, 1.0 - 0.02425
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        x = (((((_C[0]*q+_C[1])*q+_C[2])*q+_C[3])*q+_C[4])*q+_C[5]) / \
            ((((_D[0]*q+_D[1])*q+_D[2])*q+_D[3])*q+1.0)
    elif p <= phigh:
        q = p - 0.5
        r = q*q
        x = (((((_A[0]*r+_A[1])*r+_A[2])*r+_A[3])*r+_A[4])*r+_A[5])*q / \
            (((((_B[0]*r+_B[1])*r+_B[2])*r+_B[3])*r+_B[4])*r+1.0)
    else:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        x = -(((((_C[0]*q+_C[1])*q+_C[2])*q+_C[3])*q+_C[4])*q+_C[5]) / \
            ((((_D[0]*q+_D[1])*q+_D[2])*q+_D[3])*q+1.0)
    # Halley 精化一步(用 erf 的精确 CDF)
    e = norm_cdf(x) - p
    u = e * math.sqrt(2.0 * math.pi) * math.exp(x * x / 2.0)
    x = x - u / (1.0 + x * u / 2.0)
    return x


# ── Sharpe 与高阶矩(BLdP/mlfinlab 口径:SR 用 ddof=1,偏度/峰度用总体矩 n)──────────
def sharpe_ratio(returns: list) -> Optional[float]:
    """逐期(非年化)Sharpe = 均值 / 样本标准差(ddof=1)。n<2 或 std=0 → None。"""
    xs = [x for x in returns if x is not None]
    n = len(xs)
    if n < 2:
        return None
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1)
    if var <= 0.0:
        return None
    return mean / math.sqrt(var)


def skew_kurtosis(returns: list) -> Optional[tuple]:
    """总体标准化偏度 γ3 与峰度 γ4(非超额,正态 γ4=3;BLdP/mlfinlab 口径,分母用 n)。n<3 或 m2=0 → None。"""
    xs = [x for x in returns if x is not None]
    n = len(xs)
    if n < 3:
        return None
    mean = sum(xs) / n
    m2 = sum((x - mean) ** 2 for x in xs) / n
    if m2 <= 0.0:
        return None
    m3 = sum((x - mean) ** 3 for x in xs) / n
    m4 = sum((x - mean) ** 4 for x in xs) / n
    return m3 / m2 ** 1.5, m4 / m2 ** 2.0


# ── PSR / SR* / DSR ─────────────────────────────────────────────────────────────
def psr(sr_hat: float, skew: float, kurt: float, n: int, sr_benchmark: float = 0.0) -> Optional[float]:
    """PSR(SR_b):真实 Sharpe 超过基准 SR_b 的概率(含 γ3/γ4 修正)。n<2 或方差项≤0 → None。"""
    if n < 2:
        return None
    var_term = 1.0 - skew * sr_hat + (kurt - 1.0) / 4.0 * sr_hat * sr_hat
    if var_term <= 0.0:
        return None
    z = (sr_hat - sr_benchmark) * math.sqrt(n - 1) / math.sqrt(var_term)
    return norm_cdf(z)


def var_sr_proxy(sr_hat: float, skew: float, kurt: float, n: int) -> Optional[float]:
    """BLdP 退化路径:单 SR 抽样方差 Var[SR_hat] 作试验间方差 V 的代理(v_mode='proxy';待拍建议)。"""
    if n < 2:
        return None
    return (1.0 - skew * sr_hat + (kurt - 1.0) / 4.0 * sr_hat * sr_hat) / (n - 1)


def expected_max_sr(v: float, N: int) -> float:
    """SR* = 期望最大 Sharpe 缩水项(N 次独立试验)。N<2 → 0(无缩水);V≤0 → 0。"""
    if N < 2 or v <= 0.0:
        return 0.0
    return math.sqrt(v) * ((1.0 - EULER_MASCHERONI) * norm_ppf(1.0 - 1.0 / N)
                           + EULER_MASCHERONI * norm_ppf(1.0 - 1.0 / (N * math.e)))


def deflated_sharpe(returns: list, N: int, v_mode: str = "proxy",
                    trial_srs: Optional[list] = None, v: Optional[float] = None) -> dict:
    """精确 DSR 常设报告项(不进 verdict)。返回全中间量供报告登记 + 复核。

    N = 族内 trial 计数(#2b=2)。v_mode 选试验间方差 V 口径(见模块 docstring;默认 'proxy' 待拍)。
    n<2 或矩不可估 → dsr/psr_vs_zero=None,其余量尽力给。
    """
    xs = [x for x in returns if x is not None]
    n = len(xs)
    sr = sharpe_ratio(xs)
    sk = skew_kurtosis(xs)
    out = {"n": n, "N": N, "v_mode": v_mode, "sr_hat": sr,
           "skew": None, "kurtosis": None, "v": None, "sr_star": None,
           "psr_vs_zero": None, "dsr": None}
    if sr is None or sk is None:
        return out
    skew, kurt = sk
    out["skew"], out["kurtosis"] = skew, kurt

    # 试验间方差 V(待拍口径分支;人裁前默认 proxy,报告登记所选口径)
    if v_mode == "given":
        if v is None:
            raise ValueError("v_mode='given' 须显式传 v")
        v_use = v
    elif v_mode == "trial_var":
        if not trial_srs or len(trial_srs) < 2:
            raise ValueError("v_mode='trial_var' 须传 ≥2 个已实现 trial-SR")
        m = sum(trial_srs) / len(trial_srs)
        v_use = sum((s - m) ** 2 for s in trial_srs) / len(trial_srs)  # 总体方差
    elif v_mode == "proxy":
        v_use = var_sr_proxy(sr, skew, kurt, n)
    else:
        raise ValueError(f"未知 v_mode: {v_mode!r}")
    out["v"] = v_use

    sr_star = expected_max_sr(v_use, N) if v_use is not None else None
    out["sr_star"] = sr_star
    out["psr_vs_zero"] = psr(sr, skew, kurt, n, 0.0)
    if sr_star is not None:
        out["dsr"] = psr(sr, skew, kurt, n, sr_star)
    return out


if __name__ == "__main__":
    # ── 正态辅助:CDF/PPF 往返 + 已知值 ──────────────────────────────────────────
    assert abs(norm_cdf(0.0) - 0.5) < 1e-15
    assert abs(norm_cdf(1.959963984540054) - 0.975) < 1e-12, norm_cdf(1.959963984540054)
    assert abs(norm_ppf(0.975) - 1.959963984540054) < 1e-9, norm_ppf(0.975)
    assert abs(norm_ppf(0.95) - 1.6448536269514722) < 1e-9, norm_ppf(0.95)
    for z in (-2.5, -0.3, 0.0, 0.7, 2.1):
        assert abs(norm_ppf(norm_cdf(z)) - z) < 1e-9, z

    # ── Sharpe / 矩:对称正态样本 skew≈0 kurt≈3 ─────────────────────────────────
    import random
    rng = random.Random(12345)
    sym = [rng.gauss(0.001, 0.02) for _ in range(2000)]
    sk, ku = skew_kurtosis(sym)
    assert abs(sk) < 0.2 and abs(ku - 3.0) < 0.4, (sk, ku)
    sr = sharpe_ratio(sym)
    assert sr is not None and sr > 0  # 正均值

    # ── PSR:强正 SR → PSR(0) 高;基准抬高 → PSR 降 ───────────────────────────────
    p0 = psr(sr, sk, ku, len(sym), 0.0)
    assert p0 is not None and p0 > 0.9, p0
    p_hi = psr(sr, sk, ku, len(sym), sr * 2.0)
    assert p_hi < p0, (p_hi, p0)

    # ── SR* N=2 显式手算:ppf(1−1/2)=0 → SR*=√V·γ_e·ppf(1−1/(2e)) ────────────────
    v_demo = 0.01
    star2 = expected_max_sr(v_demo, 2)
    manual = math.sqrt(v_demo) * EULER_MASCHERONI * norm_ppf(1.0 - 1.0 / (2.0 * math.e))
    assert abs(star2 - manual) < 1e-12, (star2, manual)
    assert star2 > 0
    assert expected_max_sr(v_demo, 1) == 0.0  # N=1 无缩水
    # N 越大缩水越狠(SR* 单调增)
    assert expected_max_sr(v_demo, 10) > expected_max_sr(v_demo, 2)

    # ── DSR:N=2 缩水后 DSR < PSR(0);三 v_mode 均可跑;报告项不进 verdict ─────────
    d_proxy = deflated_sharpe(sym, N=2, v_mode="proxy")
    assert d_proxy["dsr"] is not None and d_proxy["sr_star"] > 0
    assert d_proxy["dsr"] < d_proxy["psr_vs_zero"], (d_proxy["dsr"], d_proxy["psr_vs_zero"])
    # trial_var 口径:两 trial-SR(事件版/策略版桩)
    d_tv = deflated_sharpe(sym, N=2, v_mode="trial_var", trial_srs=[sr, sr * 0.8])
    assert d_tv["dsr"] is not None and d_tv["v"] > 0
    # given 口径:显式 V
    d_gv = deflated_sharpe(sym, N=2, v_mode="given", v=v_demo)
    assert abs(d_gv["v"] - v_demo) < 1e-15 and d_gv["dsr"] is not None

    # ── 退化:n<2 → 各主量 None(合法,非报错) ───────────────────────────────────
    d_empty = deflated_sharpe([0.01], N=2)
    assert d_empty["sr_hat"] is None and d_empty["dsr"] is None

    print("dsr.py 自检 OK:Φ/Φ⁻¹往返机器精度 / SR·γ3·γ4 / PSR单调 / SR*(N=2手算·N单调·N=1无缩水) / "
          "DSR<PSR(0) / 三v_mode(proxy待拍·trial_var·given) / n<2退化None")
    print("EULER_MASCHERONI =", EULER_MASCHERONI, "| 待拍:V 口径默认 proxy(见 docstring,报告须登记)")
