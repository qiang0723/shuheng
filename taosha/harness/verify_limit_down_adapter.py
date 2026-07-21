"""exp13 limit_down_open driver+report 分支专项验收(冻结令 2026-07-21;零 DB,合成行+仓内冻结件)。

验五面:
  ① engine_kwargs_from_pap = 逐字消费冻结 PAP(真实冻结文件,digest 583c4c94…0c42),
    缺键/多键 fail-closed;st 居首诊断轴(令三.2);引擎白名单与冻结 PAP axes 逐项一致;
  ② events_from_prices 映射正确性(EventRow 字段/event_id 格式/层键二值/listing fail-closed/
    留痕透传/跨票分组/B 口径开关/确定性双跑);
  ③ selection_audit 块(七档漏斗恒等/hijack 审计分母/ST 轴恒等/B 对照差异/逐条槽位);
  ④ driver 依赖的 digest 不变量(冻结文件 canonical==令绑定 digest;_family_trial 运行时键
    不进 digest;改实质键必变);
  ⑤ report limit_down_selection 分支(合成域全流水线):缺锚/present-but-None fail-closed;
    真锚→exp13 专属标题+快照行;exp8 标题零命中;exp8 分支自身行为不变(回归探针)。
用法: python taosha/harness/verify_limit_down_adapter.py
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
from taosha.experiment.pap import canonical_pap_sha256                    # noqa: E402
from taosha.harness.make_ashare_fixture import generate, write_csv        # noqa: E402
from taosha.harness.run_ashare_study import synth_pap                     # noqa: E402
from taosha.harness.run_limit_down_study import (                         # noqa: E402
    ENGINE_PARAM_KEYS, engine_kwargs_from_pap, events_from_prices, selection_audit)
from taosha.reader.contract import PriceRow                               # noqa: E402
from taosha.reader.synthetic import SyntheticReader                       # noqa: E402

FAIL = 0
N = 0

ORDER_DIGEST = "583c4c946078006aef6061cdc405d7255d16a7bfd9d36bdb3c3793f57f0e0c42"
PAP_FINAL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "docs", "limit-down-open-pap-final-2026-07-21.json")


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
check("①kwargs 全集(st 居首=令三.2)", kw, {
    "benchmark_mode": "market", "strata_enabled": False, "st_mode": "event_day",
    "st_policy": "keep", "verdict_policy": "adj_bmp_main_only", "nfv_structured": True,
    "postpone_policy": "unified", "diagnostic_dims": ("st", "listing_age")})
check("①note 不进引擎参数", "note" in kw, False)

bad = dict(pap)
bad["engine_params"] = {k: v for k, v in pap["engine_params"].items() if k != "st_policy"}
try:
    engine_kwargs_from_pap(bad)
    check("①缺键 fail-closed", "放行", "SystemExit")
except SystemExit as e:
    check("①缺键 fail-closed", "st_policy" in str(e), True)

bad2 = dict(pap)
bad2["engine_params"] = dict(pap["engine_params"], runtime_free_choice=1)
try:
    engine_kwargs_from_pap(bad2)
    check("①多键 fail-closed", "放行", "SystemExit")
except SystemExit as e:
    check("①多键 fail-closed", "runtime_free_choice" in str(e), True)

check("①引擎白名单==冻结 PAP axes 逐项一致(st)",
      list(rn._DIAG_DIM_SPECS["st"]["layers"]),
      pap["diagnostic_dimensions"]["axes"]["st"])
check("①引擎白名单==冻结 PAP axes 逐项一致(listing_age)",
      list(rn._DIAG_DIM_SPECS["listing_age"]["layers"]),
      pap["diagnostic_dimensions"]["axes"]["listing_age"])

# ── ② events_from_prices(合成 PriceRow)────────────────────────────────────
def P(ts, d, lim, olim, board="main", is_st=False):
    return PriceRow(ts_code=ts, trade_date=dt.date.fromisoformat(d), close=10.0,
                    is_suspended=False, limit_status=lim, board=board,
                    is_st=is_st, industry="X", open=10.0, open_limit_status=olim)


ROWS = [
    # A票: 2日一字跌停链 → 开板(none) → 事件 2023-01-06;行序 1-3 → recent_listing
    P("000001.SZ", "2023-01-04", "one_word", "open_at_down_limit"),
    P("000001.SZ", "2023-01-05", "one_word", "open_at_down_limit"),
    P("000001.SZ", "2023-01-06", "none", "none"),
    # B票: 同构链但 listing 缺失 → fail-closed 零事件
    P("600000.SH", "2023-03-01", "one_word", "open_at_down_limit"),
    P("600000.SH", "2023-03-02", "one_word", "open_at_down_limit"),
    P("600000.SH", "2023-03-03", "none", "none"),
    # C票: 链后反向一字涨停 → hijack 排除
    P("600100.SH", "2023-05-08", "one_word", "open_at_down_limit"),
    P("600100.SH", "2023-05-09", "one_word", "open_at_down_limit"),
    P("600100.SH", "2023-05-10", "one_word", "open_at_up_limit"),
    P("600100.SH", "2023-05-11", "none", "none"),
]
LISTING = {"000001.SZ": {"list_date": dt.date(2023, 1, 4), "delist_date": None},
           "600100.SH": {"list_date": dt.date(2023, 5, 8), "delist_date": None}}

events, sel = events_from_prices(iter(ROWS), LISTING, "study_snapshot:99")
check("②事件数(B票 listing fail-closed/C票 hijack 排除)", len(events), 1)
check("②event_id 格式", events[0].event_id, "000001.SZ:20230106")
check("②first_ann_date", events[0].first_ann_date, dt.date(2023, 1, 6))
check("②层键=recent_listing(行序3≤30)", events[0].event_type_layer, "recent_listing")
check("②snapshot_batch 透传", events[0].snapshot_batch, "study_snapshot:99")
check("②留痕计数(listing 1/hijack 1)",
      (sel["reject_reasons"]["listing_missing_fail_closed"],
       sel["reject_reasons"]["reversal_hijack"]), (1, 1))
check("②counters 跨票求和", sel["counters"]["input_rows"], 10)
check("②cal_index 不传 → b_control=None(零新键)", sel["b_control"], None)

# seasoned 层:链起点行序 31(>30)
LONG = [P("000002.SZ", (dt.date(2023, 1, 2) + dt.timedelta(days=i)).isoformat(),
          "none", "none") for i in range(30)]
LONG += [P("000002.SZ", "2023-02-10", "one_word", "open_at_down_limit"),
         P("000002.SZ", "2023-02-11", "one_word", "open_at_down_limit"),
         P("000002.SZ", "2023-02-12", "none", "none")]
ev2, _ = events_from_prices(iter(LONG), {"000002.SZ": {"list_date": dt.date(2023, 1, 2),
                                                       "delist_date": None}}, "b")
check("②层键=seasoned(行序31>30)", [e.event_type_layer for e in ev2], ["seasoned"])

r1 = [e.event_id for e in events_from_prices(iter(ROWS), LISTING, "b")[0]]
r2 = [e.event_id for e in events_from_prices(iter(ROWS), LISTING, "b")[0]]
check("②确定性双跑", r1 == r2, True)

# B 口径开关(cal_index 全轴连续 → A/B 同构)
CAL = {dt.date(2023, 1, 1) + dt.timedelta(days=i): i for i in range(200)}
ev3, sel3 = events_from_prices(iter(ROWS), LISTING, "b", cal_index=CAL)
check("②B 口径镜像在场且主集不变(日历连续时 A==B 主集)",
      ([e.event_id for e in ev3] == r1, sel3["b_control"]["counters"]["final_main_events"]),
      (True, 1))

# ── ③ selection_audit ───────────────────────────────────────────────────────
aud = selection_audit(sel3)
check("③七档漏斗恒等(3链=hijack1+listing1+主集1)",
      (aud["funnel"]["原始最大链"], aud["funnel"]["identity_ok"],
       aud["funnel"]["reversal_hijack"], aud["funnel"]["listing_anomaly"],
       aud["funnel"]["final_main_events"]), (3, True, 1, 1, 1))
check("③hijack 审计块(分母显式+NFV)",
      (aud["reversal_hijack_audit"]["count"],
       aud["reversal_hijack_audit"]["share"]["denominator_surviving_candidates"],
       aud["reversal_hijack_audit"]["not_for_verdict"]), (1, 2, True))
check("③ST 轴恒等+NFV", (aud["st_axis"]["identity_ok"], aud["st_axis"]["not_for_verdict"]),
      (True, True))
check("③B 对照块差异全零(日历连续)+NFV",
      (aud["b_axis_control"]["vs_a_main_events"]["n_only_a"],
       aud["b_axis_control"]["vs_a_main_events"]["n_only_b"],
       aud["b_axis_control"]["not_for_verdict"]), (0, 0, True))
check("③逐条槽五类在场(dup/listing三类/hijack)",
      sorted(aud["itemized_rejects"]), sorted([
          "duplicate_event_date_mapping", "listing_missing_fail_closed",
          "pre_listing_bar_fail_closed", "listing_window_anomaly_fail_closed",
          "reversal_hijack"]))
check("③链长/逐年/层分布", (aud["chain_len_dist"], aud["events_yearly"], aud["layer_counts"]),
      ({"2": 1}, {"2023": 1}, {"recent_listing": 1, "seasoned": 0}))

# ── ④ digest 不变量(driver fail-fast 依赖)─────────────────────────────────
with open(PAP_FINAL, "rb") as fh:
    raw = fh.read()
check("④文件 SHA256==令绑定 digest", hashlib.sha256(raw).hexdigest(), ORDER_DIGEST)
check("④canonical==令绑定 digest", canonical_pap_sha256(pap), ORDER_DIGEST)
pap_rt = dict(pap, _family_trial=1)
check("④_family_trial 运行时键不进 digest", canonical_pap_sha256(pap_rt), ORDER_DIGEST)
check("④改实质键 digest 必变",
      canonical_pap_sha256(dict(pap, sample_gate=31)) == ORDER_DIGEST, False)

# ── ⑤ report limit_down_selection 分支(合成域全流水线)──────────────────────
def _try_render(res):
    try:
        return report_mod.render(res), None
    except SystemExit as e:
        return None, str(e)


_, err = _try_render({"audit": {"limit_down_selection": {}, "benchmark_mode": "market"}})
check("⑤缺锚 fail-closed(SystemExit,禁回退合成标题)",
      err is not None and "limit_down_selection" in err, True)
_, err = _try_render({"audit": {"limit_down_selection": {},
                                "study_snapshot": {"snapshot_id": None, "digest": None},
                                "benchmark_mode": "market"}})
check("⑤present-but-None 同 fail-closed", err is not None and "limit_down_selection" in err, True)

with tempfile.TemporaryDirectory() as td:
    p, e, m = (os.path.join(td, x) for x in ("p.csv", "e.csv", "m.json"))
    write_csv(generate(), p, e, m)
    _DIAG_AXES = {"axes": {"st": ["ST", "non_ST"], "listing_age": ["recent_listing", "seasoned"]}}
    pap13 = dict(synth_pap(), _family_trial=1, bias_statement=pap["bias_statement"],
                 diagnostic_dimensions=_DIAG_AXES)
    base_events = list(SyntheticReader(p, e).events())
    half = len(base_events) // 2
    ev_split = ([dataclasses.replace(ev, event_type_layer="recent_listing")
                 for ev in base_events[:half]]
                + [dataclasses.replace(ev, event_type_layer="seasoned")
                   for ev in base_events[half:]])
    res13 = rn.run_study(SyntheticReader(p, e), pap13, benchmark_mode="market",
                         events=ev_split, strata_enabled=False, st_mode="event_day",
                         st_policy="keep", verdict_policy="adj_bmp_main_only",
                         nfv_structured=True, postpone_policy="unified",
                         diagnostic_dims=("st", "listing_age"))
    res13["audit"]["study_snapshot"] = {"snapshot_id": 0, "digest": "synthetic-fixture"}
    res13["audit"]["limit_down_selection"] = selection_audit(sel3)
    rendered = report_mod.render(res13)
    check("⑤真锚→exp13 专属标题",
          rendered.splitlines()[0], "═══ 淘沙 · 事件研究体检报告(exp13 一字跌停开板·事件版)═══")
    check("⑤快照行直读真实锚", "StudySnapshot=0 digest=synthetic-fixture" in rendered, True)
    check("⑤exp8/exp20 标题零命中",
          ("exp8 一字涨停开板" in rendered, "exp20 业绩预告修正" in rendered), (False, False))
    # exp8 分支回归探针:同一 result 改挂 limit_open_selection 键 → exp8 标题不变(分支互斥)
    res8 = dict(res13)
    res8["audit"] = dict(res13["audit"])
    del res8["audit"]["limit_down_selection"]
    res8["audit"]["limit_open_selection"] = {"counters": {}}
    rendered8 = report_mod.render(res8)
    check("⑤exp8 分支自身行为不变(真锚标题在位)",
          rendered8.splitlines()[0], "═══ 淘沙 · 事件研究体检报告(exp8 一字涨停开板·事件版)═══")
    check("⑤exp8 渲染 exp13 标题零命中", "exp13 一字跌停开板" in rendered8, False)

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
