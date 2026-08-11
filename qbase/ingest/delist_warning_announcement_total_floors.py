#!/usr/bin/env python3
"""exp22 已保全官方响应的单日公告数下界；只收紧新读取。"""
from __future__ import annotations

import datetime as dt
from collections import Counter


DAY_TOTAL_FLOORS = {
    # v6/v7 保留的官方响应多次观测到 35；新遍不得把稳定的 32 误收为全集。
    ("000607", "2021-04-30"): 35,
}


def assert_historical_day_total_floors(code: str, rows: list[dict],
                                       start: dt.date, end: dt.date) -> dict:
    counts = Counter(row["announcement_date_cn"] for row in rows)
    audit = {}
    for (floor_code, day_text), minimum in DAY_TOTAL_FLOORS.items():
        day = dt.date.fromisoformat(day_text)
        if floor_code != code or not start <= day <= end:
            continue
        actual = counts[day_text]
        if actual < minimum:
            raise RuntimeError(
                f"{code}/{day_text} 公告数{actual}低于历史官方观测下界{minimum}")
        audit[day_text] = {"minimum": minimum, "actual": actual}
    return audit
