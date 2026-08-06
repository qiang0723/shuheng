"""exp19 dividend 数据资产的字段、解析与环境边界。"""
from __future__ import annotations

import math
import os
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

SOURCE = "tushare:dividend"
HOLDOUT = date(2024, 7, 1)
FIELDS = (
    "ts_code,end_date,ann_date,div_proc,stk_div,stk_bo_rate,stk_co_rate,cash_div,"
    "cash_div_tax,record_date,ex_date,pay_date,div_listdate,imp_ann_date,base_date,"
    "base_share,update_flag"
)
FIELD_NAMES = tuple(FIELDS.split(","))
DATE_FIELDS = {
    "end_date", "ann_date", "record_date", "ex_date", "pay_date",
    "div_listdate", "imp_ann_date", "base_date",
}
NUMERIC_FIELDS = {
    "stk_div", "stk_bo_rate", "stk_co_rate", "cash_div", "cash_div_tax", "base_share",
}


def required_env(*names: str) -> dict[str, str]:
    """只从进程环境读取凭据；错误只报告变量名，不回显值。"""
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"缺环境变量 {missing}（不回显值）")
    return {name: os.environ[name] for name in names}


def is_nullish(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return str(value).strip() in {"", "None", "nan", "NaT"}


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
    valid_time = (
        datetime.combine(ann_date, datetime.min.time(), tzinfo=timezone.utc)
        if ann_date else pull_time
    )
    return tuple(values) + (valid_time,)
