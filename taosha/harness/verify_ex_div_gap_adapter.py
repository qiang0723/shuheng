"""exp14 冻结/driver/report/reader 适配攻击 fixture；零数据库连接。"""
from __future__ import annotations

import copy
import dataclasses
import datetime as dt
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

from taosha.engine import report as report_mod
from taosha.engine import runner
from taosha.experiment.pap import canonical_pap_sha256
from taosha.harness.make_ashare_fixture import generate, write_csv
from taosha.harness.run_ashare_study import synth_pap
from taosha.harness.run_ex_div_gap_recon import (
    ENGINE_PARAM_KEYS, EXPECTED_BATCHES, PAP_DIGEST, REFERENCE, SOURCE_SNAPSHOT_ID,
    _assert_equal, _assert_snapshot, assert_formal_snapshot, assert_reference,
    attach_experiment_identity, engine_kwargs_from_pap, event_rows,
    execution_limit_audit, selection_audit,
)
from taosha.reader.ex_div_gap import VIEWS
from taosha.reader.synthetic import SyntheticReader


FAIL = 0
N = 0


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    FAIL += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


def raises(name, function, contains):
    try:
        function()
    except SystemExit as exc:
        check(name, contains in str(exc), True)
    else:
        check(name, "未拒绝", contains)


def failure(function):
    try:
        function()
        return ""
    except SystemExit as exc:
        return str(exc)


check("F1 source snapshot钉375", SOURCE_SNAPSHOT_ID, 375)
check("F2 终版PAP digest全值钉定", len(PAP_DIGEST), 64)
check("F3 三条qbase消费批次", EXPECTED_BATCHES,
      {"dividend": 17, "adj_factor": 7, "trade_cal": 10})
check("F4 current/snapshot各两张专属视图",
      (set(VIEWS), {key: len(value) for key, value in VIEWS.items()}),
      ({"current", "snapshot"}, {"current": 2, "snapshot": 2}))
check("F5 current/snapshot视图名不复用", set(VIEWS["current"]) == set(VIEWS["snapshot"])
      and not (set(VIEWS["current"].values()) & set(VIEWS["snapshot"].values())), True)

good_info = {"snapshot_id": 375, "content": {"qbase": EXPECTED_BATCHES}, "digest": "x"}
_assert_snapshot(good_info)
check("F6 snapshot375正确向量通过", True, True)
raises("F7 snapshot ID篡改拒绝",
       lambda: _assert_snapshot({**good_info, "snapshot_id": 374}), "snapshot375")
raises("F8 qbase批次篡改拒绝",
       lambda: _assert_snapshot({**good_info, "content": {"qbase": {**EXPECTED_BATCHES,
                                                                        "adj_factor": 99}}}),
       "向量不符")

base = {"source_batches": {"dividend": "batch17"}, "selection": {"events": [1]},
        "selection_content_sha256": "a"}
_assert_equal(base, dict(base))
check("F9 current/snapshot相等通过", True, True)
raises("F10 选择差异fail-closed",
       lambda: _assert_equal(base, {**base, "selection": {"events": [2]},
                                    "selection_content_sha256": "b"}), "选择不一致")
raises("F11 批次差异fail-closed",
       lambda: _assert_equal(base, {**base, "source_batches": {"dividend": "batch18"}}),
       "批次不一致")

reader = Path("taosha/reader/ex_div_gap.py").read_text(encoding="utf-8")
check("F12 连接建立即只读", 'options="-c default_transaction_read_only=on"' in reader, True)
check("F13 因子按键限量请求", reader.count("unnest(%s::text[],%s::date[])") , 1)
check("F14 reader零价格收益字段", "adj_close" in reader or "raw_close" in reader
      or "ret_eqw" in reader or "log_return" in reader, False)
recon = Path("taosha/harness/run_ex_div_gap_recon.py").read_text(encoding="utf-8")
check("F15 recon分支进入正式函数前不加载runner",
      "runner" in recon.split("def _run_formal", 1)[0], False)
formal = recon.split("def _run_formal", 1)[1].split("def main", 1)[0]
check("F16 正式三值硬闸早于收益读取",
      0 <= formal.find("assert_reference(selection)") < formal.find("ViewReader(")
      < formal.find("runner.run_study("), True)

ROOT = Path(__file__).resolve().parents[2]
pap_path = ROOT / "taosha/docs/ex-div-gap-pap-final-2026-08-09.json"
raw = pap_path.read_bytes()
pap = json.loads(raw)
kwargs = engine_kwargs_from_pap(pap)
check("A1 文件SHA/canonical双口径",
      (hashlib.sha256(raw).hexdigest(), canonical_pap_sha256(pap)),
      (PAP_DIGEST, PAP_DIGEST))
check("A1 18键无signed_ar", (len(pap), "signed_ar" in pap), (18, False))
check("A2 engine_params八键逐字消费", set(pap["engine_params"]), set(ENGINE_PARAM_KEYS))
check("A2 ST keep/missing_bar_only/同日tau0",
      (kwargs["st_policy"], kwargs["postpone_policy"], kwargs["tau0_on_anchor"]),
      ("keep", "missing_bar_only", True))
check("A2 tau0_on_anchor无CLI自由入口", "tau0-on-anchor" in recon, False)

missing = copy.deepcopy(pap)
del missing["engine_params"]["st_policy"]
extra = copy.deepcopy(pap)
extra["engine_params"]["st_mode"] = "keep"
raises("A3 engine缺键fail-closed", lambda: engine_kwargs_from_pap(missing), "st_policy")
raises("A3 engine多键fail-closed", lambda: engine_kwargs_from_pap(extra), "st_mode")
bad_text = copy.deepcopy(pap)
bad_text["window"] = bad_text["window"].replace("τ0=ex_date当日", "τ0待定")
raises("A3 同日tau0文本硬门", lambda: engine_kwargs_from_pap(bad_text), "window")
bad_signed = dict(pap, signed_ar={})
raises("A3 单事件集signed_ar旁路拒绝", lambda: engine_kwargs_from_pap(bad_signed), "signed_ar")

