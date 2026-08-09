"""exp21 资产负债表 PIT 资产的字段、期间与忠实解析。"""
from __future__ import annotations

import math
import os
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

SOURCE = "tushare:balancesheet"
HOLDOUT = date(2024, 7, 1)
FIELDS = (
    "ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,update_flag,goodwill,"
    "total_hldr_eqy_exc_min_int,total_hldr_eqy_inc_min_int"
)
FIELD_NAMES = tuple(FIELDS.split(","))
DATE_FIELDS = {"ann_date", "f_ann_date", "end_date"}
NUMERIC_FIELDS = {
    "goodwill", "total_hldr_eqy_exc_min_int", "total_hldr_eqy_inc_min_int",
}


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


def quarter_periods(start_year: int = 1990, end: date = HOLDOUT) -> list[str]:
    periods = []
    for year in range(start_year, end.year + 1):
        for suffix in ("0331", "0630", "0930", "1231"):
            value = date.fromisoformat(f"{year}-{suffix[:2]}-{suffix[2:]}")
            if value < end:
                periods.append(f"{year}{suffix}")
    return periods


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
    actual = values[FIELD_NAMES.index("f_ann_date")]
    announced = values[FIELD_NAMES.index("ann_date")]
    disclosed = actual or announced
    valid_time = datetime.combine(disclosed, datetime.min.time(), tzinfo=timezone.utc) \
        if disclosed else pull_time
    return tuple(values) + (valid_time,)
