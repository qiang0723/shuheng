"""exp8 冻结前回修二 engine 适配自检(人令 2026-07-17 深夜三 + 中途调整令;零 DB,合成域)。

必验覆盖(执行令§四-§七 + 调整令一~六):
  ①C1:postpone_policy 参数化——unified 下纯停牌 1/5/6 日、一字 1/5/6 日、混合 5/6 日统一顺延
    计数(1/5 留、6 剔 postpone);T 缺行/停牌=event_day_anomaly fail-closed 单独留痕;notes 写
    "不可交易状态顺延"并列停牌/一字数量;legacy 默认行为逐字保留(T/T+1 停牌=item7 suspension)。
  ②st_policy 两态+非法值拒(C2 保留,不重开)。
  ③辅助方法反向不得改变 adj_bmp_main_only 判决(P1-1 保留,不重开)。
  ④C3:诊断层三态 fixture——有存活(统计块,无状态判决)/有事件覆盖归零
    (UNESTIMABLE_BY_FROZEN_COVERAGE)/零事件(NO_EVENTS_IN_LAYER);另证清洗致零存活
    =UNESTIMABLE_AFTER_FROZEN_CLEANING;块不缺席。
  ⑤C6 攻击:诊断路径禁调 _verdict(monkeypatch 计数=顶层恰 1 次+诊断构建器在 _verdict 炸弹下
    照常工作);result 递归唯一顶层 verdict;零 sig_state_report_only 及等价判决字段;诊断子树
    无 SIG/NOT_SIG/AMBIGUOUS/INSUFFICIENT 值;两条独立轴无四格交叉统计(cross_counts 仅计数)。
  ⑥field_roles:与主窗实际字段集合逐项对账、无漏项;未分类新字段 fail-closed。
  ⑦P1-4:偏差声明逐字来自 pap['bias_statement'](唯一权威);exp8 报告旧"保守下界"类措辞
    零命中+新声明逐字对账;bias_statement_assert 仅作断言(不等 fail-closed);新策略启用而
    pap 缺键拒跑;默认旧路径固定段+渲染逐字节零回归。
  ⑨回修三·窄阻塞一(P1-4 真锚,人转外部复核令 2026-07-17 深夜四)四证:canonical_pap_sha256
    对 PAP v2 实物重算==文件 sha256==`2611be36…`;改任一实质字段 digest 变;仅加 _family_trial
    不变;错误 digest 断言拒/正确断言放行结果同;result 真锚三元组{pap_sha256,key,text}=引擎
    重算值;报告来源锚直接显示实际 digest、描述性占位零命中。
  ⑩回修三·窄阻塞二(listing-age fail-closed)五证:unknown/None/空串/forecast 旧层名及混入
    单条非法层一律拒绝运行且攻击下 _verdict 调用次数=0;合法 recent/seasoned 放行;白名单与
    PAP diagnostic_dimensions.axes.listing_age 逐项一致(缺失/不一致拒);意外层禁追加
    (_diagnostic_dimensions 兜底 raise,不得追加入报告后继续研究)。
用法: python taosha/harness/verify_limit_open_engine.py
"""
import dataclasses
import datetime as dt
import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.engine import runner as rn                       # noqa: E402
from taosha.engine import report as report_mod               # noqa: E402
from taosha.engine.cleaning import (                          # noqa: E402
    MAX_POSTPONE, CleanedEvent, clean_event,
)
from taosha.experiment.pap import canonical_pap_sha256       # noqa: E402
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


# ── 公共台架:320 交易日轴,事件日 T=idx260(估计窗 [T-250,T-91] 完整)──────────────
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


def _mk(i, one_word=False, is_st=False, susp_flag=False):
    return PriceRow("A", _DS[i], (None if susp_flag else 10.0), susp_flag,
                    ("one_word" if one_word else "none"), "main", is_st, "I")


def _rows(one_word_idx=(), missing_idx=(), flag_idx=(), st_event_day=False):
    """全轴 320 行:one_word_idx 置一字、missing_idx 缺行(=停牌)、flag_idx 停牌 flag 行、
    st_event_day 置事件日行 is_st。"""
    out = []
    for i in range(320):
        if i in missing_idx:
            continue
        out.append(_mk(i, one_word=(i in one_word_idx), is_st=(st_event_day and i == _T),
                       susp_flag=(i in flag_idx)))
    return out


