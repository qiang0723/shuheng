"""exp568 driver、family trial2 与报告分支专项 fixture（零数据库）。"""
from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.engine import report, runner  # noqa: E402
from taosha.experiment.pap import canonical_pap_sha256  # noqa: E402
from taosha.harness.make_ashare_fixture import generate, write_csv  # noqa: E402
from taosha.harness.run_ashare_study import synth_pap  # noqa: E402
from taosha.harness.run_st_imposition_study import (  # noqa: E402
    ENGINE_PARAM_KEYS,
    EVENT_LAYER,
    FAMILY_TRIAL,
    PAP_DIGEST,
    engine_kwargs_from_pap,
    events_from_namechange,
    selection_audit,
)
from taosha.reader.synthetic import SyntheticReader  # noqa: E402

FAIL = 0
N = 0
PAP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "docs", "st-imposition-pap-final-2026-07-29.json")


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    FAIL += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


with open(PAP_PATH, "rb") as handle:
    raw = handle.read()
    pap = json.loads(raw)

check("终版文件SHA", hashlib.sha256(raw).hexdigest(), PAP_DIGEST)
check("终版canonical", canonical_pap_sha256(pap), PAP_DIGEST)
check("family_trial运行时键不进digest",
      canonical_pap_sha256(dict(pap, _family_trial=FAMILY_TRIAL)), PAP_DIGEST)
check("实质键篡改必变", canonical_pap_sha256(dict(pap, sample_gate=31)) == PAP_DIGEST, False)

kwargs = engine_kwargs_from_pap(pap)
check("engine_params键集逐字消费", set(pap["engine_params"]), set(ENGINE_PARAM_KEYS))
check("冻结引擎实参", kwargs, {
    "benchmark_mode": "market", "strata_enabled": False,
    "st_mode": "event_day", "st_policy": "keep",
    "verdict_policy": "adj_bmp_main_only", "nfv_structured": True,
    "postpone_policy": "missing_bar_only", "diagnostic_dims": (),
})
for mutation, token in [
    ({k: v for k, v in pap["engine_params"].items() if k != "verdict_policy"}, "verdict_policy"),
    (dict(pap["engine_params"], free_choice=True), "free_choice"),
    (dict(pap["engine_params"], postpone_policy="unified"), "missing_bar_only"),
]:
    bad = dict(pap, engine_params=mutation)
    try:
        engine_kwargs_from_pap(bad)
        check(f"篡改{token} fail-closed", "放行", "SystemExit")
    except SystemExit as error:
        check(f"篡改{token} fail-closed", token in str(error), True)


def nr(ts, alias, start, ann):
    return {
        "ts_code": ts,
        "alias": alias,
        "start_date": dt.date.fromisoformat(start),
        "ann_date": dt.date.fromisoformat(ann),
        "snapshot_batch": "batch7",
    }


rows = [
    nr("000001.SZ", "甲股份", "2018-01-01", "2017-12-29"),
    nr("000001.SZ", "*ST甲", "2020-04-30", "2020-04-29"),
    nr("000002.SZ", "乙股份", "2018-01-01", "2017-12-29"),
    nr("000002.SZ", "ST乙", "2021-04-30", "2021-04-29"),
]
events, selection = events_from_namechange(rows, "study_snapshot:999")
check("EventRow两事件", len(events), 2)
check("EventRow锚与层", (events[0].event_id, events[0].event_type_layer,
                         events[0].snapshot_batch),
      ("000001.SZ:20200429", EVENT_LAYER, "study_snapshot:999"))
shuffled = list(rows)
random.Random(8).shuffle(shuffled)
events2, _ = events_from_namechange(shuffled, "study_snapshot:999")
check("driver内部排序确定性", [event.event_id for event in events2],
      [event.event_id for event in events])

audit = selection_audit(selection)
check("漏斗+组成双恒等式", (audit["funnel_identity_ok"],
                           audit["composition_audit"]["identity_ok"]), (True, True))
check("组成审计NFV且零verdict键", (
    audit["composition_audit"]["not_for_verdict"],
    sum(1 for key in json.dumps(audit, ensure_ascii=False).split('"') if key == "verdict"),
), (True, 0))


def try_render(result):
    try:
        return report.render(result), None
    except SystemExit as error:
        return None, str(error)


_, error = try_render({"audit": {"st_imposition_selection": {},
                                  "benchmark_mode": "market"}})
check("报告缺真实快照锚fail-closed", error is not None and "st_imposition" in error, True)

with tempfile.TemporaryDirectory() as directory:
    prices, event_file, meta = (os.path.join(directory, name)
                                for name in ("p.csv", "e.csv", "m.json"))
    write_csv(generate(), prices, event_file, meta)
    synthetic_events = [dataclasses.replace(event, event_type_layer=EVENT_LAYER)
                        for event in SyntheticReader(prices, event_file).events()]
    synthetic_pap = dict(synth_pap(), _family_trial=FAMILY_TRIAL,
                         bias_statement=pap["bias_statement"])
    result = runner.run_study(
        SyntheticReader(prices, event_file), synthetic_pap,
        events=synthetic_events, **kwargs)
    check("trial2进入判决审计", (result["audit"]["family_trial"],
                                result["audit"]["family_alpha"]), (2, 0.025))
    result["audit"]["study_snapshot"] = {"snapshot_id": 999, "digest": "fixture"}
    result["audit"]["experiment_identity"] = {
        "exp_id": 568, "family": "delist_warning_financial", "family_trial": 2,
        "source_type": "llm", "verdict_power": "prescreen",
    }
    result["audit"]["st_imposition_selection"] = audit
    rendered = report.render(result)
    check("exp568专属标题", rendered.splitlines()[0],
          "═══ 淘沙 · 事件研究体检报告(exp568 ST/风险警示实施·事件版)═══")
    check("组成审计渲染且NFV", ("带星ST=1" in rendered,
                                "不计算分层CAR或显著性" in rendered), (True, True))
    check("trial2与llm/prescreen水印在场",
          "family=delist_warning_financial trial=2 α=0.025 source=llm power=prescreen"
          in rendered, True)
    check("exp12标题不冒充且exp22代理禁令在场",
          ("exp12 ST/风险警示完整撤销" in rendered,
           "不得把*ST名称代理冒充exp22正式事件集" in rendered), (False, True))

    # 既有 exp12 标题分支不变
    result12 = dict(result)
    result12["audit"] = dict(result["audit"])
    del result12["audit"]["st_imposition_selection"]
    del result12["audit"]["experiment_identity"]
    result12["audit"]["st_removal_selection"] = {
        "counters": {}, "execution_limit_audit": {},
    }
    rendered12 = report.render(result12)
    check("exp12分支零回归", rendered12.splitlines()[0],
          "═══ 淘沙 · 事件研究体检报告(exp12 ST/风险警示完整撤销·事件版)═══")

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
