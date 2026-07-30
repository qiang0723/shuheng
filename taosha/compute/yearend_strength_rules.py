"""exp16 年末相对强势事件识别（纯函数，零 I/O）。

冻结 PAP：yearend-strength-pap-final-2026-07-30.json
digest=3493944439315ed2e044aed4751a1201fdb584ca6349826ad9c3449474d1d345。
本模块只实现事件几何；不读事件后收益、不作统计判决、不写台账。
"""
from __future__ import annotations

import datetime as dt
import hashlib
import itertools
from collections import Counter
from decimal import Decimal, localcontext


EVENT_YEARS = tuple(range(2011, 2025))
HOLDOUT = dt.date(2024, 7, 1)
RELATIVE_WEALTH_THRESHOLD = Decimal("0.05")
COUNTER_KEYS = (
    "input_rows", "panel_any", "panel_full_11", "panel_partial_rejected",
    "base_missing", "window_bar_missing", "nonpositive_close_rejected",
    "exact_threshold_hits", "event_key_duplicate_groups",
    "event_key_duplicate_rows_dropped", "final_events", "final_securities",
    "event_dates",
)


def _dec(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def build_windows(calendar: list[dt.date]) -> dict[int, dict]:
    """SSE日历 → 14个年度严格11-bar选择窗与次年事件锚。"""
    ordered = sorted(calendar)
    if len(ordered) != len(set(ordered)):
        raise ValueError("SSE日历含重复日期——fail-closed")
    windows = {}
    for event_year in EVENT_YEARS:
        december = [day for day in ordered if day.year == event_year - 1 and day.month == 12]
        january = [day for day in ordered if day.year == event_year and day.month == 1]
        if len(december) < 10 or not january:
            raise ValueError(f"event_year={event_year} 日历覆盖不足——fail-closed")
        last10 = tuple(december[-10:])
        prior = [day for day in ordered if day < last10[0]]
        if not prior:
            raise ValueError(f"event_year={event_year} 缺选择窗基期——fail-closed")
        event_date = january[0]
        if not last10[-1] < event_date < HOLDOUT:
            raise ValueError(f"event_year={event_year} 事件锚越界——fail-closed")
        windows[event_year] = {
            "base_date": prior[-1], "last10": last10, "event_date": event_date,
        }
    return windows


def selection_sha(events: list[dict]) -> str:
    """事件键排序后确定性SHA，与冻结前对账脚本同式。"""
    body = "".join(
        f"{event['ts_code']}|{event['event_date']}\n"
        for event in sorted(events, key=lambda item: (item["ts_code"], item["event_date"]))
    )
    return hashlib.sha256(body.encode()).hexdigest()


def _evaluate_security(ts_code: str, rows: dict, windows: dict,
                       market_returns: dict, counters: Counter) -> list[dict]:
    events = []
    for event_year, window in windows.items():
        dates = (window["base_date"], *window["last10"])
        present = [day for day in dates if day in rows and rows[day] is not None]
        if not present:
            continue
        counters["panel_any"] += 1
        if len(present) != 11:
            counters["panel_partial_rejected"] += 1
            counters["base_missing"] += int(window["base_date"] not in present)
            counters["window_bar_missing"] += int(any(day not in present for day in window["last10"]))
            continue
        closes = [_dec(rows[day]) for day in dates]
        if any(value <= 0 for value in closes):
            counters["nonpositive_close_rejected"] += 1
            continue
        counters["panel_full_11"] += 1
        with localcontext() as context:
            context.prec = 34
            market_log = sum(
                (_dec(market_returns[day]) for day in window["last10"]), Decimal(0))
            stock_log = (closes[-1] / closes[0]).ln()
            relative_wealth = (stock_log - market_log).exp() - Decimal(1)
        counters["exact_threshold_hits"] += int(relative_wealth == RELATIVE_WEALTH_THRESHOLD)
        if relative_wealth < RELATIVE_WEALTH_THRESHOLD:
            continue
        events.append({
            "ts_code": ts_code,
            "event_date": window["event_date"].isoformat(),
            "selection_year": event_year - 1,
            "relative_wealth": str(relative_wealth),
        })
    return events


def select_yearend_events(price_rows, market_returns: dict,
                          windows: dict[int, dict]) -> dict:
    """钉批选择日价格流 → 冻结事件集；price_rows须按票、日期升序。"""
    required_market = {day for window in windows.values() for day in window["last10"]}
    missing_market = sorted(day for day in required_market if market_returns.get(day) is None)
    if missing_market:
        raise ValueError(f"市场收益缺失={missing_market[:5]}——fail-closed")

    counters = Counter()
    events = []
    last_code = None
    for ts_code, group in itertools.groupby(price_rows, key=lambda row: row.ts_code):
        if last_code is not None and ts_code <= last_code:
            raise ValueError("price_rows票序非严格递增——fail-closed")
        last_code = ts_code
        rows = {}
        last_date = None
        for row in group:
            counters["input_rows"] += 1
            if row.trade_date in rows:
                raise ValueError(f"{ts_code}@{row.trade_date}重复bar——fail-closed")
            if last_date is not None and row.trade_date <= last_date:
                raise ValueError(f"{ts_code}票内日期非严格递增——fail-closed")
            rows[row.trade_date] = row.close
            last_date = row.trade_date
        events.extend(_evaluate_security(ts_code, rows, windows, market_returns, counters))

    by_key = Counter((event["ts_code"], event["event_date"]) for event in events)
    duplicate_keys = {key for key, count in by_key.items() if count > 1}
    final = [event for event in events
             if (event["ts_code"], event["event_date"]) not in duplicate_keys]
    yearly = Counter(event["event_date"][:4] for event in final)
    counters["event_key_duplicate_groups"] = len(duplicate_keys)
    counters["event_key_duplicate_rows_dropped"] = len(events) - len(final)
    counters["final_events"] = len(final)
    counters["final_securities"] = len({event["ts_code"] for event in final})
    counters["event_dates"] = len({event["event_date"] for event in final})
    for key in COUNTER_KEYS:
        counters.setdefault(key, 0)
    return {
        "events": final,
        "counters": dict(counters),
        "events_yearly": dict(sorted(yearly.items())),
        "selection_sha256": selection_sha(final),
    }