# ── 证①:C1 postpone_policy(legacy 逐字保留 / unified 统一顺延)────────────────────
check("①MAX_POSTPONE 实物=5(冻结口径,边界基准)", MAX_POSTPONE, 5)

# ①a legacy 默认行为逐字保留(既有实验零回归面)
c = clean_event(_rows(one_word_idx={_T + 1}), _EV, _DI)
check("①a legacy顺延1日(T+1一字):留,τ0=T+2", (c.rejected, c.tau0_idx, c.postponed), (False, _T + 2, 1))
check("①a legacy notes=旧'一字板顺延'文案逐字", any(n.startswith("一字板顺延 1 交易日") for n in c.notes), True)
c = clean_event(_rows(one_word_idx=set(range(_T + 1, _T + 6))), _EV, _DI)
check("①a legacy顺延5日=上限:留,τ0=T+6", (c.rejected, c.tau0_idx, c.postponed), (False, _T + 6, 5))
c = clean_event(_rows(one_word_idx=set(range(_T + 1, _T + 7))), _EV, _DI)
check("①a legacy顺延6日=超限:剔postpone", (c.rejected, c.reject_reason), (True, "postpone"))
c = clean_event(_rows(missing_idx={_T + 1}), _EV, _DI)
check("①a legacy T+1纯停牌=item7 suspension(既有默认行为固化,仅辖默认路径)",
      (c.rejected, c.reject_reason), (True, "suspension"))
c = clean_event(_rows(missing_idx={_T}), _EV, _DI)
check("①a legacy T缺行=item7 suspension(既有默认行为固化)", (c.rejected, c.reject_reason), (True, "suspension"))
try:
    clean_event(_rows(), _EV, _DI, postpone_policy="bogus")
    check("①postpone_policy 非法值拒", "未拒", "ValueError")
except ValueError:
    check("①postpone_policy 非法值拒", "ValueError", "ValueError")

# ①b unified:纯停牌 1/5/6 日(缺行;人令§四:不得用混合替代纯停牌)
c = clean_event(_rows(missing_idx={_T + 1}), _EV, _DI, postpone_policy="unified")
check("①b unified纯停牌1日:留,τ0=T+2,postpone=1", (c.rejected, c.tau0_idx, c.postponed), (False, _T + 2, 1))
check("①b unified notes='不可交易状态顺延'+停牌/一字分计",
      any("不可交易状态顺延 1 交易日(停牌1/一字0)" in n for n in c.notes), True)
c = clean_event(_rows(missing_idx=set(range(_T + 1, _T + 6))), _EV, _DI, postpone_policy="unified")
check("①b unified纯停牌5日=上限:留,τ0=T+6", (c.rejected, c.tau0_idx, c.postponed), (False, _T + 6, 5))
c = clean_event(_rows(missing_idx=set(range(_T + 1, _T + 7))), _EV, _DI, postpone_policy="unified")
check("①b unified纯停牌6日=超限:剔postpone", (c.rejected, c.reject_reason), (True, "postpone"))
check("①b unified超限notes列停牌/一字数量", any("(停牌6/一字0)" in n for n in c.notes), True)
c = clean_event(_rows(flag_idx={_T + 1}), _EV, _DI, postpone_policy="unified")
check("①b unified纯停牌1日(flag行变体):留,τ0=T+2", (c.rejected, c.tau0_idx, c.postponed), (False, _T + 2, 1))

# ①c unified:一字 1/5/6 日(一字路径在 unified 下同样成立)
c = clean_event(_rows(one_word_idx={_T + 1}), _EV, _DI, postpone_policy="unified")
check("①c unified一字1日:留,τ0=T+2", (c.rejected, c.tau0_idx, c.postponed), (False, _T + 2, 1))
c = clean_event(_rows(one_word_idx=set(range(_T + 1, _T + 6))), _EV, _DI, postpone_policy="unified")
check("①c unified一字5日=上限:留,τ0=T+6", (c.rejected, c.tau0_idx, c.postponed), (False, _T + 6, 5))
c = clean_event(_rows(one_word_idx=set(range(_T + 1, _T + 7))), _EV, _DI, postpone_policy="unified")
check("①c unified一字6日=超限:剔postpone", (c.rejected, c.reject_reason), (True, "postpone"))

