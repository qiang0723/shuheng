"""exp12 st_removal driver+engine+report 分支专项验收(冻结令 2026-07-23;零 DB,合成行+仓内冻结件)。

验七面(令三节攻击 fixture 清单映射):
  ① engine_kwargs_from_pap = 逐字消费冻结 PAP(真实冻结文件,digest 62a387a2…4353),
    缺键/多键/postpone 篡改 fail-closed;st_mode/st_policy=driver 定值(头注论证);
  ② driver 依赖的 digest 不变量(冻结文件 canonical==令绑定 digest;_family_trial 运行时键
    不进 digest;改实质键必变);
  ③ events_from_namechange 映射正确性(EventRow 字段/event_id 格式/单层键/跨票分组/
    确定性双跑/漏斗留痕透传);
  ④ 引擎 postpone_policy='missing_bar_only'(令:缺bar顺延1/5/6日、一字涨跌停不顺延):
    缺bar 1 日顺延/5 日保留/6 日剔 postpone;一字涨停·一字跌停有真实 bar 即 τ0(τ0一字板
    留痕注记);unified 同构零回归探针(一字板照旧阻塞);legality(runner+cleaning 白名单
    收 missing_bar_only、bogus 拒、缺 axis 拒);ST 锚日 keep 不剔(driver 定值行为面);
  ⑤ report st_removal_selection 分支(合成域全流水线):缺锚/present-but-None fail-closed;
    缺 execution_limit_audit fail-closed;真锚→exp12 专属标题+漏斗段+一字板执行限制段;
    exp8/exp13/exp20 标题零命中;exp13 分支自身行为不变(回归探针);
  ⑥ execution_limit_audit_from_result(τ0 行 one_word 计数/分母/比例;空 result 安全);
  ⑦ batch 7 参考数对账块(非硬断言;delta 结构+血缘注记在场)。
用法: python taosha/harness/verify_st_removal_adapter.py
"""
import dataclasses
import datetime as dt
import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.engine import report as report_mod                            # noqa: E402
from taosha.engine import runner as rn                                    # noqa: E402
from taosha.engine.cleaning import clean_event                            # noqa: E402
from taosha.experiment.pap import canonical_pap_sha256                    # noqa: E402
from taosha.harness.make_ashare_fixture import generate, write_csv        # noqa: E402
from taosha.harness.run_ashare_study import synth_pap                     # noqa: E402
from taosha.harness.run_st_removal_study import (                         # noqa: E402
    ENGINE_PARAM_KEYS, engine_kwargs_from_pap, events_from_namechange,
    execution_limit_audit_from_result, selection_audit)
from taosha.reader.contract import PriceRow                               # noqa: E402
from taosha.reader.synthetic import SyntheticReader                       # noqa: E402

FAIL = 0
N = 0

ORDER_DIGEST = "62a387a290707985f2d50ee490d1ac83bccc6e6dc2e6d4241ced12e6791d4353"
PAP_FINAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "docs", "st-removal-pap-final-2026-07-23.json")


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    if not ok:
        FAIL += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


# ── ① engine_params 逐字消费(真实冻结件)────────────────────────────────────
with open(PAP_FINAL, "rb") as fh:
    pap = json.loads(fh.read())
kw = engine_kwargs_from_pap(pap)
check("①kwargs 全集(postpone=missing_bar_only;st=driver 定值 keep/event_day)", kw, {
    "benchmark_mode": "market", "strata_enabled": False, "st_mode": "event_day",
    "st_policy": "keep", "verdict_policy": "adj_bmp_main_only", "nfv_structured": True,
    "postpone_policy": "missing_bar_only", "diagnostic_dims": ()})
check("①note 不进引擎参数", "note" in kw, False)
check("①冻结件键集==driver 白名单", set(pap["engine_params"]), set(ENGINE_PARAM_KEYS))

bad = dict(pap)
bad["engine_params"] = {k: v for k, v in pap["engine_params"].items() if k != "verdict_policy"}
try:
    engine_kwargs_from_pap(bad)
    check("①缺键 fail-closed", "放行", "SystemExit")
