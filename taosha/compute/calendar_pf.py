"""淘沙 · compute · 日历时间组合法(切片2 稳健性二,spec §6;S2-Q 裁决补建)。

事件聚集时,截面法(BMP)的独立性假设被破坏 → 假阳性。日历时间组合法把事件从
"事件时"搬到"日历时":每个日历交易日构造一个当日处于事件窗内证券的等权组合,
对组合日收益(异常)做时序 t 检验。同一日历日的聚集事件被并成**一个**组合观测,
截面相关不再重复计入(Jaffe-Mandelker / Loughran-Ritter 思想)。

方法:
  1. 每日历交易日 d:成员 = 事件窗(τ=0..W)覆盖 d 的证券;组合 AR_d = 等权均值(禁零填充,
     缺项不入)。
  2. 时序:series = {AR_d : d 有 ≥1 成员};t_cal = mean(series) / (sd(series)/√K),K=有成员日数。
  3. 方向 = sign(mean(series))。

spec §6 裁决关联:日历时间法与截面法方向相反 → 查事件密集期、补事件加权(verdict 层处理)。
红线:纯函数;禁零填充;无 estudy2 对台,自检以构造验证。
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Optional, Sequence

Num = Optional[float]


@dataclass
class CalEvent:
    """单事件日历输入。dates[τ]=事件窗第 τ 日的日历交易日;ar[τ]=对应 AR(None=缺)。"""
    dates: Sequence[dt.date]
    ar: Sequence[Num]


def _tstat(series: list[float]) -> Optional[float]:
    k = len(series)
    if k < 2:
        return None
    m = sum(series) / k
    sd = (sum((x - m) ** 2 for x in series) / (k - 1)) ** 0.5
    return (m / (sd / k ** 0.5)) if sd > 0 else None


def calendar_time(events: Sequence[CalEvent], main_len: int, robust_len: int) -> dict:
    """日历时间组合法。对主/稳健窗各建组合、时序 t 检验。返回 t_cal + 方向 + 日历日数。"""
    def _window(win_len: int) -> dict:
        by_date: dict[dt.date, list[float]] = {}
        for ev in events:
            for tau in range(min(win_len, len(ev.ar))):
                a = ev.ar[tau]
                d = ev.dates[tau]
                if a is not None and d is not None:
                    by_date.setdefault(d, []).append(a)
        series = [sum(v) / len(v) for _, v in sorted(by_date.items())]  # 按日历日排序的组合 AR
        t = _tstat(series)
        m = (sum(series) / len(series)) if series else None
        return {"t_cal": t, "direction": _sign(m), "n_cal_days": len(series),
                "port_mean": m}
    return {"main": _window(main_len), "robust": _window(robust_len)}


def _sign(x):
    if x is None:
        return 0
    return 1 if x > 0 else (-1 if x < 0 else 0)


if __name__ == "__main__":
    import random
    rng = random.Random(11)
    base = dt.date(2021, 3, 1)
    days = [base + dt.timedelta(days=k) for k in range(12)]
    # 自检1:20 事件全共享同一事件日历(聚集),τ=0 正 AR → 组合 τ=0 日均值正、方向 +1。
    evs = []
    for _ in range(20):
        d = [days[t] for t in range(6)]
        a = [0.03 + rng.gauss(0, 0.005)] + [rng.gauss(0, 0.005) for _ in range(5)]
        evs.append(CalEvent(d, a))
    r = calendar_time(evs, main_len=3, robust_len=6)
    assert r["main"]["direction"] == 1, r["main"]
    assert r["main"]["n_cal_days"] == 3, r["main"]     # 聚集:主窗仅 3 个日历日
    assert r["robust"]["n_cal_days"] == 6, r["robust"]
    # 自检2:组合把同日聚集并成一个观测(20 证券同日 → 1 个组合 AR,非 20)
    #        故主窗日历日数=3(不因证券多而变),验证截面相关不重复计入。
    #        port_mean = 3 个日历日均值(τ=0≈0.03,τ=1/2≈0)≈ 0.01。
    assert 0.008 < r["main"]["port_mean"] < 0.015, r["main"]
    # 自检3:禁零填充——缺项不入组合;全缺日不产生观测
    ev_gap = [CalEvent([days[0], None, days[2]], [0.01, None, 0.02])]
    r3 = calendar_time(ev_gap, 3, 3)
    assert r3["main"]["n_cal_days"] == 2, r3["main"]   # 只有 2 个有效日历日
    print("calendar_pf.py 自检 OK:聚集并单观测(日历日=3)/ 方向 / 禁零填充(缺项不入)")
