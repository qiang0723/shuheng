"""exp16 driver、报告与同日τ0专项fixture（零DB、合成数据）。"""
from __future__ import annotations

import copy
import dataclasses
import datetime as dt
import hashlib
import json
import os
import tempfile

from taosha.engine import report as report_mod
from taosha.engine import runner
from taosha.engine.cleaning import clean_event
from taosha.experiment.pap import canonical_pap_sha256
from taosha.harness.make_ashare_fixture import generate, write_csv
from taosha.harness.run_ashare_study import synth_pap
from taosha.harness.run_yearend_strength_study import (
    ENGINE_PARAM_KEYS, PAP_DIGEST, attach_experiment_identity, engine_kwargs_from_pap,
    _market_returns, _taosha_dsn_name, event_rows, execution_limit_audit,
    selection_audit,
)
from taosha.reader.contract import EventRow, PriceRow
from taosha.reader.synthetic import SyntheticReader


FAIL = 0
N = 0
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAP_PATH = os.path.join(ROOT, "taosha", "docs",
                        "yearend-strength-pap-final-2026-07-30.json")


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
check("A1 运行时键不进digest", canonical_pap_sha256(dict(pap, _family_trial=7)), PAP_DIGEST)
check("A2 冻结8键逐字消费", set(pap["engine_params"]), set(ENGINE_PARAM_KEYS))
check("A2 ST keep与同日τ0", (kwargs["st_policy"], kwargs["tau0_on_anchor"]), ("keep", True))
check("A2 传引擎键", set(kwargs), {
    "benchmark_mode", "diagnostic_dims", "nfv_structured", "postpone_policy",
    "st_policy", "strata_enabled", "verdict_policy", "tau0_on_anchor",
})

missing = dict(pap, engine_params={key: value for key, value in pap["engine_params"].items()
                                   if key != "st_policy"})
extra = dict(pap, engine_params=dict(pap["engine_params"], st_mode="event_day"))
check("A3 缺键fail-closed", "st_policy" in failure(lambda: engine_kwargs_from_pap(missing)), True)
check("A3 多键fail-closed", "st_mode" in failure(lambda: engine_kwargs_from_pap(extra)), True)
bad_tau = dict(pap, event_def=pap["event_def"].replace("τ0=event_date当日", "τ0待定"))
check("A3 τ0文本缺失fail-closed", "event_def" in failure(
    lambda: engine_kwargs_from_pap(bad_tau)), True)


class MarketConn:
    def __init__(self):
        self.sql = ""
        self.params = ()

    def execute(self, sql, params):
        self.sql, self.params = sql, params
        return [(dt.date(2020, 1, 2), 0.01)]


market_conn = MarketConn()
_market_returns(market_conn, {dt.date(2020, 1, 2)}, 88)
check("A4 recon显式钉market88", ("market_eqw_return" in market_conn.sql,
                                  market_conn.params[0]), (True, 88))
_market_returns(market_conn, {dt.date(2020, 1, 2)}, None)
check("A4 正式路径只走manifest视图", "market_return_snap" in market_conn.sql, True)
check("A4 recon连接强制只读app角色", _taosha_dsn_name(88), "TAOSHA_APP_DSN")
check("A4 正式连接维持engine角色", _taosha_dsn_name(None),
      "TAOSHA_ENGINE_TAOSHA_DSN")

fixture_selection = {
    "events": [{"ts_code": "000001.SZ", "event_date": "2015-01-05"}],
    "counters": {"panel_any": 1, "panel_full_11": 1, "panel_partial_rejected": 0,
                 "nonpositive_close_rejected": 0, "final_events": 1,
                 "final_securities": 1, "event_dates": 1,
                 "event_key_duplicate_groups": 0},
    "events_yearly": {"2015": 1}, "selection_sha256": "fixture",
    "event_bar_present": 1, "event_bar_missing": 0,
}
events = event_rows(fixture_selection, "fixture")
check("A5 EventRow单层", (len(events), events[0].event_type_layer), (1, "yearend_strength"))
check("A5 审计恒等式", selection_audit(fixture_selection)["panel_identity_ok"], True)

# 同日τ0须在清洗行为面成立，不能只验证driver参数值。
axis = [dt.date(2019, 1, 1) + dt.timedelta(days=index) for index in range(400)]