# ①d unified:混合合计 5/6 日(一字1+停牌4=5留;一字1+停牌5=6剔)
c = clean_event(_rows(one_word_idx={_T + 1}, missing_idx=set(range(_T + 2, _T + 6))),
                _EV, _DI, postpone_policy="unified")
check("①d unified混合5日(一字1+停牌4):留,τ0=T+6", (c.rejected, c.tau0_idx, c.postponed), (False, _T + 6, 5))
check("①d unified混合notes分计(停牌4/一字1)", any("(停牌4/一字1)" in n for n in c.notes), True)
c = clean_event(_rows(one_word_idx={_T + 1}, missing_idx=set(range(_T + 2, _T + 7))),
                _EV, _DI, postpone_policy="unified")
check("①d unified混合6日(一字1+停牌5):剔postpone", (c.rejected, c.reject_reason), (True, "postpone"))

# ①e unified:T 事件日缺行/停牌 = event_day_anomaly fail-closed(单独留痕,不与 T+1 顺延混淆)
c = clean_event(_rows(missing_idx={_T}), _EV, _DI, postpone_policy="unified")
check("①e unified T缺行=event_day_anomaly fail-closed", (c.rejected, c.reject_reason),
      (True, "event_day_anomaly"))
check("①e unified T异常单独留痕(不混淆顺延)", any("event_day_anomaly" in n and "不与 T+1 顺延混淆" in n
                                                   for n in c.notes), True)
c = clean_event(_rows(flag_idx={_T}), _EV, _DI, postpone_policy="unified")
check("①e unified T停牌flag=event_day_anomaly", (c.rejected, c.reject_reason), (True, "event_day_anomaly"))

# ── 证②:st_policy 两态 + 非法值拒(C2 保留,不重开)────────────────────────────────
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

# ── 证③:辅助方法反向不得改变 adj_bmp_main_only 判决(P1-1 保留,不重开)──────────────
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

# ── 递归扫描工具 ───────────────────────────────────────────────────────────────────
def _scan_key(obj, key):
    n = 0
    if isinstance(obj, dict):
        for k, v in obj.items():
            n += (1 if k == key else 0) + _scan_key(v, key)
    elif isinstance(obj, list):
        for v in obj:
            n += _scan_key(v, key)
    return n


def _scan_values(obj, targets: set) -> int:
    n = 0
    if isinstance(obj, dict):
        for v in obj.values():
            n += _scan_values(v, targets)
    elif isinstance(obj, list):
        for v in obj:
            n += _scan_values(v, targets)
    elif isinstance(obj, str) and obj in targets:
        n += 1
    return n


# exp8 偏差声明固定口径(人令§六原文;唯一权威=pap['bias_statement'])
EXP8_BIAS = ("清洗剔除与listing fail-closed产生样本选择,偏差方向未知;"
             "估计对象仅限清洗存活样本,不得外推为全体一字涨停链事件的效应。")
FORBIDDEN_PHRASES = ("保守处置", "倾向缩小效应", "真实效应不小于报告值", "保守下界")
EXP8_KW = dict(st_policy="keep", verdict_policy="adj_bmp_main_only", nfv_structured=True,
               postpone_policy="unified", diagnostic_dims=("listing_age", "st"),
               strata_enabled=False)

# PAP v2 实物对账(逐字):fixture 期望声明/参数须与冻结候选 PAP 实物一致,防两套口径
_PAP_V2_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "docs", "limit-open-pap-final-v2-2026-07-17.json")
with open(_PAP_V2_PATH, encoding="utf-8") as _fh:
    _PAP_V2 = json.load(_fh)
check("⑦PAP v2 实物 bias_statement 与 fixture 期望逐字相等", _PAP_V2["bias_statement"], EXP8_BIAS)
_ep = _PAP_V2["engine_params"]
check("⑦PAP v2 engine_params 冻结值与 EXP8_KW 逐项一致(driver 逐字消费面)",
      (_ep["st_policy"], _ep["verdict_policy"], _ep["nfv_structured"], _ep["postpone_policy"],
       tuple(_ep["diagnostic_dims"]), _ep["strata_enabled"], _ep["st_mode"], _ep["benchmark_mode"]),
      ("keep", "adj_bmp_main_only", True, "unified", ("listing_age", "st"), False,
       "event_day", "market"))

