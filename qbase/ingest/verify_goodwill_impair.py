#!/usr/bin/env python3
"""exp21 数据闭合件的离线最小攻击验证。"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd

from qbase.ingest.balancesheet_common import (
    FIELD_NAMES, normalize_source_row, quarter_periods, required_env,
)
from qbase.ingest.goodwill_disclosure import (
    amount_evidence, carrier_from_title, has_revision_marker, is_candidate_title,
)
from qbase.ingest.profile_goodwill_impair import build_profile
from qbase.ingest.seed_balancesheet import fetch_period, load_responses, validate_page
from qbase.ingest.verify_goodwill_disclosure import document_search_start

checks = 0


def check(label, got, expected) -> None:
    global checks
    checks += 1
    if got != expected:
        raise AssertionError(f"{label}: got={got!r} expected={expected!r}")


def source_row(**changes) -> dict:
    row = {field: None for field in FIELD_NAMES}
    row.update({"ts_code": "000001.SZ", "ann_date": "20240420", "f_ann_date": "20240422",
                "end_date": "20231231", "report_type": "1", "comp_type": "1",
                "update_flag": "0", "goodwill": "100.50",
                "total_hldr_eqy_exc_min_int": "1000",
                "total_hldr_eqy_inc_min_int": "1100"})
    row.update(changes)
    return row


class FakePro:
    def __init__(self, pages: list[pd.DataFrame]):
        self.pages = pages

    def query(self, api_name, **kwargs):
        check("VIP接口", api_name, "balancesheet_vip")
        return self.pages[kwargs["offset"] // 4000]


def test_common_and_collector() -> None:
    periods = quarter_periods(2023, date(2024, 7, 1))
    check("季度全集", periods, ["20230331", "20230630", "20230930", "20231231",
                                   "20240331", "20240630"])
    normalized = normalize_source_row(source_row(), datetime(2026, 8, 9, tzinfo=timezone.utc))
    check("实际公告日优先", normalized[-1].date(), date(2024, 4, 22))
    check("Decimal忠实", normalized[FIELD_NAMES.index("goodwill")], "100.50")
    frame = pd.DataFrame([source_row()], columns=FIELD_NAMES)
    validate_page(frame, "20231231", 0)
    check("合法页", True, True)
    bad = frame.rename(columns={"goodwill": "extra"})
    try:
        validate_page(bad, "20231231", 0)
        raise AssertionError("字段漂移未拒绝")
    except RuntimeError as exc:
        check("字段漂移拒绝", "字段漂移" in str(exc), True)
    mixed = pd.DataFrame([source_row(end_date="20230930")], columns=FIELD_NAMES)
    try:
        validate_page(mixed, "20231231", 0)
        raise AssertionError("混报告期未拒绝")
    except RuntimeError as exc:
        check("混报告期拒绝", "混入" in str(exc), True)
    payload = fetch_period(FakePro([frame]), "20231231")
    check("分页终止", (payload["pages"], len(payload["records"])), (1, 1))
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "checkpoint.jsonl"
        item = {"period": "20231231", "columns": FIELD_NAMES, "pages": 1, "records": []}
        path.write_text(json.dumps(item) + "\n" + json.dumps(item) + "\n")
        try:
            load_responses(path, {"20231231"})
            raise AssertionError("重复断点未拒绝")
        except RuntimeError as exc:
            check("重复断点拒绝", "重复" in str(exc), True)


def test_disclosure() -> None:
    exact = amount_evidence("公司预计计提商誉减值准备为1.25亿元。")
    check("精确金额", exact["status"], "qualified")
    check("精确金额换元", exact["selected"]["low_cny"], Decimal("125000000.00"))
    interval = amount_evidence("预计计提商誉减值准备为8000万元至1.2亿元。")
    check("跨单位区间不误算", interval["status"], "qualified")
    check("区间下限", interval["selected"]["low_cny"], Decimal("80000000"))
    combined = amount_evidence("商誉及无形资产减值合计，计提商誉减值准备为5000万元。")
    check("组合金额拒绝", combined["status"], "combined_unseparable")
    check("定性不量化", amount_evidence("商誉可能发生减值")["status"], "not_quantified")
    conflict = amount_evidence("计提商誉减值为1亿元，修订为计提商誉减值为2亿元。")
    check("金额冲突", conflict["status"], "amount_conflict")
    check("标题仅定位", is_candidate_title("2023年度业绩预告"), True)
    check("问询排除", is_candidate_title("关于商誉减值问询回复"), False)
    check("载体分类", carrier_from_title("2023年度业绩快报"), "express")
    check("修订标记", has_revision_marker("业绩预告修订公告", ""), True)
    check("修正标记", has_revision_marker("业绩预告修正公告", ""), True)
    check("F1检索不以后验期末截断", document_search_start(date(2023, 12, 31)),
          date(2023, 1, 1))


def test_profile_and_ddl() -> None:
    row = source_row()
    normalized = normalize_source_row(row, datetime(2026, 8, 9, tzinfo=timezone.utc))
    fields = dict(zip(FIELD_NAMES, normalized[:len(FIELD_NAMES)]))
    for field in ("goodwill", "total_hldr_eqy_exc_min_int", "total_hldr_eqy_inc_min_int"):
        fields[field] = Decimal(fields[field]) if fields[field] is not None else None
    forecasts = [{"ts_code": "000001.SZ", "ann_date": date(2024, 5, 1),
                  "first_ann_date": date(2024, 5, 1), "end_date": date(2023, 12, 31),
                  "summary": "", "change_reason": "商誉"}]
    profile = build_profile(20, [fields], forecasts)
    check("画像行守恒", profile["scope_rows"], 1)
    check("召回仅NFV", profile["locator_prior_equity_shape_nfv"],
          {"denominator_positive": 1})
    ddl = Path("qbase/sql/029_goodwill_impair_reader.sql").read_text(encoding="utf-8")
    check("holdout双焊", ddl.count("COALESCE(b.f_ann_date,b.ann_date)<DATE '2024-07-01'"), 2)
    check("SHSZ双白名单", ddl.count("b.ts_code ~ '\\.(SH|SZ)$'"), 2)
    check("snap钉批", "study_snap_batch('balancesheet')" in ddl, True)
    check("append-only三路", "BEFORE UPDATE OR DELETE ON public.balancesheet_pit_snap" in ddl
          and "BEFORE TRUNCATE ON public.balancesheet_pit_snap" in ddl, True)
    check("底表不授引擎", "GRANT SELECT ON public.balancesheet_pit_snap TO taosha_engine" in ddl,
          False)


def main() -> int:
    test_common_and_collector()
    test_disclosure()
    test_profile_and_ddl()
    old = os.environ.pop("TEST_GOODWILL_MISSING", None)
    try:
        try:
            required_env("TEST_GOODWILL_MISSING")
            raise AssertionError("缺环境变量未拒绝")
        except RuntimeError as exc:
            check("凭据不回显", "TEST_GOODWILL_MISSING" in str(exc), True)
    finally:
        if old is not None:
            os.environ["TEST_GOODWILL_MISSING"] = old
    print(f"verify_goodwill_impair: {checks}/{checks} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
