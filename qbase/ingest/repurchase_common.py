"""exp23 repurchase 数据资产的字段、窗口与忠实解析。"""
from __future__ import annotations

import math
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

SOURCE = "tushare:repurchase"
HOLDOUT = date(2024, 7, 1)
DEFAULT_START = date(1990, 1, 1)
FIELDS = "ts_code,ann_date,end_date,proc,exp_date,vol,amount,high_limit,low_limit"
FIELD_NAMES = tuple(FIELDS.split(","))
DATE_FIELDS = {"ann_date", "end_date", "exp_date"}
NUMERIC_FIELDS = {"vol", "amount", "high_limit", "low_limit"}


def required_env(*names: str) -> dict[str, str]:
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"缺环境变量 {missing}（不回显值）")
    return {name: os.environ[name] for name in names}


def is_nullish(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) \
        or str(value).strip() in {"", "None", "nan", "NaT"}


def as_text(value) -> str | None:
    return None if is_nullish(value) else str(value).strip()


def as_date(value) -> date | None:
    if is_nullish(value):
        return None
    return datetime.strptime(str(value).strip()[:8], "%Y%m%d").date()


def as_decimal_text(value) -> str | None:
    text = as_text(value)
    if text is None:
        return None
    try:
        return format(Decimal(text), "f")
    except InvalidOperation as exc:
        raise RuntimeError(f"numeric字段不可解析：{text!r}") from exc


def normalize_source_row(record: dict, pull_time: datetime) -> tuple:
    values = []
    for field in FIELD_NAMES:
        value = record.get(field)
        if field in DATE_FIELDS:
            values.append(as_date(value))
        elif field in NUMERIC_FIELDS:
            values.append(as_decimal_text(value))
        else:
            values.append(as_text(value))
    ann_date = values[FIELD_NAMES.index("ann_date")]
    valid_time = datetime.combine(ann_date, datetime.min.time(), tzinfo=timezone.utc) \
        if ann_date else pull_time
    return tuple(values) + (valid_time,)


def month_windows(start: date, end: date) -> list[tuple[date, date]]:
    if start > end:
        raise ValueError("起点晚于终点")
    windows = []
    cursor = start
    while cursor <= end:
        next_month = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)
        window_end = min(end, next_month - timedelta(days=1))
        windows.append((cursor, window_end))
        cursor = window_end + timedelta(days=1)
    return windows


def window_key(window: tuple[date, date]) -> str:
    return f"{window[0]:%Y%m%d}-{window[1]:%Y%m%d}"
