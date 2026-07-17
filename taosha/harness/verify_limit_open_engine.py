"""exp8 回修单元 engine 适配自检(人令 2026-07-17 深夜二;零 DB,合成域)。
必验覆盖:①T+1 顺延 1/5/6 日边界(一字/一字+停牌混合;T/T+1 纯停牌=item7 'suspension' 剔除
如实验证)②st_policy='reject'/'keep' 两态+非法值拒 ③辅助方法反向不得改变 adj_bmp_main_only
判决(_verdict 两策略可区分用例)④NOT_FOR_VERDICT 结构化(全 result 扫描:唯一 verdict 键=顶层)
⑤默认参数路径结构零回归(不加键、双跑相等;逐字节 sha 硬证=合成 e2e 3116ba9b 随件另跑)。
用法: python taosha/harness/verify_limit_open_engine.py
"""
import datetime as dt
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.engine import runner as rn                       # noqa: E402
from taosha.engine import report as report_mod               # noqa: E402
from taosha.engine.cleaning import MAX_POSTPONE, clean_event  # noqa: E402
from taosha.harness.make_ashare_fixture import generate, write_csv  # noqa: E402
from taosha.harness.run_ashare_study import synth_pap        # noqa: E402
from taosha.reader.contract import EventRow, PriceRow        # noqa: E402
from taosha.reader.synthetic import SyntheticReader          # noqa: E402

FAIL = 0
N = 0


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    if not ok:
        FAIL += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


# ── 证①② 公共台架:320 交易日轴,事件日 T=idx260(估计窗 [T-250,T-91] 完整)─────────
def _biz_days(start, n):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


_DS = _biz_days(dt.date(2020, 1, 2), 320)
_T = 260
_DI = {d: i for i, d in enumerate(_DS)}
_EV = EventRow(ts_code="A", event_id="A:e1", first_ann_date=_DS[_T],
               event_type_layer="预喜", snapshot_batch="S")


def _mk(i, one_word=False, is_st=False):
    return PriceRow("A", _DS[i], 10.0, False, ("one_word" if one_word else "none"),
                    "main", is_st, "I")


def _rows(one_word_idx=(), missing_idx=(), st_event_day=False):
    """全轴 320 行,one_word_idx 置一字、missing_idx 缺行(=停牌)、st_event_day 置事件日行 is_st。"""
    out = []
    for i in range(320):
        if i in missing_idx:
            continue
        out.append(_mk(i, one_word=(i in one_word_idx), is_st=(st_event_day and i == _T)))
    return out


# ── 证①:T+1 顺延 1/5/6 日边界(必验第 1 项)──────────────────────────────────────
check("MAX_POSTPONE 实物=5(冻结口径,边界基准)", MAX_POSTPONE, 5)
c = clean_event(_rows(one_word_idx={_T + 1}), _EV, _DI)
check("①顺延1日(T+1一字):留,τ0=T+2", (c.rejected, c.tau0_idx, c.postponed), (False, _T + 2, 1))
c = clean_event(_rows(one_word_idx=set(range(_T + 1, _T + 6))), _EV, _DI)
check("①顺延5日(T+1..T+5一字)=上限:留,τ0=T+6", (c.rejected, c.tau0_idx, c.postponed), (False, _T + 6, 5))
c = clean_event(_rows(one_word_idx=set(range(_T + 1, _T + 7))), _EV, _DI)
check("①顺延6日(T+1..T+6一字)=超限:剔postpone", (c.rejected, c.reject_reason), (True, "postpone"))
c = clean_event(_rows(one_word_idx={_T + 1}, missing_idx=set(range(_T + 2, _T + 6))), _EV, _DI)
check("①混合:一字1+停牌缺行4=顺延5:留,τ0=T+6", (c.rejected, c.tau0_idx, c.postponed), (False, _T + 6, 5))
c = clean_event(_rows(one_word_idx={_T + 1}, missing_idx=set(range(_T + 2, _T + 7))), _EV, _DI)
check("①混合:一字1+停牌缺行5=顺延6:剔postpone", (c.rejected, c.reject_reason), (True, "postpone"))
c = clean_event(_rows(missing_idx={_T + 1}), _EV, _DI)
check("①T+1纯停牌=item7先剔suspension(不进顺延;实物如实验证)",
      (c.rejected, c.reject_reason), (True, "suspension"))