except SystemExit as e:
    check("①缺键 fail-closed", "verdict_policy" in str(e), True)

bad2 = dict(pap)
bad2["engine_params"] = dict(pap["engine_params"], runtime_free_choice=1)
try:
    engine_kwargs_from_pap(bad2)
    check("①多键 fail-closed", "放行", "SystemExit")
except SystemExit as e:
    check("①多键 fail-closed", "runtime_free_choice" in str(e), True)

bad3 = dict(pap)
bad3["engine_params"] = dict(pap["engine_params"], postpone_policy="unified")
try:
    engine_kwargs_from_pap(bad3)
    check("①postpone 篡改 fail-closed(driver 只认冻结值不映射)", "放行", "SystemExit")
except SystemExit as e:
    check("①postpone 篡改 fail-closed(driver 只认冻结值不映射)",
          "missing_bar_only" in str(e), True)

# ── ② digest 不变量(driver fail-fast 依赖)─────────────────────────────────
with open(PAP_FINAL, "rb") as fh:
    raw = fh.read()
check("②文件 SHA256==令绑定 digest", hashlib.sha256(raw).hexdigest(), ORDER_DIGEST)
check("②canonical==令绑定 digest", canonical_pap_sha256(pap), ORDER_DIGEST)
check("②_family_trial 运行时键不进 digest",
      canonical_pap_sha256(dict(pap, _family_trial=1)), ORDER_DIGEST)
check("②改实质键 digest 必变",
      canonical_pap_sha256(dict(pap, sample_gate=31)) == ORDER_DIGEST, False)

# ── ③ events_from_namechange 映射 ───────────────────────────────────────────
def NR(ts, alias, start, ann):
    return {"ts_code": ts, "alias": alias,
            "start_date": dt.date.fromisoformat(start) if start else None,
            "ann_date": dt.date.fromisoformat(ann) if ann else None,
            "snapshot_batch": "batch7"}


NC_ROWS = [
    NR("000001.SZ", "ST丰华", "2012-01-10", "2012-01-06"),
    NR("000001.SZ", "丰华股份", "2015-06-10", "2015-06-08"),
    NR("000002.SZ", "*ST海源", "2012-01-10", "2012-01-06"),   # 摘星:非事件仅报数
    NR("000002.SZ", "ST海源", "2013-05-10", "2013-05-07"),
    NR("600001.SH", "ST丁", "2012-01-10", "2012-01-06"),       # ST→退市(前缀):非事件
    NR("600001.SH", "退市丁", "2015-06-10", "2015-06-08"),
]
events, sel = events_from_namechange(list(NC_ROWS), batch="study_snapshot:99")
check("③事件数(摘星/退市前缀均排除)", len(events), 1)
check("③event_id 格式", events[0].event_id, "000001.SZ:20150608")
check("③first_ann_date=ann 锚", events[0].first_ann_date, dt.date(2015, 6, 8))
check("③单层键", events[0].event_type_layer, "st_removal")
check("③snapshot_batch 透传", events[0].snapshot_batch, "study_snapshot:99")
check("③NFV 计数透传", (sel["counters"]["destar_all"],
                        sel["counters"]["st_to_delist_all"]), (1, 1))
import random                                                             # noqa: E402
shuffled = list(NC_ROWS)
random.Random(7).shuffle(shuffled)
e2, _ = events_from_namechange(shuffled, batch="study_snapshot:99")
check("③行序无关确定性(内部再排序同键)",
      [e.event_id for e in e2], [e.event_id for e in events])

# ── ④ 引擎 missing_bar_only(令:缺bar顺延1/5/6日、一字涨跌停不顺延)──────────
D0 = dt.date(2020, 1, 1)
AXIS = []
_d = D0
while len(AXIS) < 400:
    if _d.weekday() < 5:
        AXIS.append(_d)
    _d += dt.timedelta(days=1)
IDX = {x: i for i, x in enumerate(AXIS)}
T = 300