def clean_at(missing=(), one_word=False):
    missing = set(missing)
    rows = [
        PriceRow("A.SZ", day, 100.0, False,
                 "one_word" if one_word and index == 300 else "none",
                 "main", True, "电子")
        for index, day in enumerate(axis) if index not in missing
    ]
    event = EventRow("A.SZ", "e", axis[300], "yearend_strength", "fixture")
    return clean_event(
        rows, event, {day: index for index, day in enumerate(axis)},
        st_policy="keep", postpone_policy="missing_bar_only",
        axis_dates=axis, tau0_on_anchor=True,
    )


check("A6 同日有bar即τ0", clean_at().tau0_idx, 300)
check("A6 ST keep不剔除", clean_at().rejected, False)
one_word = clean_at(one_word=True)
check("A6 一字板有bar不顺延", (one_word.tau0_idx, one_word.postponed), (300, 0))
check("A6 缺bar顺延5日", clean_at(missing=range(300, 305)).tau0_idx, 305)
check("A6 第6日仍缺bar剔除", clean_at(missing=range(300, 306)).reject_reason,
      "postpone")


def render_attempt(result):
    try:
        return report_mod.render(result), ""
    except SystemExit as exc:
        return "", str(exc)


_, error = render_attempt({"audit": {"yearend_strength_selection": {}}})
check("A7 缺快照锚fail-closed", "yearend_strength_selection" in error, True)

with tempfile.TemporaryDirectory() as td:
    prices, event_csv, meta = (os.path.join(td, name) for name in ("p.csv", "e.csv", "m.json"))
    write_csv(generate(), prices, event_csv, meta)
    base_events = list(SyntheticReader(prices, event_csv).events())
    synthetic_events = [dataclasses.replace(event, event_type_layer="yearend_strength")
                        for event in base_events]
    run_pap = dict(synth_pap(), _family_trial=1, bias_statement=pap["bias_statement"])
    result = runner.run_study(
        SyntheticReader(prices, event_csv), run_pap, events=synthetic_events,
        benchmark_mode="market", diagnostic_dims=(), nfv_structured=True,
        postpone_policy="missing_bar_only", st_policy="keep", strata_enabled=False,
        verdict_policy="adj_bmp_main_only", tau0_on_anchor=True,
    )
    result["per_tau"]["tau_axis"] = (
        "τ=0:=event_date当日首个真实bar价格观察日(exp16冻结口径)")
    audit = selection_audit(fixture_selection)
    audit["execution_limit_audit"] = execution_limit_audit(result)
    result["audit"]["study_snapshot"] = {"snapshot_id": 0, "digest": "fixture"}
    result["audit"]["yearend_strength_selection"] = audit
    before_identity = (json.dumps(
        result, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n").encode()
    attach_experiment_identity(result, {
        "exp_id": 16, "family": "yearend_strength", "family_trial": 1,
        "source_type": "llm", "verdict_power": "prescreen",
    })
    restored = copy.deepcopy(result)
    del restored["audit"]["experiment_identity"]
    check("A8 身份写入恰新增audit一键",
          (json.dumps(restored, ensure_ascii=False, indent=2, sort_keys=True,
                      default=str) + "\n").encode() == before_identity, True)
    rendered = report_mod.render(result)
    check("A8 exp16真锚标题", rendered.splitlines()[0],
          "═══ 淘沙 · 事件研究体检报告(exp16 年末相对强势·事件版)═══")
    check("A8 同日价格观察术语", "event_date当日首个真实bar价格观察日" in rendered, True)
    check("A8 执行限制NFV", "exp16 τ0执行限制审计" in rendered
          and "不等于可成交收益或策略证据" in rendered, True)
    check("A8 llm/prescreen水印在场",
          "family=yearend_strength trial=1 source=llm power=prescreen" in rendered, True)
    missing_identity = copy.deepcopy(result)
    del missing_identity["audit"]["experiment_identity"]
    _, error = render_attempt(missing_identity)
    check("A8 删除身份水印fail-closed", "实验身份水印" in error, True)
    check("A8 递归verdict唯一", json.dumps(result, ensure_ascii=False).count('"verdict"'), 1)

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
raise SystemExit(1 if FAIL else 0)