# ── 证②:st_policy 两态 + 非法值拒(必验第 2 项;C2 乙案)────────────────────────────
c = clean_event(_rows(st_event_day=True), _EV, _DI)
check("②默认(不传)=reject:ST剔除零回归", (c.rejected, c.reject_reason, c.is_st), (True, "st", True))
c = clean_event(_rows(st_event_day=True), _EV, _DI, st_policy="reject")
check("②st_policy='reject':ST剔除", (c.rejected, c.reject_reason), (True, "st"))
c = clean_event(_rows(st_event_day=True), _EV, _DI, st_policy="keep")
check("②st_policy='keep':ST保留入样本(is_st留标)", (c.rejected, c.is_st, c.tau0_idx), (False, True, _T + 1))
try:
    clean_event(_rows(), _EV, _DI, st_policy="drop")
    check("②st_policy 非法值拒", "未拒", "ValueError")
except ValueError:
    check("②st_policy 非法值拒", "ValueError", "ValueError")

# ── 证③:辅助方法反向不得改变 adj_bmp_main_only 判决(必验第 3 项;P1-1)──────────────
_A = 0.05  # 双侧临界 ±1.960


def _vd(adj, naive, rank, cal, policy):
    car = {"main_window": {"adj_bmp_car": adj, "naive_t": naive}}
    rb = {"corrado_rank": {"main": {"t_rank": rank}}, "calendar_time": {"main": {"t_cal": cal}}}
    return rn._verdict("OK", car, rb, _A, policy=policy)


v3, _ = _vd(3.5, 3.5, -3.5, 3.5, "three_method")
vm, nm = _vd(3.5, 3.5, -3.5, 3.5, "adj_bmp_main_only")
check("③秩反向:three_method=AMBIGUOUS(既有行为)", v3, "AMBIGUOUS")
check("③秩反向:main_only=SIG 不改判", vm, "SIG")
check("③秩反向:main_only 分歧如实入note", "Corrado秩" in nm and "反向" in nm, True)
v3, _ = _vd(3.5, 3.5, 3.5, -3.5, "three_method")
vm, nm = _vd(3.5, 3.5, 3.5, -3.5, "adj_bmp_main_only")
check("③日历反向:three_method=AMBIGUOUS(既有行为)", v3, "AMBIGUOUS")
check("③日历反向:main_only=SIG 不改判+分歧入note", (vm, "日历时间" in nm), ("SIG", True))
check("③聚集假阳性(朴素t显著ADJ不显著):两策略同=NOT_SIG",
      (_vd(1.0, 5.0, 1.0, 1.0, "three_method")[0], _vd(1.0, 5.0, 1.0, 1.0, "adj_bmp_main_only")[0]),
      ("NOT_SIG", "NOT_SIG"))
check("③三法同向显著:两策略同=SIG",
      (_vd(3.5, 3.5, 3.5, 3.5, "three_method")[0], _vd(3.5, 3.5, 3.5, 3.5, "adj_bmp_main_only")[0]),
      ("SIG", "SIG"))
check("③INSUFFICIENT 闸两策略同过(非辅助法改判)",
      (rn._verdict("INSUFFICIENT", {}, {}, _A)[0],
       rn._verdict("INSUFFICIENT", {}, {}, _A, policy="adj_bmp_main_only")[0]),
      ("INSUFFICIENT", "INSUFFICIENT"))
