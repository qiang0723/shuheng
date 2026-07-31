#!/usr/bin/env python3
"""exp18 fina_audit 采集件离线最小验证。"""
import os
from datetime import datetime, timezone
from unittest.mock import patch

import pandas as pd

from qbase.ingest.seed_fina_audit import (
    FIELD_NAMES,
    frame_record,
    normalize_record,
    normalized_rows,
    load_env,
    validate_frame,
    ymd,
)
from qbase.ingest.verify_fina_audit_disclosure import (
    evenly_spaced,
    is_initial_document_title,
    is_revision_title,
    select_documents,
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

    with patch.dict(os.environ, {"TUSHARE_TOKEN": "token", "QBASE_APP_DSN": "dsn"}, clear=True):
        check("环境变量优先且不读文件", load_env("/不存在/也不应读取"),
              {"TUSHARE_TOKEN": "token", "QBASE_APP_DSN": "dsn"})

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

    check("初始年度报告标题", is_initial_document_title("2023年年度报告", 2023), True)
    check("摘要不作原件", is_initial_document_title("2023年年度报告摘要", 2023), False)
    check("修订标题", is_revision_title("2023年年度报告（修订稿）", 2023), True)
    check("延期披露不是原件", is_initial_document_title("关于延期披露2023年年度报告的公告", 2023), False)
    check("涉及事项不是审计原件", is_initial_document_title(
        "独立董事关于2023年度保留意见审计报告涉及事项的意见", 2023), False)
    check("均匀抽样", evenly_spaced([{"x": i} for i in range(10)], 3),
          [{"x": 0}, {"x": 4}, {"x": 9}])
    check("无公告安全返回", select_documents([], 2023), ([], []))

    print(f"verify_fina_audit: {checks}/{checks} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