def prows(skip=(), ow=(), ow_dir="open_at_up_limit", st=True):
    out = []
    for i, x in enumerate(AXIS):
        if i in skip:
            continue
        out.append(PriceRow(ts_code="000001.SZ", trade_date=x, close=10.0, is_suspended=False,
                            limit_status=("one_word" if i in ow else "none"), board="main",
                            is_st=st, industry="x", open=10.0,
                            open_limit_status=(ow_dir if i in ow else "none")))
    return out


@dataclasses.dataclass
class _Ev:
    ts_code: str = "000001.SZ"
    event_id: str = "e1"
    first_ann_date: dt.date = AXIS[T]


MBO = dict(st_policy="keep", postpone_policy="missing_bar_only", axis_dates=AXIS)
ce = clean_event(prows(skip={T + 1}), _Ev(), IDX, **MBO)
check("④缺bar顺延1日", (ce.rejected, ce.tau0_idx, ce.postponed), (False, T + 2, 1))
ce = clean_event(prows(skip=set(range(T + 1, T + 6))), _Ev(), IDX, **MBO)
check("④缺bar顺延5日保留", (ce.rejected, ce.tau0_idx, ce.postponed), (False, T + 6, 5))
ce = clean_event(prows(skip=set(range(T + 1, T + 7))), _Ev(), IDX, **MBO)
check("④缺bar第6日剔 postpone", (ce.rejected, ce.reject_reason), (True, "postpone"))
ce = clean_event(prows(ow={T + 1}, ow_dir="open_at_up_limit"), _Ev(), IDX, **MBO)
check("④一字涨停不顺延(τ0=一字日,postponed=0)",
      (ce.rejected, ce.tau0_idx, ce.postponed), (False, T + 1, 0))
check("④τ0一字板留痕注记", any("τ0日一字板" in n for n in ce.notes), True)
ce = clean_event(prows(ow={T + 1}, ow_dir="open_at_down_limit"), _Ev(), IDX, **MBO)
check("④一字跌停不顺延(τ0=一字日,postponed=0)",
      (ce.rejected, ce.tau0_idx, ce.postponed), (False, T + 1, 0))
ce = clean_event(prows(skip={T + 1, T + 2}, ow={T + 3}), _Ev(), IDX, **MBO)
check("④混合:缺bar2日+一字日=τ0(仅缺bar计入顺延)",
      (ce.rejected, ce.tau0_idx, ce.postponed), (False, T + 3, 2))
check("④ST 锚日 keep 不剔(driver 定值行为面;事件本体=ST摘帽)",
      (ce.is_st, ce.rejected), (True, False))
# unified 零回归探针:同构一字日照旧阻塞顺延
ce_u = clean_event(prows(ow={T + 1}), _Ev(), IDX, st_policy="keep",
                   postpone_policy="unified")
check("④unified 零回归(一字板照旧阻塞顺延)", (ce_u.tau0_idx, ce_u.postponed), (T + 2, 1))
# legality
try:
    clean_event(prows(), _Ev(), IDX, postpone_policy="missing_bar_only")
    check("④缺 axis_dates 拒", "放行", "ValueError")
except ValueError:
    check("④缺 axis_dates 拒", "ValueError", "ValueError")
try:
    clean_event(prows(), _Ev(), IDX, postpone_policy="bogus")
    check("④bogus 值拒", "放行", "ValueError")
except ValueError as e:
    check("④bogus 值拒", "missing_bar_only" in str(e), True)

# ── ⑤ report st_removal_selection 分支(合成域全流水线)──────────────────────
def _try_render(res):
    try:
        return report_mod.render(res), None
    except SystemExit as e:
        return None, str(e)


_, err = _try_render({"audit": {"st_removal_selection": {}, "benchmark_mode": "market"}})
check("⑤缺锚 fail-closed(SystemExit,禁回退合成标题)",
      err is not None and "st_removal_selection" in err, True)
_, err = _try_render({"audit": {"st_removal_selection": {},
                                "study_snapshot": {"snapshot_id": None, "digest": None},
                                "benchmark_mode": "market"}})
check("⑤present-but-None 同 fail-closed", err is not None and "st_removal_selection" in err, True)