try:
    rn._verdict("OK", {}, {}, _A, policy="two_method")
    check("③verdict policy 非法值拒", "未拒", "ValueError")
except ValueError:
    check("③verdict policy 非法值拒", "ValueError", "ValueError")

# ── 证④⑤:全流水线 NFV 结构化 + 默认路径结构零回归(必验第 5 项;C6)───────────────────
def _scan_key(obj, key):
    n = 0
    if isinstance(obj, dict):
        for k, v in obj.items():
            n += (1 if k == key else 0) + _scan_key(v, key)
    elif isinstance(obj, list):
        for v in obj:
            n += _scan_key(v, key)
    return n


with tempfile.TemporaryDirectory() as td:
    p, e, m = (os.path.join(td, x) for x in ("p.csv", "e.csv", "m.json"))
    write_csv(generate(), p, e, m)
    pap = synth_pap()
    pap["_family_trial"] = 1
    rd = SyntheticReader(p, e)
    res_a1 = rn.run_study(rd, pap, benchmark_mode="market")
    res_a2 = rn.run_study(SyntheticReader(p, e), pap, benchmark_mode="market")
    check("⑤默认路径双跑逐字节相等(确定性)",
          json.dumps(res_a1, sort_keys=True, default=str) == json.dumps(res_a2, sort_keys=True, default=str), True)
    check("⑤默认路径零新键:全 result 无 not_for_verdict/premend_params",
          (_scan_key(res_a1, "not_for_verdict"), _scan_key(res_a1, "premend_params"),
           _scan_key(res_a1, "not_for_verdict_policy")), (0, 0, 0))
    check("⑤默认路径分层块 verdict 键在位(既有结构不变)", _scan_key(res_a1, "verdict") > 1, True)
    check("⑤默认路径 ST 注记原文不变",
          res_a1["board_strata"]["_st_note"].startswith("ST 为已剔除层(spec §5"), True)
    st_rejected_a = res_a1["board_strata"].get("ST", {}).get("rejected", 0)

    res_b = rn.run_study(SyntheticReader(p, e), pap, benchmark_mode="market",
                         st_policy="keep", verdict_policy="adj_bmp_main_only",
                         nfv_structured=True)
    check("④NFV:唯一 verdict 键=顶层(分层块改名 sig_state_report_only)",
          (_scan_key(res_b, "verdict"), _scan_key(res_b, "sig_state_report_only") >= 1), (1, True))
    marked = set(res_b["not_for_verdict_policy"]["marked_blocks"])
    check("④NFV:非权威块全标记(含 car.robust_window/robustness/双分层)",
          {"per_tau", "robustness", "type_strata", "board_strata", "car.robust_window"} <= marked, True)
    check("④NFV:审计记三参数",
          res_b["audit"]["premend_params"],
          {"st_policy": "keep", "verdict_policy": "adj_bmp_main_only", "nfv_structured": True})
    check("②keep 全流水线:ST 事件入主样本(valid>0 且旧 rejected 归零)",
          (res_b["board_strata"].get("ST", {}).get("valid", 0) > 0,
           res_b["board_strata"].get("ST", {}).get("rejected", 0) < st_rejected_a
           or st_rejected_a == 0), (True, True))
    check("②keep:N_valid 严格增(=ST 保留数并入)", res_b["n_valid"] > res_a1["n_valid"], True)
    check("②keep:ST 注记=保留层文本", "保留层" in res_b["board_strata"]["_st_note"], True)
    rendered_b = report_mod.render(res_b)
    check("④NFV:报告渲染含结构化水印段", "【NOT_FOR_VERDICT 结构化(回修单元 C6)】" in rendered_b, True)
    rendered_a = report_mod.render(res_a1)
    check("⑤默认路径渲染无 NFV 水印段", "NOT_FOR_VERDICT 结构化" in rendered_a, False)

print(f"\n{'='*60}\nverify_limit_open_engine: {N - FAIL}/{N} PASS"
      + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