fixture_selection = {
    "events": [{"ts_code": "000001.SZ", "ex_date": dt.date(2021, 4, 1),
                "end_date": dt.date(2020, 12, 31), "_total": "0.5"}],
    "counters": {"implementation_rows": 1, "implementation_groups": 1,
                 "group_qualified": 1, "group_multi_null": 0,
                 "group_multi_conflict": 0, "threshold_groups": 1,
                 "pre_factor_candidates": 1, "factor_factor_changed": 1,
                 "factor_factor_static": 0, "factor_calendar_missing": 0,
                 "factor_current_missing": 0, "factor_previous_missing": 0,
                 "factor_factor_invalid": 0, **{key: value for key, value in
                    REFERENCE.items() if key != "selection_sha256"}},
    "identities": {"group": True, "threshold": True, "event_key": True,
                   "factor": True, "yearly": True, "regime": True},
    "events_yearly": {"2021": 1},
    "regulatory_composition": {"exchange_rule_period": 1},
    "factor_mechanism_audit": {"not_for_verdict": True, "events": 1,
                               "ratio_min": "1.5", "ratio_mean": "1.5",
                               "ratio_max": "1.5"},
    "selection_sha256": REFERENCE["selection_sha256"],
}
events = event_rows(fixture_selection, "fixture")
check("A4 EventRow锚与固定单层",
      [(row.first_ann_date, row.event_type_layer) for row in events],
      [(dt.date(2021, 4, 1), "ex_div_gap")])
assert_reference(fixture_selection)
check("A4 参考三值与六恒等式通过", True, True)
raises("A4 source375正式冒充拒绝", lambda: assert_formal_snapshot(375), "不得冒充")
check("A4 exp14自有manifest放行", failure(lambda: assert_formal_snapshot(999)), "")

check("A5 tau0执行审计显式核tau序", "首行不是tau0" in failure(
    lambda: execution_limit_audit({"censor_diagnostic": {"all": {
        "by_tau_censor": [{"tau": 1}]}}})), True)
audit = selection_audit(fixture_selection)
check("A5 选择审计只作NFV且参考命中",
      (audit["not_for_verdict"], audit["reference_reconciliation"]["exact_match"],
       audit["raw_price_mechanical_audit"]["raw_price_enters_car"]),
      (True, True, False))


def render_attempt(result):
    try:
        return report_mod.render(result), ""
    except SystemExit as exc:
        return "", str(exc)


_, error = render_attempt({"audit": {"ex_div_gap_selection": {}}})
check("A6 缺真实快照锚fail-closed", "exp14缺真实StudySnapshot锚" in error, True)

with tempfile.TemporaryDirectory() as td:
    prices, event_csv, meta = (os.path.join(td, name) for name in ("p.csv", "e.csv", "m.json"))
    write_csv(generate(), prices, event_csv, meta)
    base_events = list(SyntheticReader(prices, event_csv).events())
    run_events = [dataclasses.replace(event, event_type_layer="ex_div_gap")
                  for event in base_events]
    run_pap = dict(synth_pap(), _family_trial=1,
                   bias_statement=pap["bias_statement"],
                   diagnostic_dimensions=pap["diagnostic_dimensions"])
    result = runner.run_study(
        SyntheticReader(prices, event_csv), run_pap, events=run_events, **kwargs)
    result["audit"]["study_snapshot"] = {"snapshot_id": 0, "digest": "fixture"}
    formal_audit = copy.deepcopy(audit)
    formal_audit["execution_limit_audit"] = execution_limit_audit(result)
    result["audit"]["ex_div_gap_selection"] = formal_audit
    before = json.dumps(result, ensure_ascii=False, sort_keys=True, default=str)
    attach_experiment_identity(result, {
        "exp_id": 14, "family": "ex_div_gap", "family_trial": 1,
        "source_type": "llm", "verdict_power": "prescreen",
    })
    restored = copy.deepcopy(result)
    del restored["audit"]["experiment_identity"]
    check("A7 身份写入恰新增audit一键",
          json.dumps(restored, ensure_ascii=False, sort_keys=True, default=str), before)
    rendered = report_mod.render(result)
    check("A7 exp14真锚标题", rendered.splitlines()[0],
          "═══ 淘沙 · 事件研究体检报告(exp14 实际高送转除权·事件版)═══")
    check("A7 llm/prescreen水印", "family=ex_div_gap trial=1 source=llm power=prescreen" in rendered,
          True)
    check("A7 漏斗/因子/raw/监管/执行限制均NFV",
          all(text in rendered for text in (
              "A1/B1/C1/D1事件生成漏斗", "因子比", "raw除权跳空",
              "非精确法律制度分层", "τ0执行限制审计", "NOT_FOR_VERDICT")), True)
    missing_identity = copy.deepcopy(result)
    del missing_identity["audit"]["experiment_identity"]
    _, error = render_attempt(missing_identity)
    check("A7 删除身份水印fail-closed", "实验身份水印" in error, True)
    missing_execution = copy.deepcopy(result)
    del missing_execution["audit"]["ex_div_gap_selection"]["execution_limit_audit"]
    _, error = render_attempt(missing_execution)
    check("A7 删除执行限制审计fail-closed", "execution_limit_audit" in error, True)
    check("A7 递归verdict唯一", json.dumps(result, ensure_ascii=False).count('"verdict"'), 1)

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
