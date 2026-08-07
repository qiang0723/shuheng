#!/usr/bin/env python3
"""exp23 repurchase 数据闭合件的离线最小攻击验证。"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd

from qbase.ingest.profile_repurchase import build_profile
from qbase.ingest.repurchase_common import (
    FIELD_NAMES, month_windows, normalize_source_row, required_env, window_key,
)
from qbase.ingest.repurchase_disclosure import (
    document_evidence, has_revision_marker, is_candidate_title, purpose_evidence,
)
from qbase.ingest.seed_repurchase import API_ROW_CEILING, load_responses, validate_frame


checks = 0


def check(name, got, expected) -> None:
    global checks
    checks += 1
    if got != expected:
        raise AssertionError(f"{name}: got={got!r} expected={expected!r}")


def frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=FIELD_NAMES)


def sample_row(**changes) -> dict:
    row = {field: None for field in FIELD_NAMES}
    row.update({"ts_code": "000001.SZ", "ann_date": "20240115", "proc": "预案",
                "high_limit": "12.50"})
    row.update(changes)
    return row


def test_common() -> None:
    windows = month_windows(date(2024, 1, 15), date(2024, 3, 2))
    check("月窗无重叠", windows, [(date(2024, 1, 15), date(2024, 1, 31)),
                                  (date(2024, 2, 1), date(2024, 2, 29)),
                                  (date(2024, 3, 1), date(2024, 3, 2))])
    check("窗口键", window_key(windows[0]), "20240115-20240131")
    row = normalize_source_row(sample_row(), datetime(2024, 2, 1, tzinfo=timezone.utc))
    check("日期解析", row[FIELD_NAMES.index("ann_date")], date(2024, 1, 15))
    check("Decimal忠实", row[FIELD_NAMES.index("high_limit")], "12.50")


def test_collector() -> None:
    window = (date(2024, 1, 1), date(2024, 1, 31))
    validate_frame(frame([sample_row()]), window)
    check("正常frame", True, True)
    bad = frame([sample_row(ann_date="20240201")])
    try:
        validate_frame(bad, window)
        raise AssertionError("窗外日期未拒绝")
    except RuntimeError as exc:
        check("窗外日期拒绝", "窗外" in str(exc), True)
    try:
        validate_frame(pd.DataFrame([{**sample_row(), "extra": 1}]), window)
        raise AssertionError("字段漂移未拒绝")
    except RuntimeError as exc:
        check("字段漂移拒绝", "字段漂移" in str(exc), True)
    ceiling = frame([sample_row() for _ in range(API_ROW_CEILING)])
    try:
        validate_frame(ceiling, window)
        raise AssertionError("触顶未拒绝")
    except RuntimeError as exc:
        check("触顶拒绝", "触顶" in str(exc), True)
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "checkpoint.jsonl"
        payload = {"window": "20240101-20240131", "columns": FIELD_NAMES, "records": []}
        path.write_text(json.dumps(payload) + "\n" + json.dumps(payload) + "\n")
        try:
            load_responses(path, {payload["window"]})
            raise AssertionError("重复窗口未拒绝")
        except RuntimeError as exc:
            check("重复窗口拒绝", "重复" in str(exc), True)


def test_disclosure() -> None:
    cancellation = "董事会审议通过回购股份方案，回购股份将全部予以注销并减少注册资本。"
    inventory = "董事会审议通过回购股份方案，本次回购股份用于员工持股计划。"
    mixed = cancellation + "部分用于股权激励。"
    check("注销正文", purpose_evidence(cancellation)["category"], "cancellation")
    check("库存正文", purpose_evidence(inventory)["category"], "inventory")
    check("混合用途", purpose_evidence(mixed)["category"], "other_explicit")
    check("无证据不可分类", purpose_evidence("公司经营正常")["category"], "unclassifiable")
    check("限制股正文注销", purpose_evidence(
        "公司同意将本次回购注销的限制性股票办理注销手续。"
    )["category"], "cancellation")
    check("减资注销正文", purpose_evidence(
        "公司将办理减少注册资本和股份注销登记等手续。"
    )["category"], "cancellation")
    check("标题不得单独判用途", purpose_evidence(
        "关于回购注销部分限制性股票的公告"
    )["category"], "unclassifiable")
    check("标题只定位正例", is_candidate_title("关于回购股份方案的公告"), True)
    check("限制股注销原件可定位", is_candidate_title("关于回购注销部分限制性股票的公告"), True)
    check("法律意见非发行人原件", is_candidate_title("关于回购注销的法律意见书"), False)
    check("进展标题排除", is_candidate_title("关于回购股份进展的公告"), False)
    text = "董事会审议通过关于回购股份方案的议案，回购价格不超过12.50元/股。" + inventory
    proof = document_evidence(text, Decimal("12.50"))
    check("首次披露三合取", proof["first_disclosure_supported"], True)
    check("价格零容差", document_evidence(text, Decimal("12.51"))["exact_high_limit_match"], False)
    fixed = "董事会审议通过回购股份方案，回购价格为8.20元/股。" + cancellation
    check("固定回购价精确匹配", document_evidence(fixed, Decimal("8.20"))[
        "exact_high_limit_match"], True)
    not_higher = "董事会审议通过回购股份方案，回购股份的价格不高于12元/股。" + inventory
    check("不高于价格精确匹配", document_evidence(not_higher, Decimal("12"))[
        "exact_high_limit_match"], True)
    revision = text + "这是调整后的回购股份方案。"
    check("修订正文拒绝", document_evidence(revision, Decimal("12.50"))[
        "first_disclosure_supported"], False)
    future_adjustment = text + "若政策调整，本回购方案按调整后的政策实施。"
    check("未来政策调整非修订件", has_revision_marker(future_adjustment), False)
    check("标题不参与用途", proof["purpose"]["title_used_for_purpose"], False)


def test_profile_and_ddl() -> None:
    rows = [sample_row(ann_date=date(2024, 1, 15), high_limit=Decimal("12.5")),
            sample_row(ann_date=date(2024, 1, 16), high_limit=Decimal("12.5")),
            sample_row(ann_date=date(2024, 1, 16), proc="完成", high_limit=Decimal("12.5"))]
    payload = build_profile(18, rows)
    check("预案键", payload["proposal_c1"]["proposal_keys"], 2)
    check("C1划分", payload["proposal_c1"]["single_row_keys"], 1)
    check("C1多行", payload["proposal_c1"]["c1_multirow_keys"], 1)
    check("多方案身份待证", payload["single_proposal_securities_with_multiple_dates"], 0)
    ddl = Path("qbase/sql/027_buyback_announce_reader.sql").read_text(encoding="utf-8")
    check("snap钉批", "study_snap_batch('repurchase')" in ddl, True)
    check("holdout双焊", ddl.count("ann_date<DATE '2024-07-01'"), 2)
    check("A股后缀双白名单", ddl.count("ts_code ~ '\\.(SH|SZ)$'") , 2)
    check("append-only三路", "BEFORE UPDATE OR DELETE ON public.repurchase_snap" in ddl
          and "BEFORE TRUNCATE ON public.repurchase_snap" in ddl, True)
    check("引擎仅视图授权", "GRANT SELECT ON public.repurchase_snap TO taosha_engine" in ddl, False)


def main() -> int:
    test_common()
    test_collector()
    test_disclosure()
    test_profile_and_ddl()
    old = os.environ.pop("TEST_REPURCHASE_MISSING", None)
    try:
        try:
            required_env("TEST_REPURCHASE_MISSING")
            raise AssertionError("缺环境变量未拒绝")
        except RuntimeError as exc:
            check("环境缺失不回显值", "TEST_REPURCHASE_MISSING" in str(exc), True)
    finally:
        if old is not None:
            os.environ["TEST_REPURCHASE_MISSING"] = old
    print(f"verify_repurchase: {checks}/{checks} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