with tempfile.TemporaryDirectory() as td:
    p, e, m = (os.path.join(td, x) for x in ("p.csv", "e.csv", "m.json"))
    write_csv(generate(), p, e, m)
    pap12 = dict(synth_pap(), _family_trial=1, bias_statement=pap["bias_statement"])
    base_events = list(SyntheticReader(p, e).events())
    ev12 = [dataclasses.replace(ev, event_type_layer="st_removal") for ev in base_events]
    res12 = rn.run_study(SyntheticReader(p, e), pap12, benchmark_mode="market",
                         events=ev12, strata_enabled=False, st_mode="event_day",
                         st_policy="keep", verdict_policy="adj_bmp_main_only",
                         nfv_structured=True, postpone_policy="missing_bar_only",
                         diagnostic_dims=())
    aud12 = selection_audit(sel)
    # ⑥ execution_limit_audit(真实 run_study result 消费口)
    ela = execution_limit_audit_from_result(res12)
    check("⑥ela 结构(NFV+计数+分母)",
          (ela["not_for_verdict"], ela["denominator_n_valid"] == res12["n_valid"],
           isinstance(ela["tau0_one_word_n"], int)), (True, True, True))
    check("⑥空 result 安全", execution_limit_audit_from_result({})["ratio"], None)
    res12["audit"]["study_snapshot"] = {"snapshot_id": 0, "digest": "synthetic-fixture"}
    # 缺 execution_limit_audit → fail-closed(强制报告项)
    res12["audit"]["st_removal_selection"] = dict(aud12)
    _, err = _try_render(res12)
    check("⑤缺 execution_limit_audit fail-closed", err is not None and "execution_limit" in err,
          True)
    res12["audit"]["st_removal_selection"]["execution_limit_audit"] = ela
    rendered = report_mod.render(res12)
    check("⑤真锚→exp12 专属标题", rendered.splitlines()[0],
          "═══ 淘沙 · 事件研究体检报告(exp12 ST/风险警示完整撤销·事件版)═══")
    check("⑤快照行直读真实锚", "StudySnapshot=0 digest=synthetic-fixture" in rendered, True)
    check("⑤漏斗段+NFV 报数段在场",
          ("exp12 事件生成漏斗" in rendered, "摘星未摘帽全史=1" in rendered), (True, True))
    check("⑤一字板执行限制段在场(NFV+口径句)",
          ("一字板执行限制(execution_limit_audit" in rendered,
           "不得表述为可成交策略证据" in rendered), (True, True))
    check("⑤batch7 参考数对账行在场(非硬断言)", "641 仅对账参考非硬断言" in rendered
          or "参考数非硬断言" in rendered, True)
    check("⑤exp8/exp13/exp20 标题零命中",
          ("exp8 一字涨停开板" in rendered, "exp13 一字跌停开板" in rendered,
           "exp20 业绩预告修正" in rendered), (False, False, False))
    # exp13 分支回归探针:同一 result 改挂 limit_down_selection 键 → exp13 标题不变(分支互斥)
    res13 = dict(res12)
    res13["audit"] = dict(res12["audit"])
    del res13["audit"]["st_removal_selection"]
    res13["audit"]["limit_down_selection"] = {"counters": {}}
    rendered13 = report_mod.render(res13)
    check("⑤exp13 分支自身行为不变(真锚标题在位)", rendered13.splitlines()[0],
          "═══ 淘沙 · 事件研究体检报告(exp13 一字跌停开板·事件版)═══")
    check("⑤exp13 渲染 exp12 标题/漏斗段零命中",
          ("ST/风险警示完整撤销" in rendered13, "exp12 事件生成漏斗" in rendered13),
          (False, False))

# ── ⑦ batch 7 参考数对账块(非硬断言;结构面)─────────────────────────────────
recon = aud12["reference_reconciliation"]
check("⑦delta 结构 11 档全在场", len(recon["layer_deltas"]), 11)
check("⑦参考=641/非硬断言注记", (recon["reference"]["final_events"],
                                 "非硬断言" in recon["summary"]), (641, True))

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