# ── 证⑨(模块级):canonical PAP digest 四证(回修三·窄阻塞一,对 PAP v2 实物)──────────
_V2_DIGEST_EXPECT = "2611be36a37b89055a5e4c393f18c507492b36fa51db323db66d43be370b66b4"
with open(_PAP_V2_PATH, "rb") as _fh:
    _V2_FILE_SHA = hashlib.sha256(_fh.read()).hexdigest()
check("⑨canonical:引擎重算 PAP v2 == 文件 sha256(canonical 算法与 PAP 文件对账)",
      canonical_pap_sha256(_PAP_V2), _V2_FILE_SHA)
check("⑨canonical:PAP v2 重算得 2611be36…(人令定点值)",
      canonical_pap_sha256(_PAP_V2), _V2_DIGEST_EXPECT)
check("⑨canonical:仅添加 _family_trial 不改变冻结 PAP digest(非 PAP 字段不进 digest)",
      canonical_pap_sha256(dict(_PAP_V2, _family_trial=7)), _V2_DIGEST_EXPECT)
for _k in ("window", "bias_statement", "event_def"):
    _mut = dict(_PAP_V2)
    _mut[_k] = str(_mut[_k]) + "X"
    check(f"⑨canonical:修改实质字段 {_k} → digest 改变",
          canonical_pap_sha256(_mut) != _V2_DIGEST_EXPECT, True)

# ── 证⑩(模块级):listing_age 白名单=引擎↔PAP v2 实物逐项一致 ──────────────────────
check("⑩白名单:引擎 _DIAG_DIM_SPECS['listing_age'].layers == PAP v2 axes.listing_age 逐项一致",
      list(rn._DIAG_DIM_SPECS["listing_age"]["layers"]),
      _PAP_V2["diagnostic_dimensions"]["axes"]["listing_age"])

