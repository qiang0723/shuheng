"""exp17 driver/report/reader 适配攻击 fixture；零数据库、合成收益。"""
from __future__ import annotations

import copy
import dataclasses
import datetime as dt
import hashlib
import json
import os
import sys
import tempfile

from taosha.engine import report as report_mod
from taosha.engine import runner
from taosha.experiment.pap import canonical_pap_sha256
from taosha.harness.make_ashare_fixture import generate, write_csv
from taosha.harness.run_ashare_study import synth_pap
from taosha.harness.run_earnings_flash_gap_study import (
    ENGINE_PARAM_KEYS, PAP_DIGEST, REFERENCE, SIGNED_AR_KEYS,
    assert_formal_snapshot, attach_experiment_identity, engine_kwargs_from_pap,
    event_rows, selection_audit,
)
from taosha.reader.synthetic import SyntheticReader


FAIL = 0
N = 0
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAP_PATH = os.path.join(ROOT, "taosha", "docs",
                        "earnings-flash-gap-pap-final-2026-07-30.json")
SQL_PATH = os.path.join(ROOT, "qbase", "sql", "024_earnings_flash_gap_reader.sql")


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    FAIL += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


def failure(fn):
    try:
        fn()
        return ""
    except SystemExit as exc:
        return str(exc)


with open(PAP_PATH, "rb") as handle:
    raw = handle.read()
pap = json.loads(raw)
kwargs = engine_kwargs_from_pap(pap)
check("A1 文件SHA", hashlib.sha256(raw).hexdigest(), PAP_DIGEST)
check("A1 canonical", canonical_pap_sha256(pap), PAP_DIGEST)
check("A1 运行时键不进digest", canonical_pap_sha256(dict(pap, _family_trial=9)), PAP_DIGEST)
check("A2 19键含signed_ar", (len(pap), "signed_ar" in pap), (19, True))
check("A2 engine_params逐字消费", set(pap["engine_params"]), set(ENGINE_PARAM_KEYS))
check("A2 signed_ar逐字消费", set(pap["signed_ar"]), set(SIGNED_AR_KEYS))
check("A2 signed路径与A1/ST冻结值",
      (kwargs["direction_signed_main"], kwargs["effect_alignment_source"],
       kwargs["postpone_policy"], kwargs["st_policy"]),
      (True, "adj_bmp_sign", "unified_announcement", "reject"))

missing = dict(pap, engine_params={key: value for key, value in pap["engine_params"].items()
                                   if key != "st_policy"})
extra = dict(pap, engine_params=dict(pap["engine_params"], st_mode="event_day"))
check("A3 engine缺键fail-closed", "st_policy" in failure(
    lambda: engine_kwargs_from_pap(missing)), True)
check("A3 engine多键fail-closed", "st_mode" in failure(
    lambda: engine_kwargs_from_pap(extra)), True)
bad_signed = dict(pap, signed_ar={key: value for key, value in pap["signed_ar"].items()
                                  if key != "formula"})
check("A3 signed_ar缺键fail-closed", "signed_ar" in failure(
    lambda: engine_kwargs_from_pap(bad_signed)), True)
bad_axes = copy.deepcopy(pap)
bad_axes["diagnostic_dimensions"]["axes"]["direction"] = ["down", "up"]
check("A3 方向白名单只取PAP且顺序篡改即拒", "axes.direction" in failure(
    lambda: engine_kwargs_from_pap(bad_axes)), True)
check("A3 driver不向引擎传exp24 direction_layers", "direction_layers" in kwargs, False)

fixture_selection = {
    "events": [
        {"ts_code": "000001.SZ", "event_date": dt.date(2020, 4, 1),
         "direction": "up"},
        {"ts_code": "000002.SZ", "event_date": dt.date(2020, 4, 2),
         "direction": "down"},
    ],
    "counters": dict(REFERENCE), "classification_yearly": {},
    "classification_identity_ok": True, "event_identity_ok": True,
    "yearly_identity_ok": True, "selection_sha256": "fixture",
}
events = event_rows(fixture_selection, "fixture")
check("A4 EventRow方向层与锚",
      [(row.event_type_layer, row.first_ann_date) for row in events],
      [("up", fixture_selection["events"][0]["event_date"]),
       ("down", fixture_selection["events"][1]["event_date"])])
