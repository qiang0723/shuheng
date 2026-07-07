"""淘沙 · compute · SIM 单指数市场模型 + 异常收益(切片2 item 2/3,口径②)。

口径②=SIM(单指数市场模型),estimation_method=OLS;regressor 按冻结基准取
(frozen_config.regressor_benchmark:池内=雷达股池等权/全市场=全市场等权)。

逐点对齐 estudy2 0.10.0 `R/apply_market_model.R` 的 `returns(market_model="sim")`:
  1. 按日对齐 security 收益 r 与 regressor 收益 rm(merge all=TRUE)。
  2. 估计样本 = 估计窗 [−250,−91] 内 **complete.cases**(r 与 rm 皆非 NA)(returns.zoo:594-597)。
  3. OLS:lm(y ~ x) → α=截距, β=斜率(returns.zoo:608, 628-631)。
  4. 预测覆盖全期:AR_t = r_t − (α + β·rm_t)(returns.zoo:620-621)。
  5. delta = 估计样本长度(returns.zoo:598);**即覆盖计数**,喂 frozen_config.coverage_ok。

红线:纯函数;禁零填充(NA 一律 None);不发明参数。α/β/AR/残差方差供下游 BMP/ADJ-BMP。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence

Num = Optional[float]


@dataclass(frozen=True)
class SimFit:
    """SIM-OLS 估计结果(对齐 estudy2 returns 对象的相关字段)。"""
    alpha: float                  # 截距
    beta: float                   # 斜率
    delta: int                    # 估计样本数(complete.cases 于估计窗);= 覆盖计数(=estudy2 estimation_length)
    est_ar_sd: float              # sd(估计窗 AR),ddof=1 → 逐点对齐 estudy2 BMP 的 sd(company_estimation_abnormal)
    x_bar: float                  # 估计窗 regressor 均值(BMP 预测误差修正用,=mean_market_estimation)
    sxx: float                    # Σ(x−x̄)^2 于估计窗(BMP 预测误差修正分母)
    abnormal: list[Num]           # 全期异常收益 AR_t(与输入等长,缺项 None)


def _ols(ys: Sequence[float], xs: Sequence[float]) -> tuple[float, float]:
    """普通最小二乘 lm(y~x):返回 (alpha, beta)。等价 estudy2 的 stats::lm。"""
    n = len(ys)
    xbar = sum(xs) / n
    ybar = sum(ys) / n
    sxx = sum((x - xbar) ** 2 for x in xs)
    sxy = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys))
    beta = sxy / sxx
    alpha = ybar - beta * xbar
    return alpha, beta


def sim_fit(security: Sequence[Num], market: Sequence[Num],
            est_mask: Sequence[bool]) -> SimFit:
    """拟合 SIM 并计算全期 AR。

    security/market: 等长按日对齐的收益序列(None=NA)。
    est_mask: 等长布尔,True=该日属估计窗 [−250,−91](事件窗/其余为 False)。
    """
    if not (len(security) == len(market) == len(est_mask)):
        raise ValueError("security/market/est_mask 必须等长(按日对齐)")

    # 估计样本 = 估计窗内 complete.cases(returns.zoo:594-597)
    ys, xs = [], []
    for r, rm, in_est in zip(security, market, est_mask):
        if in_est and r is not None and rm is not None:
            ys.append(r)
            xs.append(rm)
    delta = len(ys)
    if delta < 2:
        raise ValueError(f"估计样本 delta={delta} < 2,OLS 无法估计(覆盖门槛应先剔)")

    alpha, beta = _ols(ys, xs)

    # 估计窗 AR = OLS 残差;其 sd(ddof=1)即 estudy2 BMP 的标准化尺度
    # sd(company_estimation_abnormal)(parametric_tests.R:905)。OLS 含截距 → 残差均值恒 0。
    resid = [y - (alpha + beta * x) for y, x in zip(ys, xs)]
    ar_bar = sum(resid) / delta
    est_ar_sd = math.sqrt(sum((e - ar_bar) ** 2 for e in resid) / (delta - 1))
    xbar = sum(xs) / delta
    sxx = sum((x - xbar) ** 2 for x in xs)

    # 全期 AR:r 或 rm 缺项则 None(禁零填充)
    abnormal: list[Num] = []
    for r, rm in zip(security, market):
        if r is None or rm is None:
            abnormal.append(None)
        else:
            abnormal.append(r - (alpha + beta * rm))

    return SimFit(alpha=alpha, beta=beta, delta=delta, est_ar_sd=est_ar_sd,
                  x_bar=xbar, sxx=sxx, abnormal=abnormal)


if __name__ == "__main__":
    # 自检1:无噪声线性 r = 0.001 + 1.5·rm → 应精确回收 α=0.001,β=1.5,残差≈0。
    rm = [0.01, -0.02, 0.005, 0.03, -0.01, 0.02, 0.0, -0.015, 0.008, 0.012]
    sec = [0.001 + 1.5 * m for m in rm]
    est = [True] * 8 + [False] * 2          # 前8日估计窗,后2日事件窗
    fit = sim_fit(sec, rm, est)
    assert abs(fit.alpha - 0.001) < 1e-12, fit.alpha
    assert abs(fit.beta - 1.5) < 1e-12, fit.beta
    assert fit.delta == 8, fit.delta
    assert fit.est_ar_sd < 1e-12, fit.est_ar_sd
    # 事件窗 AR 也应≈0(线性无噪声)
    assert all(abs(a) < 1e-12 for a in fit.abnormal[8:]), fit.abnormal[8:]
    # 自检2:估计窗内缺项(complete.cases)不入回归,delta 相应减少
    sec2 = list(sec); sec2[3] = None       # 估计窗第4日 security 缺
    fit2 = sim_fit(sec2, rm, est)
    assert fit2.delta == 7, fit2.delta
    # 自检3:禁零填充——AR 在缺项处为 None,不是 0
    assert fit2.abnormal[3] is None, fit2.abnormal[3]
    print("market_model.py 自检 OK:SIM-OLS 精确回收 α/β / complete.cases 覆盖计数 / 禁零填充")