# ── 证④~⑧:全流水线(合成域)────────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    p, e, m = (os.path.join(td, x) for x in ("p.csv", "e.csv", "m.json"))
    write_csv(generate(), p, e, m)
    pap = synth_pap()
    pap["_family_trial"] = 1
    # pap8 携带 diagnostic_dimensions.axes(回修三·窄阻塞二:白名单须与 PAP 逐项一致对账)
    _DIAG_AXES = {"axes": {"listing_age": ["recent_listing", "seasoned"], "st": ["ST", "non_ST"]}}
    pap8 = dict(synth_pap(), _family_trial=1, bias_statement=EXP8_BIAS,
                diagnostic_dimensions=_DIAG_AXES)
    rd = SyntheticReader(p, e)
    cal_dates = [c.trade_date for c in rd.calendar()]
    base_events = list(SyntheticReader(p, e).events())

    # ⑧ 默认路径零回归(双跑相等 + 零新键 + 渲染无新增段/标记)
    res_a1 = rn.run_study(SyntheticReader(p, e), pap, benchmark_mode="market")
    res_a2 = rn.run_study(SyntheticReader(p, e), pap, benchmark_mode="market")
    check("⑧默认路径双跑逐字节相等(确定性)",
          json.dumps(res_a1, sort_keys=True, default=str) == json.dumps(res_a2, sort_keys=True, default=str), True)
    check("⑧默认路径零新键(nfv/premend/dims/bias/field_roles 全零)",
          (_scan_key(res_a1, "not_for_verdict"), _scan_key(res_a1, "premend_params"),
           _scan_key(res_a1, "not_for_verdict_policy"), _scan_key(res_a1, "diagnostic_dimensions"),
           _scan_key(res_a1, "bias_statement"), _scan_key(res_a1, "field_roles")),
          (0, 0, 0, 0, 0, 0))
    check("⑧默认路径分层块 verdict 键在位(既有结构不变)", _scan_key(res_a1, "verdict") > 1, True)
    check("⑧默认路径 ST 注记原文不变",
          res_a1["board_strata"]["_st_note"].startswith("ST 为已剔除层(spec §5"), True)
    rendered_a = report_mod.render(res_a1)
    check("⑧默认渲染=原固定偏差段在位", "【偏差方向声明(固定段,item 9)】" in rendered_a, True)
    check("⑧默认渲染零新增标记/段落",
          ("[NOT_FOR_VERDICT]" in rendered_a, "正交诊断维度" in rendered_a,
           "NOT_FOR_VERDICT 结构化" in rendered_a), (False, False, False))

    # ④C3 三态 + ⑤C6 + ⑥field_roles + ⑦P1-4:exp8 模式(诊断路径禁调 _verdict 由计数攻击证明)
    half = len(base_events) // 2
    ev_split = ([dataclasses.replace(ev, event_type_layer="recent_listing") for ev in base_events[:half]]
                + [dataclasses.replace(ev, event_type_layer="seasoned") for ev in base_events[half:]])
    _orig_verdict = rn._verdict
    _calls = {"n": 0}

    def _counting_verdict(*a, **k):
        _calls["n"] += 1
        return _orig_verdict(*a, **k)

    rn._verdict = _counting_verdict
    try:
        res8 = rn.run_study(SyntheticReader(p, e), pap8, benchmark_mode="market",
                            events=ev_split, **EXP8_KW)
    finally:
        rn._verdict = _orig_verdict
    check("⑤C6攻击:全跑 _verdict 恰调用 1 次(=顶层;诊断路径零调用)", _calls["n"], 1)
    check("⑤C6递归:唯一 verdict 键=顶层", (_scan_key(res8, "verdict"), _scan_key(res8, "verdict_note")), (1, 1))
    check("⑤C6递归:零 sig_state_report_only/sig_state_note(改名旁路已废)",
          (_scan_key(res8, "sig_state_report_only"), _scan_key(res8, "sig_state_note")), (0, 0))
    dd = res8["diagnostic_dimensions"]
    check("⑤C6诊断子树:无 SIG/NOT_SIG/AMBIGUOUS/INSUFFICIENT 分类值",
          _scan_values(dd, {"SIG", "NOT_SIG", "AMBIGUOUS", "INSUFFICIENT"}), 0)
    check("⑤C6两条独立轴在场(listing_age+st,无第三维)", sorted(dd["dims"].keys()), ["listing_age", "st"])
    la = dd["dims"]["listing_age"]["layers"]
    stx = dd["dims"]["st"]["layers"]
    check("④C3有存活:recent_listing 统计块在场且无状态判决键",
          (la["recent_listing"]["n_valid"] > 0, la["recent_listing"]["stats"] is not None,
           "status" in la["recent_listing"]), (True, True, False))
    check("④C3有存活:seasoned 同报统计块", (la["seasoned"]["n_valid"] > 0,
                                             la["seasoned"]["stats"] is not None), (True, True))
    check("⑤ST轴两层在场(ST/non_ST;keep 下 ST 有存活)",
          ("ST" in stx and "non_ST" in stx, stx["ST"]["n_valid"] > 0), (True, True))
    check("⑤诊断层统计块无判决字段(main_window 无 verdict 类键)",
          (_scan_key(dd, "verdict"), _scan_key(dd, "verdict_note")), (0, 0))
    cc = dd.get("cross_counts") or {}
    check("⑤二维矩阵=仅计数核对(cells 只有 n_events/n_valid)",
          all(set(v.keys()) == {"n_events", "n_valid"} for v in (cc.get("cells") or {}).values())
          and len(cc.get("cells") or {}) >= 1, True)
    check("⑤type_strata 注记中性(无 #2b/无 forecast 文案)",
          ("#2b" in res8["type_strata"]["note"], "预喜" in res8["type_strata"]["note"]), (False, False))
    check("⑤审计记全参数(含实际 postpone_policy,人令调整一)",
          res8["audit"]["premend_params"],
          {"st_policy": "keep", "verdict_policy": "adj_bmp_main_only", "nfv_structured": True,
           "postpone_policy": "unified", "diagnostic_dims": ["listing_age", "st"]})
    marked = set(res8["not_for_verdict_policy"]["marked_blocks"])
    check("⑤NFV:非权威块全标记(含 diagnostic_dimensions/car.robust_window)",
          {"per_tau", "robustness", "type_strata", "board_strata", "car.robust_window",
           "diagnostic_dimensions"} <= marked, True)
    check("②keep 全流水线:ST 入主样本(board_strata ST valid>0)+N_valid 增",
          (res8["board_strata"].get("ST", {}).get("valid", 0) > 0,
           res8["n_valid"] > res_a1["n_valid"]), (True, True))

    # ⑥ field_roles 与主窗实际字段逐项对账、无漏项
    mw8 = res8["car"]["main_window"]
    fr = mw8.get("field_roles") or {}
    check("⑥field_roles=主窗实际字段全覆盖(逐项对账无漏项)",
          set(fr.keys()) == set(mw8.keys()) - {"field_roles"}, True)
    check("⑥角色:adj_bmp_car=VERDICT_AUTHORITY / naive_t·bmp_car·caar=NOT_FOR_VERDICT / taus·n=CONTEXT",
          (fr.get("adj_bmp_car"), fr.get("naive_t"), fr.get("bmp_car"), fr.get("caar"),
           fr.get("taus"), fr.get("n")),
          ("VERDICT_AUTHORITY", "NOT_FOR_VERDICT", "NOT_FOR_VERDICT", "NOT_FOR_VERDICT",
           "CONTEXT", "CONTEXT"))
    try:
        rn._main_window_field_roles({"adj_bmp_car": 1.0, "mystery_stat": 2.0})
        check("⑥未分类新统计字段 fail-closed", "未拒", "ValueError")
    except ValueError:
        check("⑥未分类新统计字段 fail-closed", "ValueError", "ValueError")

    # ⑦ P1-4 报告对账
    check("⑦result 偏差声明逐字来自 pap['bias_statement']",
          res8["bias_statement"]["text"] == pap8["bias_statement"] == EXP8_BIAS, True)
    rendered8 = report_mod.render(res8)
    check("⑦exp8报告渲染新声明逐字+来源锚", (EXP8_BIAS in rendered8, "来源锚" in rendered8), (True, True))
    check("⑦exp8报告旧禁止措辞零命中(保守处置/倾向缩小效应/真实效应不小于报告值/保守下界)",
          [ph for ph in FORBIDDEN_PHRASES if ph in rendered8], [])
    check("⑦exp8报告无 forecast 专属文案(预喜/预亏/扭亏零命中)",
          ("预喜" in rendered8, "预亏" in rendered8, "扭亏" in rendered8), (False, False, False))
    check("⑦exp8报告渲染两条独立轴+NOT_FOR_VERDICT 直接标记",
          ("【正交诊断维度(C6 二次回修;两条独立轴" in rendered8,
           "recent_listing [NOT_FOR_VERDICT]" in rendered8,
           "ST [NOT_FOR_VERDICT]" in rendered8), (True, True, True))
    try:
        rn.run_study(SyntheticReader(p, e), pap, benchmark_mode="market",
                     events=ev_split, **EXP8_KW)   # pap 无 bias_statement
        check("⑦新策略启用而 pap 缺 bias_statement → 拒绝运行", "未拒", "ValueError")
    except ValueError:
        check("⑦新策略启用而 pap 缺 bias_statement → 拒绝运行", "ValueError", "ValueError")
    try:
        rn.run_study(SyntheticReader(p, e), pap8, benchmark_mode="market", events=ev_split,
                     bias_statement_assert="别的文字", **EXP8_KW)
        check("⑦bias_statement_assert 与 pap 不等 → fail-closed", "未拒", "ValueError")
    except ValueError:
        check("⑦bias_statement_assert 与 pap 不等 → fail-closed", "ValueError", "ValueError")
    res8b = rn.run_study(SyntheticReader(p, e), pap8, benchmark_mode="market", events=ev_split,
                         bias_statement_assert=EXP8_BIAS, **EXP8_KW)
    check("⑦bias_statement_assert 逐字相等 → 放行且结果同",
          json.dumps(res8b, sort_keys=True, default=str) == json.dumps(res8, sort_keys=True, default=str), True)

    # ⑨ P1-4 真锚(回修三·窄阻塞一):result 三元组 + 报告实际 digest + digest 断言两态
    pap8_sha = canonical_pap_sha256(pap8)
    bs8 = res8["bias_statement"]
    check("⑨result 真锚三元组{pap_sha256,key,text}在场且 pap_sha256=引擎重算值",
          (bs8["pap_sha256"], bs8["key"], bs8["text"]), (pap8_sha, "bias_statement", EXP8_BIAS))
    check("⑨result 来源锚串内含实际 digest(非描述性占位)", pap8_sha in bs8["source_anchor"], True)
    check("⑨报告来源锚直接显示实际 digest", f"pap_sha256={pap8_sha}" in rendered8, True)
    check("⑨报告描述性占位文本零命中(旧 source_anchor 文案已废)",
          "pap['bias_statement'](" in rendered8, False)
    try:
        rn.run_study(SyntheticReader(p, e), pap8, benchmark_mode="market", events=ev_split,
                     pap_sha256_assert="0" * 64, **EXP8_KW)
        check("⑨错误 digest 断言 → fail-closed 拒", "未拒", "ValueError")
    except ValueError:
        check("⑨错误 digest 断言 → fail-closed 拒", "ValueError", "ValueError")
    res8c = rn.run_study(SyntheticReader(p, e), pap8, benchmark_mode="market", events=ev_split,
                         pap_sha256_assert=pap8_sha, **EXP8_KW)
    check("⑨正确 digest 断言(=引擎重算值)→ 放行且结果同",
          json.dumps(res8c, sort_keys=True, default=str) == json.dumps(res8, sort_keys=True, default=str), True)

    # ⑩ listing-age fail-closed(回修三·窄阻塞二):非法层攻击五证(拒 + _verdict 零调用)
    def _attack_listing(events_bad, name):
        calls = {"n": 0}

        def _cv(*a, **k):
            calls["n"] += 1
            return _orig_verdict(*a, **k)

        rn._verdict = _cv
        try:
            rn.run_study(SyntheticReader(p, e), pap8, benchmark_mode="market",
                         events=events_bad, **EXP8_KW)
            got = "未拒"
        except ValueError:
            got = "ValueError"
        finally:
            rn._verdict = _orig_verdict
        check(f"⑩{name} → fail-closed 拒绝运行", got, "ValueError")
        check(f"⑩{name}:攻击下 _verdict() 调用次数=0(校验先于顶层判决)", calls["n"], 0)

    _attack_listing([dataclasses.replace(ev, event_type_layer="unknown") for ev in base_events],
                    "全事件标 unknown 层")
    _attack_listing([dataclasses.replace(ev, event_type_layer=None) for ev in base_events],
                    "缺失层(None)")
    _attack_listing([dataclasses.replace(ev, event_type_layer="") for ev in base_events],
                    "空字符串层")
    _attack_listing([dataclasses.replace(ev, event_type_layer="预喜") for ev in base_events],
                    "forecast 旧层名(预喜)")
    _attack_listing(ev_split + [dataclasses.replace(ev_split[0], event_id="A:badlayer",
                                                    event_type_layer="unknown")],
                    "合法样本混入单条非法层")
    check("⑩合法 recent/seasoned 全体放行(res8 即证:顶层判决在场+两层诊断块)",
          ("verdict" in res8, sorted(la.keys())), (True, ["recent_listing", "seasoned"]))
    pap8_nodiag = dict(synth_pap(), _family_trial=1, bias_statement=EXP8_BIAS)
    try:
        rn.run_study(SyntheticReader(p, e), pap8_nodiag, benchmark_mode="market",
                     events=ev_split, **EXP8_KW)
        check("⑩PAP 缺 diagnostic_dimensions.axes.listing_age(白名单不逐项一致)→ 拒", "未拒", "ValueError")
    except ValueError:
        check("⑩PAP 缺 diagnostic_dimensions.axes.listing_age(白名单不逐项一致)→ 拒",
              "ValueError", "ValueError")

    # ④C3 覆盖归零态:recent_listing 仅 1 事件且历史门槛剔(coverage/history 类)→ BY_FROZEN_COVERAGE
    ev_b = ([EventRow(ts_code=base_events[0].ts_code, event_id=f"{base_events[0].ts_code}:rlB",
                      first_ann_date=cal_dates[10], event_type_layer="recent_listing",
                      snapshot_batch="S")]
            + [dataclasses.replace(ev, event_type_layer="seasoned") for ev in base_events])
    res_b3 = rn.run_study(SyntheticReader(p, e), pap8, benchmark_mode="market",
                          events=ev_b, **EXP8_KW)
    la_b = res_b3["diagnostic_dimensions"]["dims"]["listing_age"]["layers"]["recent_listing"]
    check("④C3覆盖归零:n_events=1/n_valid=0 → UNESTIMABLE_BY_FROZEN_COVERAGE",
          (la_b["n_events"], la_b["n_valid"], la_b["status"]),
          (1, 0, "UNESTIMABLE_BY_FROZEN_COVERAGE"))
    check("④C3覆盖归零:逐因分解在场(history 门槛)",
          la_b["rejections_by_reason_total"], {"history": 1})

    # ④C3 零事件态:recent_listing 无事件 → NO_EVENTS_IN_LAYER 且块不缺席
    ev_c = [dataclasses.replace(ev, event_type_layer="seasoned") for ev in base_events]
    res_c3 = rn.run_study(SyntheticReader(p, e), pap8, benchmark_mode="market",
                          events=ev_c, **EXP8_KW)
    la_c = res_c3["diagnostic_dimensions"]["dims"]["listing_age"]["layers"]["recent_listing"]
    check("④C3零事件:块在场 NO_EVENTS_IN_LAYER", (la_c["n_events"], la_c["status"]),
          (0, "NO_EVENTS_IN_LAYER"))