audit = selection_audit(fixture_selection)
check("A4 选择审计身份三项", audit["identities"],
      {"classification": True, "event": True, "yearly": True})
check("A4 source340正式冒充fail-closed", "不得冒充" in failure(
    lambda: assert_formal_snapshot(340)), True)
check("A4 exp17自有manifest ID放行", failure(lambda: assert_formal_snapshot(999)), "")

with open(SQL_PATH, encoding="utf-8") as handle:
    sql = handle.read()
check("A5 current/snap专属视图俱在",
      ("explore_reader_forecast_profit AS" in sql,
       "explore_reader_forecast_profit_snap AS" in sql), (True, True))
check("A5 snap经manifest路由且holdout排北焊死",
      ("study_snap_batch('forecast')" in sql,
       sql.count("ann_date < DATE '2024-07-01'") == 2,
       sql.count("ts_code !~ '\\.BJ$'") == 2), (True, True, True))
check("A5 最小列面含利润上下沿且只授只读",
      ("net_profit_min" in sql and "net_profit_max" in sql,
       sql.count("GRANT SELECT") == 2), (True, True))


def render_attempt(result):
    try:
        return report_mod.render(result), ""
    except SystemExit as exc:
        return "", str(exc)


_, error = render_attempt({"audit": {"earnings_flash_gap_selection": {}}})
check("A6 缺快照锚fail-closed", "exp17缺真实StudySnapshot锚" in error, True)

with tempfile.TemporaryDirectory() as td:
    prices, event_csv, meta = (os.path.join(td, name) for name in ("p.csv", "e.csv", "m.json"))
    write_csv(generate(), prices, event_csv, meta)
    base_events = list(SyntheticReader(prices, event_csv).events())
    signed_events = [dataclasses.replace(
        event, event_type_layer="up" if index % 2 == 0 else "down")
        for index, event in enumerate(base_events)]
    run_pap = dict(synth_pap(), _family_trial=1, bias_statement=pap["bias_statement"],
                   diagnostic_dimensions=pap["diagnostic_dimensions"],
                   signed_ar=pap["signed_ar"])
    result = runner.run_study(
        SyntheticReader(prices, event_csv), run_pap, events=signed_events, **kwargs)
    result["audit"]["study_snapshot"] = {"snapshot_id": 0, "digest": "fixture"}
    result["audit"]["earnings_flash_gap_selection"] = audit
    before = (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True,
                         default=str) + "\n").encode()
    attach_experiment_identity(result, {
        "exp_id": 17, "family": "earnings_flash_gap", "family_trial": 1,
        "source_type": "llm", "verdict_power": "prescreen",
    })
    restored = copy.deepcopy(result)
    del restored["audit"]["experiment_identity"]
    check("A7 身份写入恰新增audit一键",
          (json.dumps(restored, ensure_ascii=False, indent=2, sort_keys=True,
                      default=str) + "\n").encode() == before, True)
    rendered = report_mod.render(result)
    check("A7 exp17真锚标题", rendered.splitlines()[0],
          "═══ 淘沙 · 事件研究体检报告(exp17 业绩快报偏离预告·signed事件版)═══")
    check("A7 llm/prescreen水印在场",
          "family=earnings_flash_gap trial=1 source=llm power=prescreen" in rendered, True)
    check("A7 A1/B1/C1漏斗与signed单判决说明在场",
          ("exp17 A1/B1/C1事件生成漏斗" in rendered,
           "合并signed事件集产生一个verdict" in rendered), (True, True))
    missing_identity = copy.deepcopy(result)
    del missing_identity["audit"]["experiment_identity"]
    _, error = render_attempt(missing_identity)
    check("A7 删除身份水印fail-closed", "实验身份水印" in error, True)
    check("A7 递归verdict唯一", json.dumps(result, ensure_ascii=False).count('"verdict"'), 1)

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
