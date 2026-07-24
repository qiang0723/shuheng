"""exp11 high_pullback driver+report 分支专项验收(冻结令 2026-07-24 五;零 DB,合成行+仓内冻结件)。

覆盖冻结令三.2 攻击面(适配侧):
  ① engine_params 逐字消费(键集恰 7,缺键/多键 fail-closed;6 参数逐字透传);
  ② events_from_prices(EventRow 单层 high_pullback/event_id 形态/确定性双跑/日历外 fail-closed);
  ③ selection_audit(三恒等式/MA20 审计 NFV/42,719 参考对账非硬断言);
  ④ digest 不变量(文件 SHA==canonical==令 digest/_family_trial 不进 digest/改实质键必变);
  ⑤ report high_pullback_selection 分支(缺锚/present-but-None fail-closed;真锚标题;
    **「价格观察日」术语渲染在场+exp11 漏斗段零『可交易』**;他 exp 标题零命中;exp8 分支回归探针)。
用法: python taosha/harness/verify_high_pullback_adapter.py
"""
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

from taosha.engine import report as report_mod                            # noqa: E402
from taosha.engine import runner as rn                                    # noqa: E402
from taosha.experiment.pap import canonical_pap_sha256                    # noqa: E402
from taosha.harness.make_ashare_fixture import generate, write_csv        # noqa: E402
from taosha.harness.run_ashare_study import synth_pap                     # noqa: E402
from taosha.harness.run_high_pullback_study import (                      # noqa: E402
    ENGINE_PARAM_KEYS, engine_kwargs_from_pap, events_from_prices, selection_audit)
from taosha.reader.synthetic import SyntheticReader                       # noqa: E402

FAIL = 0
N = 0

ORDER_DIGEST = "eaa54b3da8ede7baf27e3a387454ac0611be999ba351c376b73eadde5aacb6fc"
PAP_FINAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "docs", "high-pullback-pap-final-2026-07-24.json")


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    if not ok:
        FAIL += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


with open(PAP_FINAL, "rb") as fh:
    _RAW = fh.read()
pap = json.loads(_RAW)

# ── ① engine_params 逐字消费(fail-closed)────────────────────────────────────────
kw = engine_kwargs_from_pap(pap)
check("①冻结件 6 参数逐字透传(note 校验在场不传引擎)",
      kw, {"benchmark_mode": "market", "strata_enabled": False,
           "verdict_policy": "adj_bmp_main_only", "nfv_structured": True,
           "postpone_policy": "missing_bar_only", "diagnostic_dims": ()})
check("①键集恰 7(冻结件)", sorted(ENGINE_PARAM_KEYS),
      sorted(["benchmark_mode", "diagnostic_dims", "nfv_structured", "note",
              "postpone_policy", "strata_enabled", "verdict_policy"]))


def _try(fn):
    try:
        fn()
        return None
    except SystemExit as e:
        return str(e)


ep_missing = dict(pap, engine_params={k: v for k, v in pap["engine_params"].items()
                                      if k != "postpone_policy"})
err = _try(lambda: engine_kwargs_from_pap(ep_missing))
check("①缺键 fail-closed", err is not None and "postpone_policy" in err, True)
ep_extra = dict(pap, engine_params=dict(pap["engine_params"], st_policy="keep"))
err = _try(lambda: engine_kwargs_from_pap(ep_extra))
check("①多键 fail-closed", err is not None and "st_policy" in err, True)

# ── ② events_from_prices(合成两票域)───────────────────────────────────────────
Row = namedtuple("Row", "ts_code trade_date close board is_st")
START = dt.date(2015, 1, 5)
DATES = [START + dt.timedelta(days=k) for k in range(252)]
CAL_INDEX = {d: k + 1 for k, d in enumerate(DATES)}
LAST_RANK = 252 + 100


def _mk(ts, closes):
    return [Row(ts, DATES[k], Decimal(str(c)), "main", False)
            for k, c in enumerate(closes)]


ROWS = _mk("000001.SZ", [100] * 250 + [200, 194]) + _mk("000002.SZ", [100] * 252)
ev, sel = events_from_prices(iter(ROWS), CAL_INDEX, LAST_RANK, batch="fixture")
check("②事件=1(甲票 EVENT/乙票平史零锚)", (len(ev), sel["counters"]["final_events"]), (1, 1))
check("②EventRow 形态(单层 high_pullback/event_id/first_ann_date)",
      (ev[0].event_type_layer, ev[0].event_id, ev[0].first_ann_date, ev[0].snapshot_batch),
      ("high_pullback", f"000001.SZ:{DATES[251].isoformat().replace('-', '')}",
       DATES[251], "fixture"))
r1 = [e.event_id for e in events_from_prices(iter(ROWS), CAL_INDEX, LAST_RANK, batch="b")[0]]
r2 = [e.event_id for e in events_from_prices(iter(ROWS), CAL_INDEX, LAST_RANK, batch="b")[0]]
check("②确定性双跑", r1 == r2, True)
BAD = [Row("000003.SZ", dt.date(2030, 1, 1), Decimal("100"), "main", False)]
err = _try(lambda: events_from_prices(iter(BAD), CAL_INDEX, LAST_RANK, batch="b"))
check("②日历外 bar fail-closed", err is not None and "日历轴" in err, True)

# ── ③ selection_audit ───────────────────────────────────────────────────────────
aud = selection_audit(sel)
check("③三恒等式(newhigh/outcome/events)",
      (aud["newhigh_identity_ok"], aud["funnel_identity_ok"], aud["events_identity_ok"]),
      (True, True, True))
