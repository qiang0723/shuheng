"""淘沙 · engine · 市场基准收益(口径②,切片2)。

口径②=SIM;regressor 按冻结基准(frozen_config.regressor_benchmark):
  池内假设=雷达股池等权 / 全市场假设=全市场等权(否决"等权 market-adjusted")。
本模块从 reader 全宇宙价格算**等权对数收益基准**,作 SIM 的 regressor(rm)。

红线:禁零填充(某日无有效证券收益→该日基准 None);等权=当日有效证券收益的算术均值。
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

from taosha.compute.returns import log_rates_from_prices
from taosha.reader.contract import PriceRow

Num = Optional[float]


def returns_by_date(rows: list[PriceRow], dates: list[dt.date]) -> list[Num]:
    """把一只证券的价格行对齐到统一 date 轴,算跨缺口对数收益,返回按 date 对齐的收益。

    ret[j] = 从 date[j-1] 到 date[j] 的对数收益(returns.py 跨缺口:恢复日收益落恢复日);
    ret[0]=None(无前值)。停牌 close=None → 该处收益按 returns.py 规则 None(禁零填充)。
    """
    close_by_date = {r.trade_date: r.close for r in rows}
    close_series = [close_by_date.get(d) for d in dates]     # None=停牌/无该证券当日行
    rates = log_rates_from_prices(close_series, quote="Close", multi_day=True)  # 长度 n-1
    return [None] + rates                                     # 对齐 date 轴,ret[j]↔date[j]


def equal_weight_market(sec_returns: dict[str, list[Num]], n_dates: int) -> list[Num]:
    """全市场等权对数收益(口径②"全市场假设=全市场等权")。

    每日 = 当日有效(非 None)证券收益的算术均值;当日无有效证券 → None(禁零填充)。
    """
    mkt: list[Num] = []
    for j in range(n_dates):
        vals = [r[j] for r in sec_returns.values() if r[j] is not None]
        mkt.append(sum(vals) / len(vals) if vals else None)
    return mkt


def pool_equal_weight_market(sec_returns: dict[str, list[Num]], pool: set,
                             n_dates: int) -> list[Num]:
    """池内等权对数收益(口径②"池内假设=雷达股池等权"):仅 pool 内证券参与等权。"""
    return equal_weight_market({k: v for k, v in sec_returns.items() if k in pool}, n_dates)
