"""exp16 yearend_strength冻结规则攻击fixture（纯函数、零DB）。"""
from __future__ import annotations

import datetime as dt
import sys
from collections import namedtuple
from decimal import Decimal

from taosha.compute.yearend_strength_rules import (
    build_windows, select_yearend_events,
)


FAIL = 0
N = 0
Row = namedtuple("Row", "ts_code trade_date close")
BASE = dt.date(2010, 12, 17)
DAYS = tuple(BASE + dt.timedelta(days=index) for index in range(11))
EVENT = dt.date(2011, 1, 4)
WINDOWS = {2011: {"base_date": DAYS[0], "last10": DAYS[1:], "event_date": EVENT}}
MARKET = {day: Decimal(0) for day in DAYS[1:]}


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    FAIL += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


def fails(fn):
    try:
        fn()
        return ""
    except ValueError as exc:
        return str(exc)


def rows(code="000001.SZ", last=Decimal("105"), missing=()):
    closes = [Decimal("100")] * 10 + [last]
    return [Row(code, day, closes[index]) for index, day in enumerate(DAYS)
            if index not in set(missing)]


# F1 恰5%闭区间收录；10收益必须使用前置base形成11-bar。
s = select_yearend_events(rows(), MARKET, WINDOWS)
check("F1 恰5%收录", (s["counters"]["final_events"], s["events"][0]["event_date"]),
      (1, "2011-01-04"))
check("F1 11-bar完整面板", (s["counters"]["panel_any"],
                            s["counters"]["panel_full_11"]), (1, 1))

# F2 略低5%拒绝。
s = select_yearend_events(rows(last=Decimal("104.999")), MARKET, WINDOWS)
check("F2 略低阈值拒绝", s["counters"]["final_events"], 0)

# F3 缺base或任一窗内bar均整组拒绝。
s = select_yearend_events(rows(missing=(0,)), MARKET, WINDOWS)
check("F3 缺base拒绝", (s["counters"]["panel_partial_rejected"],
                         s["counters"]["base_missing"]), (1, 1))
s = select_yearend_events(rows(missing=(5,)), MARKET, WINDOWS)
check("F3 缺窗内bar拒绝", (s["counters"]["panel_partial_rejected"],
                           s["counters"]["window_bar_missing"]), (1, 1))

# F4 其他日期bar不得按个股自身行序补足缺口。
extra = rows(missing=(5,)) + [Row("000001.SZ", DAYS[-1] + dt.timedelta(days=1), Decimal("105"))]
extra.sort(key=lambda row: (row.ts_code, row.trade_date))
s = select_yearend_events(extra, MARKET, WINDOWS)
check("F4 禁个股行序补足", s["counters"]["final_events"], 0)

# F5 市场收益任一日缺失即全局fail-closed。
bad_market = dict(MARKET); bad_market.pop(DAYS[3])
check("F5 市场收益缺失拒绝", "市场收益缺失" in fails(
    lambda: select_yearend_events(rows(), bad_market, WINDOWS)), True)

# F6 非正close视为异常整组拒绝。
bad = rows(); bad[4] = Row(bad[4].ts_code, bad[4].trade_date, Decimal(0))
s = select_yearend_events(bad, MARKET, WINDOWS)
check("F6 非正close拒绝", s["counters"]["nonpositive_close_rejected"], 1)

# F7 同票同日重复bar拒绝，不择一。
duplicate = rows() + [rows()[3]]
duplicate.sort(key=lambda row: (row.ts_code, row.trade_date))
check("F7 重复raw bar拒绝", "重复bar" in fails(
    lambda: select_yearend_events(duplicate, MARKET, WINDOWS)), True)

# F8 两个规则窗映射同一事件键时涉事行全剔，不择一保留。
dup_windows = {2011: WINDOWS[2011], 2012: dict(WINDOWS[2011])}
s = select_yearend_events(rows(), MARKET, dup_windows)
check("F8 重复事件键全剔", (s["counters"]["final_events"],
                            s["counters"]["event_key_duplicate_groups"],
                            s["counters"]["event_key_duplicate_rows_dropped"]), (0, 1, 2))

# F8b 同票日期顺序必须严格递增，不能依赖字典静默重排。
unordered = rows()
unordered[3], unordered[4] = unordered[4], unordered[3]
check("F8b 票内日期乱序拒绝", "日期非严格递增" in fails(
    lambda: select_yearend_events(unordered, MARKET, WINDOWS)), True)

# F9 selection SHA双跑确定。
s1 = select_yearend_events(rows(), MARKET, WINDOWS)
s2 = select_yearend_events(rows(), MARKET, WINDOWS)
check("F9 双跑确定性", (s1["events"], s1["selection_sha256"]),
      (s2["events"], s2["selection_sha256"]))

# F10 日历构造明确取次年1月首开市日与12月窗前一开市日。
calendar = []
day = dt.date(2009, 12, 1)
while day < dt.date(2024, 2, 1):
    if day.weekday() < 5:
        calendar.append(day)
    day += dt.timedelta(days=1)
w = build_windows(calendar)
check("F10 14个年度窗", len(w), 14)
check("F10 事件锚与基期", (w[2011]["event_date"], w[2011]["base_date"]
                           < w[2011]["last10"][0]), (dt.date(2011, 1, 3), True))

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
