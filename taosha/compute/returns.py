"""淘沙 · compute · 对数收益(切片2 item 3/5)。

口径①=continuous(对数收益,frozen_config.COMPOUNDING);item 3 要求我方收益与
estudy2 `multi_day=TRUE` **同构**(跨缺口收益),提供两侧同一样本的收益序列对照。

本模块**逐行忠实复刻** estudy2 0.10.0 的 Rcpp 收益核 `src/rates.cpp`:
  - getMultiDayRates(prices, continuous, Open)  ← 主用(multi_day=TRUE)
  - getSingleDayRates(prices, continuous)
复刻要点(rates.cpp 行号在案),二者语义须逐点等价,任何分歧逐笔归因(附录D):

  1. 输出长度 = n-1(每两行之间一个收益;rates.cpp:9)。
  2. 缺口(停牌 NA)处理——**这是"跨缺口对齐"的要害**:
     Close 口径(Open=FALSE)遇缺口时,跨缺口对数收益 log(P_k / P_i) 放在**恢复日前一行
     k-1**(rates.cpp:35),缺口起始行 i 置 **NA**(rates.cpp:34);Open 口径或无缺口(k==i+1)
     则放在行 i(rates.cpp:28-31)。
  3. **禁零填充**(item 5):任何缺失一律 NA(None),绝无以 0 填补收益缺口的路径
     (rates.cpp 全程 NA_REAL,本模块全程 None)。
  4. 尾部找不到有效价则该行 NA(rates.cpp:38-41)。

红线:纯函数,无判断;不 import 兄弟顶层目录。价格 None=缺失(NA),严禁在缺口处造数。
"""
from __future__ import annotations

import math
from typing import Optional, Sequence

from taosha.compute.frozen_config import COMPOUNDING

Price = Optional[float]      # None = NA(停牌/无交易)
Rate = Optional[float]


def _rate(p_to: float, p_from: float, continuous: bool) -> float:
    """单笔收益:continuous=对数收益 log(P1/P0);discrete=P1/P0-1(rates.cpp:30/69)。"""
    return math.log(p_to / p_from) if continuous else (p_to / p_from - 1.0)


def multi_day_rates(prices: Sequence[Price], *, continuous: bool = True,
                    open_quote: bool = False) -> list[Rate]:
    """复刻 getMultiDayRates(rates.cpp:6-91)。跨缺口收益按 Close/Open 口径就位。

    prices: 单只证券价格序列(None=NA)。continuous: 对数(True)/离散(False)。
    open_quote: 是否 Open 报价(get_rates_from_prices 中 open=quote=='Open';我方 Close→False)。
    返回长度 n-1 的收益序列(None=NA)。
    """
    n = len(prices)
    rates: list[Rate] = [None] * max(n - 1, 0)
    i = 0
    while i <= n - 2:
        if prices[i] is not None:
            k = i + 1
            # 跳过连续 NA 价(其收益行置 NA);仅在 k < n-1 时推进(rates.cpp:21-25)
            while k < n - 1 and prices[k] is None:
                rates[k] = None
                k += 1
            if k <= n - 1 and prices[k] is not None:
                if open_quote or k == i + 1:
                    rates[i] = _rate(prices[k], prices[i], continuous)   # 行 i(cpp:28-31)
                else:
                    rates[i] = None                                       # cpp:34
                    rates[k - 1] = _rate(prices[k], prices[i], continuous)  # 行 k-1(cpp:35)
            else:
                rates[i] = None                                           # 尾部无有效价(cpp:38-41)
            i = k          # C++: i=k-1 后 for 的 i++ ⇒ 下一轮 i=k
        else:
            rates[i] = None                                               # cpp:44-47
            i += 1
    return rates


def single_day_rates(prices: Sequence[Price], *, continuous: bool = True) -> list[Rate]:
    """复刻 getSingleDayRates(rates.cpp:94-133):相邻两日皆有效才算收益,否则 NA。"""
    n = len(prices)
    rates: list[Rate] = [None] * max(n - 1, 0)
    for i in range(n - 1):
        a, b = prices[i], prices[i + 1]
        rates[i] = _rate(b, a, continuous) if (a is not None and b is not None) else None
    return rates


def log_rates_from_prices(prices: Sequence[Price], *, quote: str = "Close",
                          multi_day: bool = True) -> list[Rate]:
    """对齐 get_rates_from_prices(get_rates_from_prices.R):open=quote=='Open',
    compounding 取冻结口径①(continuous)。台架主入口:multi_day=True + Close + continuous。"""
    continuous = COMPOUNDING == "continuous"
    open_quote = quote == "Open"
    if multi_day:
        return multi_day_rates(prices, continuous=continuous, open_quote=open_quote)
    return single_day_rates(prices, continuous=continuous)


def _approx(a: Rate, b: Rate, tol: float = 1e-12) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= tol


if __name__ == "__main__":
    # 自检:含停牌缺口的 Close 序列,跨缺口收益应落在恢复日前一行(k-1),缺口起始行 NA。
    p = [10.0, 11.0, None, None, 13.0, 14.0]     # 索引4=恢复日 → 跨缺口收益落索引3
    got = log_rates_from_prices(p, quote="Close", multi_day=True)
    exp = [math.log(11/10), None, None, math.log(13/11), math.log(14/13)]
    assert all(_approx(g, e) for g, e in zip(got, exp)), (got, exp)
    # Open 口径:跨缺口收益落在缺口起始行 i(索引1),不后移;索引2/3 为 NA
    got_o = multi_day_rates(p, continuous=True, open_quote=True)
    exp_o = [math.log(11/10), math.log(13/11), None, None, math.log(14/13)]
    assert all(_approx(g, e) for g, e in zip(got_o, exp_o)), (got_o, exp_o)
    # single_day:相邻两日任一 NA 即 NA,绝不零填充(缺口整段无收益)
    got_s = single_day_rates(p, continuous=True)
    exp_s = [math.log(11/10), None, None, None, math.log(14/13)]
    assert all(_approx(g, e) for g, e in zip(got_s, exp_s)), (got_s, exp_s)
    print("returns.py 自检 OK:跨缺口对齐(k-1 就位)/ 禁零填充(缺口=None)/ Close·Open·single 三路一致")
