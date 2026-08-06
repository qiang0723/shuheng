#!/usr/bin/env python3
"""exp19 dividend 数据闭合件的离线最小攻击验证。"""
from __future__ import annotations

import os
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from qbase.ingest.dividend_common import FIELD_NAMES, normalize_source_row, required_env
from qbase.ingest.profile_dividend import candidate_funnel, classify_group
from qbase.ingest.seed_dividend import validate_frame
from qbase.ingest.verify_dividend_disclosure import cash_per_ten_values, is_proposal_title


def main() -> int:
    checks = 0

    def check(label, got, expected):
        nonlocal checks
        checks += 1
        if got != expected:
            raise AssertionError(f"{label}: {got!r}!={expected!r}")

    row = {field: None for field in FIELD_NAMES}
    row.update({"ts_code": "000001.SZ", "end_date": "20231231", "ann_date": "20240315",
                "div_proc": "预案", "cash_div_tax": "0.15", "update_flag": "0"})
    frame = pd.DataFrame([row], columns=FIELD_NAMES)
    validate_frame(frame, "000001.SZ")
    checks += 1
    normalized = normalize_source_row(row, datetime(2026, 8, 6, tzinfo=timezone.utc))
    check("日期解析", normalized[FIELD_NAMES.index("ann_date")], date(2024, 3, 15))
    check("Decimal文本", normalized[FIELD_NAMES.index("cash_div_tax")], "0.15")

    with patch.dict(os.environ, {"TUSHARE_TOKEN": "x", "QBASE_APP_DSN": "y"}, clear=True):
        check("环境变量唯一来源", required_env("TUSHARE_TOKEN", "QBASE_APP_DSN"),
              {"TUSHARE_TOKEN": "x", "QBASE_APP_DSN": "y"})

    missing = frame.rename(columns={"base_share": "unexpected"})
    try:
        validate_frame(missing, "000001.SZ")
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

    member = {"div_proc": "预案", "update_flag": "0", "ann_date": date(2024, 3, 15),
              "cash_div_tax": Decimal("0.15"), "base_date": None, "base_share": None}
    check("E1单行", classify_group([member])[0], "qualified")
    check("E1重复整组拒", classify_group([member, member])[0], "initial_multiple_identical")
    later = dict(member, div_proc="实施")
    check("实施值不回填", classify_group([later])[0], "initial_missing")

    groups = {
        ("000001.SZ", date(2022, 12, 31)): [member],
        ("000001.SZ", date(2023, 12, 31)): [member],
    }
    qualified = {
        ("000001.SZ", date(2022, 12, 31)): dict(member, cash_div_tax=Decimal("0.10")),
        ("000001.SZ", date(2023, 12, 31)): dict(member, cash_div_tax=Decimal("0.15")),
    }
    funnel, _ = candidate_funnel(groups, qualified)
    check("恰+50%入up", funnel["up"], 1)
    check("恰边界计数", funnel["exact_boundary"], 1)

    check("预案标题", is_proposal_title("2023年度利润分配预案公告"), True)
    check("实施标题排除", is_proposal_title("2023年度权益分派实施公告"), False)
    text = "公司拟向全体股东每10股派发现金红利1.50元（含税）。"
    check("税前金额精确抽取", cash_per_ten_values(text), [Decimal("1.50")])
    check("无保真含税词不接受", cash_per_ten_values("每10股派发现金红利1.50元"), [])

    ddl = Path("qbase/sql/026_dividend_surprise_reader.sql").read_text(encoding="utf-8")
    check("current holdout", ddl.count("d.ann_date<DATE '2024-07-01'"), 2)
    check("snap钉批", "study_snap_batch('dividend')" in ddl, True)
    check("append-only update/delete", "BEFORE UPDATE OR DELETE ON public.dividend_snap" in ddl, True)
    check("append-only truncate", "BEFORE TRUNCATE ON public.dividend_snap" in ddl, True)

    print(f"verify_dividend: {checks}/{checks} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
