"""exp10 driver/report/DDL 专项 fixture（零 DB、合成事件研究）。"""
import dataclasses
import datetime as dt
import hashlib
import json
import os
import sys
import tempfile
from collections import namedtuple
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.engine import report as report_mod  # noqa: E402
from taosha.engine import runner as rn  # noqa: E402
from taosha.experiment.pap import canonical_pap_sha256  # noqa: E402
from taosha.harness.make_ashare_fixture import generate, write_csv  # noqa: E402
from taosha.harness.run_ashare_study import synth_pap  # noqa: E402
from taosha.harness.run_volume_drought_study import (  # noqa: E402
    ENGINE_PARAM_KEYS, engine_kwargs_from_pap, events_from_volume_rows, selection_audit,
)
from taosha.reader.synthetic import SyntheticReader  # noqa: E402


FAIL = 0
N = 0
DIGEST = "18d7322c8b4e2e14871a2d037516271892422cb0fa054a8e68697d0f8830aff1"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAP_PATH = os.path.join(ROOT, "taosha", "docs", "volume-drought-break-pap-final-2026-07-29.json")
DDL_PATH = os.path.join(ROOT, "qbase", "sql", "022_volume_drought_reader.sql")


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    FAIL += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


def fails(fn):
    try:
        fn()
        return ""
    except SystemExit as exc:
        return str(exc)


with open(PAP_PATH, "rb") as handle:
    raw = handle.read()
pap = json.loads(raw)

kwargs = engine_kwargs_from_pap(pap)
check("A1 engine_params逐字消费", kwargs,
      {"benchmark_mode": "market", "diagnostic_dims": (), "nfv_structured": True,
       "postpone_policy": "missing_bar_only", "strata_enabled": False,
       "verdict_policy": "adj_bmp_main_only"})
check("A1 键集恰7", len(ENGINE_PARAM_KEYS), 7)
missing = dict(pap, engine_params={k: v for k, v in pap["engine_params"].items()
                                   if k != "postpone_policy"})
extra = dict(pap, engine_params=dict(pap["engine_params"], st_policy="keep"))
check("A1 缺键fail-closed", "postpone_policy" in fails(lambda: engine_kwargs_from_pap(missing)), True)
check("A1 多键fail-closed", "st_policy" in fails(lambda: engine_kwargs_from_pap(extra)), True)

check("A2 文件SHA", hashlib.sha256(raw).hexdigest(), DIGEST)
check("A2 canonical", canonical_pap_sha256(pap), DIGEST)
check("A2 运行时键不进digest", canonical_pap_sha256(dict(pap, _family_trial=9)), DIGEST)

Row = namedtuple("VolumeRow", "ts_code trade_date open close amount snapshot_batch")
start = dt.date(2015, 1, 1)
amounts = [Decimal("100")] * 60 + [Decimal("20")] * 5 + [Decimal("150")]
dates = [start + dt.timedelta(days=i) for i in range(len(amounts))]
cal_index = {day: idx + 1 for idx, day in enumerate(dates)}
rows = [Row("000001.SZ", day, Decimal("10"), Decimal("11"), amount, "batch6")
        for day, amount in zip(dates, amounts)]
events, selection = events_from_volume_rows(iter(rows), cal_index, "fixture")
audit = selection_audit(selection)
check("A3 EventRow单层", (len(events), events[0].event_type_layer), (1, "volume_drought_break"))
check("A3 三恒等式", (audit["armed_terminal_identity_ok"],
                       audit["breakout_terminal_identity_ok"], audit["event_period_identity_ok"]),
      (True, True, True))
check("A3 小样本不冒充参考", audit["reference_reconciliation"]["exact_match"], False)
forbidden = {"car", "return", "verdict", "significance"}
check("A3 非收阳审计零收益判决字段",
      forbidden.intersection(audit["breakout_terminal_audit"]), set())

with open(DDL_PATH, encoding="utf-8") as handle:
    ddl = handle.read()
check("A4 DDL视图对", all(name in ddl for name in
      ("explore_reader_volume_drought AS", "explore_reader_volume_drought_snap AS")), True)
check("A4 holdout与排北焊死", ("trade_date < DATE '2024-07-01'" in ddl,
                                "ts_code !~ '\\.BJ$'" in ddl), (True, True))
check("A4 最小列面不含收益加工", "adj_factor" in ddl or "RETURN" in ddl.upper(), False)


def render_attempt(result):
    try:
        return report_mod.render(result), ""
    except SystemExit as exc:
        return "", str(exc)


_, error = render_attempt({"audit": {"volume_drought_selection": {}}})
check("A5 缺快照锚fail-closed", "volume_drought_selection" in error, True)

with tempfile.TemporaryDirectory() as td:
    prices, event_csv, meta = (os.path.join(td, name) for name in ("p.csv", "e.csv", "m.json"))
    write_csv(generate(), prices, event_csv, meta)
    synthetic_pap = dict(synth_pap(), _family_trial=1, bias_statement=pap["bias_statement"])
    base_events = list(SyntheticReader(prices, event_csv).events())
    synthetic_events = [dataclasses.replace(event, event_type_layer="volume_drought_break")
                        for event in base_events]
    result = rn.run_study(SyntheticReader(prices, event_csv), synthetic_pap,
                          events=synthetic_events, benchmark_mode="market",
                          diagnostic_dims=(), nfv_structured=True,
                          postpone_policy="missing_bar_only", strata_enabled=False,
                          verdict_policy="adj_bmp_main_only")
    result["audit"]["study_snapshot"] = {"snapshot_id": 0, "digest": "fixture"}
    result["audit"]["volume_drought_selection"] = audit
    rendered = report_mod.render(result)
    check("A5 exp10真锚标题", rendered.splitlines()[0],
          "═══ 淘沙 · 事件研究体检报告(exp10 成交额干涸后首次放量收阳·事件版)═══")
    check("A5 价格观察日术语", "事件后首个有真实bar的价格观察日" in rendered, True)
    check("A5 exp10逐日段零首个可交易日", "首个可交易日" in rendered, False)
    check("A5 拒绝组NFV且无收益展示", "仅报告事件几何计数,不得读取或展示其后收益" in rendered, True)

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