# ④C3 清洗致零存活态(直接喂构建器;顺带证:_verdict 炸弹下诊断构建器照常工作=结构性禁调)
def _boom(*a, **k):
    raise AssertionError("诊断路径调用了 _verdict() —— 违反人令调整三")


_ce_d = CleanedEvent(ts_code="X", event_id="X:d", first_ann_date=dt.date(2021, 6, 1),
                     board="main", is_st=False, industry="I", regime_segment="pre_10pct",
                     t_idx=300, event_type_layer="recent_listing")
_ce_d.rejected, _ce_d.reject_reason, _ce_d.reject_year = True, "event_day_anomaly", 2021
_ce_d2 = CleanedEvent(ts_code="Y", event_id="Y:d", first_ann_date=dt.date(2022, 6, 1),
                      board="main", is_st=False, industry="I", regime_segment="pre_10pct",
                      t_idx=301, event_type_layer="recent_listing")
_ce_d2.rejected, _ce_d2.reject_reason, _ce_d2.reject_year = True, "suspension", 2022
_orig = rn._verdict
rn._verdict = _boom
try:
    dd_d = rn._diagnostic_dimensions([_ce_d, _ce_d2], [], 3, 6, (), ("listing_age", "st"))
    boom_ok = True
except AssertionError:
    dd_d, boom_ok = None, False
