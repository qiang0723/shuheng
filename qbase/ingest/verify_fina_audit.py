#!/usr/bin/env python3
"""exp18 fina_audit 采集件离线最小验证。"""
from datetime import datetime, timezone

import pandas as pd

from qbase.ingest.seed_fina_audit import (
    FIELD_NAMES,
    frame_record,
    normalize_record,
    normalized_rows,
    validate_frame,
    ymd,
)


def main() -> int:
    checks = 0

    def check(label, got, expected):
        nonlocal checks
        checks += 1
        if got != expected:
            raise AssertionError(f"{label}: {got!r} != {expected!r}")

    frame = pd.DataFrame([
        {"ts_code": "000001.SZ", "ann_date": "20240315", "end_date": "20231231",
         "audit_result": "标准无保留意见", "audit_fees": 700.0,
         "audit_agency": "事务所甲", "audit_sign": "会计师甲"},
    ], columns=FIELD_NAMES)
    validate_frame(frame, "000001.SZ")
    checks += 1
    record = frame_record(frame, "000001.SZ")
    check("响应字段", tuple(record["columns"]), FIELD_NAMES)
    check("日期解析", ymd("20240315").isoformat(), "2024-03-15")

    pull_time = datetime(2026, 7, 31, tzinfo=timezone.utc)
    row = normalize_record(record["records"][0], pull_time)
    check("证券", row[0], "000001.SZ")
    check("公告日", row[1].isoformat(), "2024-03-15")
    check("报告期", row[2].isoformat(), "2023-12-31")
    check("费用文本保真", row[4], "700.0")
    check("valid_time", row[7].isoformat(), "2024-03-15T00:00:00+00:00")

    responses = {"000001.SZ": record["records"] * 2}
    rows, raw = normalized_rows(responses, pull_time)
    check("原始行", raw, 2)
    check("整行去重", len(rows), 1)

    bad = frame.rename(columns={"audit_sign": "unexpected"})
    try:
        validate_frame(bad, "000001.SZ")
    except RuntimeError as exc:
        check("字段漂移拒绝", "字段漂移" in str(exc), True)
    else:
        raise AssertionError("字段漂移未拒绝")

    mixed = frame.copy()
    mixed.loc[0, "ts_code"] = "000002.SZ"
    try:
        validate_frame(mixed, "000001.SZ")
    except RuntimeError as exc:
        check("混票拒绝", "混入其他证券" in str(exc), True)
    else:
        raise AssertionError("混票未拒绝")

    print(f"verify_fina_audit: {checks}/{checks} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