check("③MA20 审计 NFV(入带1/过线1/比例1.0)",
      (aud["ma20_filter_audit"]["not_for_verdict"], aud["ma20_filter_audit"]["in_band"],
       aud["ma20_filter_audit"]["pass_ratio"]), (True, 1, 1.0))
check("③42,719 参考对账(非硬断言字样+delta)",
      (aud["reference_reconciliation"]["reference_final_events"],
       aud["reference_reconciliation"]["got_final_events"],
       "非硬断言" in aud["reference_reconciliation"]["summary"]), (42719, 1, True))
check("③唯一性逐条槽在场", sorted(aud["itemized_rejects"]),
      ["event_key_duplicate_fail_closed"])

# ── ④ digest 不变量(driver fail-fast 依赖)──────────────────────────────────────
check("④文件 SHA256==令绑定 digest", hashlib.sha256(_RAW).hexdigest(), ORDER_DIGEST)
check("④canonical==令绑定 digest", canonical_pap_sha256(pap), ORDER_DIGEST)
check("④_family_trial 运行时键不进 digest",
      canonical_pap_sha256(dict(pap, _family_trial=1)), ORDER_DIGEST)
check("④改实质键 digest 必变",
      canonical_pap_sha256(dict(pap, sample_gate=31)) == ORDER_DIGEST, False)

# ── ⑤ report high_pullback_selection 分支(合成域全流水线)────────────────────────
def _try_render(res):
    try:
        return report_mod.render(res), None
    except SystemExit as e:
        return None, str(e)


_, err = _try_render({"audit": {"high_pullback_selection": {}, "benchmark_mode": "market"}})
check("⑤缺锚 fail-closed(SystemExit,禁回退合成标题)",
      err is not None and "high_pullback_selection" in err, True)
_, err = _try_render({"audit": {"high_pullback_selection": {},
                                "study_snapshot": {"snapshot_id": None, "digest": None},
                                "benchmark_mode": "market"}})
check("⑤present-but-None 同 fail-closed", err is not None and "high_pullback_selection" in err, True)

with tempfile.TemporaryDirectory() as td:
    p, e, m = (os.path.join(td, x) for x in ("p.csv", "e.csv", "m.json"))
    write_csv(generate(), p, e, m)
    pap11 = dict(synth_pap(), _family_trial=1, bias_statement=pap["bias_statement"])
    base_events = list(SyntheticReader(p, e).events())
    ev11 = [dataclasses.replace(x, event_type_layer="high_pullback") for x in base_events]
    res11 = rn.run_study(SyntheticReader(p, e), pap11, benchmark_mode="market",
                         events=ev11, strata_enabled=False,
                         verdict_policy="adj_bmp_main_only", nfv_structured=True,
                         postpone_policy="missing_bar_only", diagnostic_dims=())
    res11["audit"]["study_snapshot"] = {"snapshot_id": 0, "digest": "synthetic-fixture"}
    res11["audit"]["high_pullback_selection"] = selection_audit(sel)
    rendered = report_mod.render(res11)
    check("⑤真锚→exp11 专属标题",
          rendered.splitlines()[0], "═══ 淘沙 · 事件研究体检报告(exp11 250日新高小幅回落·事件版)═══")
    check("⑤快照行直读真实锚", "StudySnapshot=0 digest=synthetic-fixture" in rendered, True)
    check("⑤exp8/exp12/exp13/exp20 标题零命中",
          ("exp8 一字涨停开板" in rendered, "exp12 ST/风险警示" in rendered,
           "exp13 一字跌停开板" in rendered, "exp20 业绩预告修正" in rendered),
          (False, False, False, False))
    # 「价格观察日」术语渲染(人终版收口令 2026-07-24)+ exp11 漏斗段零『可交易』
    check("⑤『价格观察日』术语渲染在场", "事件后首个有真实bar的价格观察日" in rendered, True)
    check("⑤一字板审计句渲染在场(人令原文)",
          "τ0一字板事件仅为价格观察,不得表述为可执行策略证据" in rendered, True)
    sec = [ln for ln in rendered.splitlines()
           if ln.startswith("【exp11 事件生成漏斗") or ln.startswith("  τ0 口径")
           or ln.startswith("  MA20 筛选比例") or ln.startswith("  期外剔除")
           or ln.startswith("  阶段结局五分") or ln.startswith("  输入行")
           or ln.startswith("  参考对账")]
    check("⑤exp11 漏斗段在场且零『可交易』",
          (len(sec) >= 6, any("可交易" in ln for ln in sec)), (True, False))
    # exp8 分支回归探针:同一 result 改挂 limit_open_selection 键 → exp8 标题不变(分支互斥)
    res8 = dict(res11)
    res8["audit"] = dict(res11["audit"])
    del res8["audit"]["high_pullback_selection"]
    res8["audit"]["limit_open_selection"] = {"counters": {}}
    rendered8 = report_mod.render(res8)
    check("⑤exp8 分支自身行为不变(真锚标题在位)",
          rendered8.splitlines()[0], "═══ 淘沙 · 事件研究体检报告(exp8 一字涨停开板·事件版)═══")
    check("⑤exp8 渲染 exp11 标题/漏斗段零命中",
          ("exp11 250日新高小幅回落" in rendered8, "【exp11 事件生成漏斗" in rendered8),
          (False, False))

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