finally:
    rn._verdict = _orig
check("⑤C6攻击:_verdict 炸弹下诊断构建器照常工作(结构性零调用)", boom_ok, True)
la_d = dd_d["dims"]["listing_age"]["layers"]["recent_listing"]
check("④C3清洗致零存活(event_day_anomaly+suspension 混合)→ UNESTIMABLE_AFTER_FROZEN_CLEANING",
      (la_d["n_events"], la_d["n_valid"], la_d["status"]),
      (2, 0, "UNESTIMABLE_AFTER_FROZEN_CLEANING"))
check("④C3清洗致零存活:逐因分解在场",
      la_d["rejections_by_reason_total"], {"event_day_anomaly": 1, "suspension": 1})
check("④C3清洗致零存活:逐年分解在场(2021/2022)",
      sorted(la_d["rejections"]["by_year"].keys()), [2021, 2022])

# ⑩ 兜底证:_diagnostic_dimensions 遇白名单外层 raise(意外层禁追加入报告后继续研究;
# 主校验在 run_study 事件源处先行,此为构建器兜底)
_ce_bad = CleanedEvent(ts_code="Z", event_id="Z:bad", first_ann_date=dt.date(2021, 6, 1),
                       board="main", is_st=False, industry="I", regime_segment="pre_10pct",
                       t_idx=300, event_type_layer="unknown")
try:
    rn._diagnostic_dimensions([_ce_bad], [], 3, 6, (), ("listing_age",))
    check("⑩兜底:_diagnostic_dimensions 白名单外层禁追加 → raise", "未拒", "ValueError")
except ValueError:
    check("⑩兜底:_diagnostic_dimensions 白名单外层禁追加 → raise", "ValueError", "ValueError")

print(f"\n{'='*60}\nverify_limit_open_engine: {N - FAIL}/{N} PASS"
      + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
