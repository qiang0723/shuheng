"""exp20 earnings_revision engine 适配攻击自检(冻结令 2026-07-18 深夜六 令三③;零 DB,合成域)。

预注册攻击 fixture 清单(交付档 §5+§7.3)本件覆盖引擎层各组:
  #1 signed 同向归一 / #2 反向样本(up=+1 恒等、down=−1 逐 τ 精确翻转,先于聚合)
  #3 SIG+REVERSED 措辞攻击(报告零"支持"类措辞+警示句在场)
  #4 公告日历锚(周末/节假日公告不剔;τ0=ann_date 后首个交易所交易日;锚日缺 bar 不构成
     event_day_anomaly——exp8 规则明令不引入)
  #5 顺延边界(公告语义 1/5/6 日,缺 bar/停牌/一字混合;5 留 6 剔)
  #6(引擎半)白名单外方向值进 CAR 前 fail-closed(泄漏攻击=#12)
  #7 raw 诊断层零判决(递归零 verdict/零显著性分类;_verdict 计数攻击=恰顶层 1 次;
     诊断层消费 raw 平行对象=与 raw 跑逐字节同)
  #8 signed 输入实改证明(估计期残差→ρ̄ 改变/秩输入改变/CAAR 非 ±raw 展示翻转可及;
     csar_sd 不因乘 ±1 改变)
  #9 pap_sha256_assert 逐字断言 fail-closed(错误拒/正确放行结果同)
  #12 flat 泄漏拒跑(flat/null/unknown/空串/旧层名/混入单条,CAR 与 verdict 前拒,_verdict=0)
  #13 effect_alignment 四分支(单元:正/负/零/不可得+INSUFFICIENT/AMBIGUOUS;集成:三态)
  #14 四态零判决影响(alignment 开/关 verdict 逐字节同;字段角色=CONTEXT)
  另:reporting⑥ signed CAAR 与 ADJ-BMP 符号不一致并列披露;premend_params 审计;
  特别验证⑦ 默认路径零新键零回归(e2e 逐字节基线另跑官方 harness)。
用法: python taosha/harness/verify_earnings_revision_engine.py
"""
import dataclasses
import datetime as dt
import json
import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.engine import report as report_mod                # noqa: E402
from taosha.engine import runner as rn                        # noqa: E402
from taosha.engine.cleaning import MAX_POSTPONE, clean_event  # noqa: E402
from taosha.harness.make_ashare_fixture import generate, write_csv  # noqa: E402
from taosha.harness.run_ashare_study import synth_pap         # noqa: E402
from taosha.reader.contract import EventRow, PriceRow         # noqa: E402
from taosha.reader.synthetic import SyntheticReader           # noqa: E402

FAIL = 0
N = 0


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    if not ok:
        FAIL += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


EXP20_BIAS = "合成测试偏差声明(exp20 引擎自检专用,非冻结原文)。"
# 冻结 PAP v2 engine_params 的引擎面(合成域自检;真实冻结件逐字消费在 driver,
# 见 verify_earnings_revision_adapter 对 PAP v2 实物的对账)
EXP20_KW = dict(strata_enabled=False, st_policy="reject", verdict_policy="adj_bmp_main_only",
                nfv_structured=True, postpone_policy="unified_announcement",
                diagnostic_dims=("direction",), direction_signed_main=True,
                direction_display="raw", effect_alignment_source="adj_bmp_sign")
RAW_KW = dict(EXP20_KW, direction_signed_main=False, direction_display=None,
              effect_alignment_source=None)


# ── #13 单元:effect_alignment 四态全定义函数(冻结 PAP v2 verdict_authority 逐字)────
check("#13白名单:引擎 direction layers == ('up','down')",
      list(rn._DIAG_DIM_SPECS["direction"]["layers"]), ["up", "down"])
check("#13单元:SIG+正→ALIGNED", rn._effect_alignment("SIG", 3.2), "ALIGNED")
check("#13单元:SIG+负→REVERSED", rn._effect_alignment("SIG", -3.2), "REVERSED")
check("#13单元:NOT_SIG+正/负→ALIGNED/REVERSED(四态与显著性正交)",
      (rn._effect_alignment("NOT_SIG", 0.5), rn._effect_alignment("NOT_SIG", -0.5)),
      ("ALIGNED", "REVERSED"))
check("#13单元:统计量=0→NEUTRAL", rn._effect_alignment("SIG", 0.0), "NEUTRAL")
check("#13单元:统计量不可得(None)→UNAVAILABLE", rn._effect_alignment("NOT_SIG", None), "UNAVAILABLE")
check("#13单元:INSUFFICIENT 即便统计量在场→UNAVAILABLE(不得猜方向)",
      rn._effect_alignment("INSUFFICIENT", -0.8), "UNAVAILABLE")
check("#13单元:AMBIGUOUS 即便统计量在场→UNAVAILABLE(不得猜方向)",
      rn._effect_alignment("AMBIGUOUS", 2.5), "UNAVAILABLE")

# ── #4/#5 cleaning 层:公告日历锚 + 顺延边界(320 交易日轴台架)─────────────────────
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


def _mk(i, one_word=False, susp_flag=False):
    return PriceRow("A", _DS[i], (None if susp_flag else 10.0), susp_flag,
                    ("one_word" if one_word else "none"), "main", False, "I")


def _rows(one_word_idx=(), missing_idx=(), flag_idx=()):
    out = []
    for i in range(320):
        if i in missing_idx:
            continue
        out.append(_mk(i, one_word=(i in one_word_idx), susp_flag=(i in flag_idx)))
    return out


def _ev(ann):
    return EventRow(ts_code="A", event_id="A:e1", first_ann_date=ann,
                    event_type_layer="down", snapshot_batch="S")


UA = dict(postpone_policy="unified_announcement", axis_dates=_DS)
# #4a 周末公告:轴内 _DS[_T] 为交易日,其后第一个周六=非交易所交易日
_sat = _DS[_T] + dt.timedelta(days=(5 - _DS[_T].weekday()) % 7 or 7)
assert _sat.weekday() == 5 and _sat not in _DI
_anchor = max(i for i, d in enumerate(_DS) if d <= _sat)
c = clean_event(_rows(), _ev(_sat), _DI, **UA)
check("#4a周末公告不剔:锚=≤ann 最近交易日,τ0=其后首个交易所交易日,零顺延",
      (c.rejected, c.t_idx, c.tau0_idx, c.postponed), (False, _anchor, _anchor + 1, 0))
# #4b 交易日公告:τ0=T+1(CAR 起点=T+1,既裁)
c = clean_event(_rows(), _ev(_DS[_T]), _DI, **UA)
check("#4b交易日公告:锚=T,τ0=T+1", (c.rejected, c.t_idx, c.tau0_idx), (False, _T, _T + 1))
# #4c 锚日缺 bar(停牌):不构成剔除事由(无 event_day_anomaly;exp8 规则明令不引入)
c = clean_event(_rows(missing_idx={_T}), _ev(_DS[_T]), _DI, **UA)
check("#4c锚日缺bar:不剔(无 event_day_anomaly),τ0 照常=T+1,ST 判定不可得留注",
      (c.rejected, c.tau0_idx, any("锚交易日行缺失" in n for n in c.notes)), (False, _T + 1, True))
c2 = clean_event(_rows(missing_idx={_T}), _ev(_DS[_T]), _DI, postpone_policy="unified")
check("#4c对照:同几何在 exp8 unified 下=event_day_anomaly(规则不同实验不同,结构隔离)",
      (c2.rejected, c2.reject_reason), (True, "event_day_anomaly"))
# #4d 公告日前轴无历史→history 剔(bisect 无落点)
c = clean_event(_rows(), _ev(_DS[0] - dt.timedelta(days=1)), _DI, **UA)
check("#4d公告日前轴无历史→history 剔除", (c.rejected, c.reject_reason), (True, "history"))
# #4e unified_announcement 未传 axis_dates → fail-closed
try:
    clean_event(_rows(), _ev(_DS[_T]), _DI, postpone_policy="unified_announcement")
    check("#4e未传 axis_dates → fail-closed 拒", "未拒", "ValueError")
except ValueError:
    check("#4e未传 axis_dates → fail-closed 拒", "ValueError", "ValueError")

# #5 顺延边界:1 日(缺bar)/5 日混合(缺bar+一字+停牌flag)留/6 日剔
check("#5基准:MAX_POSTPONE 实物=5(冻结口径)", MAX_POSTPONE, 5)
c = clean_event(_rows(missing_idx={_T + 1}), _ev(_DS[_T]), _DI, **UA)
check("#5顺延1日(T+1缺bar):留,τ0=T+2", (c.rejected, c.tau0_idx, c.postponed), (False, _T + 2, 1))
c = clean_event(_rows(missing_idx={_T + 1, _T + 2}, one_word_idx={_T + 3, _T + 4},
                      flag_idx={_T + 5}), _ev(_DS[_T]), _DI, **UA)
check("#5顺延5日混合(缺2+一字2+flag1)=上限:留,τ0=T+6,注记=公告事件语义",
      (c.rejected, c.tau0_idx, c.postponed,
       any("公告事件语义,人裁十项之七" in n for n in c.notes)), (False, _T + 6, 5, True))
c = clean_event(_rows(missing_idx={_T + 1, _T + 2}, one_word_idx={_T + 3, _T + 4},
                      flag_idx={_T + 5, _T + 6}), _ev(_DS[_T]), _DI, **UA)
check("#5顺延6日=超限:剔 postpone(第 6 日仍不可交易)",
      (c.rejected, c.reject_reason), (True, "postpone"))
# #5b 周末公告+周一起不可交易:顺延自 ann 后首个交易所交易日起计
c = clean_event(_rows(one_word_idx={_anchor + 1}), _ev(_sat), _DI, **UA)
check("#5b周末公告+下一交易日一字:顺延1,τ0=再下一日",
      (c.rejected, c.tau0_idx, c.postponed), (False, _anchor + 2, 1))

# ── 全流水线(合成域)────────────────────────────────────────────────────────────────
with tempfile.TemporaryDirectory() as td:
    p, e, m = (os.path.join(td, x) for x in ("p.csv", "e.csv", "m.json"))
    write_csv(generate(), p, e, m)
    pap = synth_pap()
    pap["_family_trial"] = 1
    pap20 = dict(synth_pap(), _family_trial=1, bias_statement=EXP20_BIAS,
                 diagnostic_dimensions={"axes": {"direction": ["up", "down"]}})
    base_events = list(SyntheticReader(p, e).events())

    def _lay(fn):
        return [dataclasses.replace(ev, event_type_layer=("up" if fn(i) else "down"))
                for i, ev in enumerate(base_events)]

    ev_up = _lay(lambda i: True)
    ev_down = _lay(lambda i: False)
    ev_mix = _lay(lambda i: (i // 3) % 2 == 0)     # 跨行业奇偶错位→ρ̄ 证据(#8)

    def run(ev, kw, pp=None, **extra):
        return rn.run_study(SyntheticReader(p, e), (pp or pap20), benchmark_mode="market",
                            events=ev, **kw, **extra)

    _orig_verdict = rn._verdict
    _calls = {"n": 0}

    def _counting_verdict(*a, **k):
        _calls["n"] += 1
        return _orig_verdict(*a, **k)

    # ── #7(前半):signed 全跑 _verdict 计数攻击=恰顶层 1 次 ─────────────────────────
    rn._verdict = _counting_verdict
    try:
        res_down = run(ev_down, EXP20_KW)
    finally:
        rn._verdict = _orig_verdict
    check("#7攻击:signed+direction 全跑 _verdict 恰调用 1 次(=顶层;诊断路径零调用)",
          _calls["n"], 1)
    res_up = run(ev_up, EXP20_KW)
    res_mix = run(ev_mix, EXP20_KW)
    raw_down = run(ev_down, RAW_KW)
    raw_up = run(ev_up, RAW_KW)
    raw_mix = run(ev_mix, RAW_KW)

    mw_d, mw_u, mw_m = (r["car"]["main_window"] for r in (res_down, res_up, res_mix))
    rmw_d, rmw_u, rmw_m = (r["car"]["main_window"] for r in (raw_down, raw_up, raw_mix))

    # ── #1/#2 signed 同向归一/反向(事件级逐 τ,先于聚合)──────────────────────────────
    STATS = ("caar", "adj_bmp_car", "bmp_car", "naive_t", "csar_mean", "csar_sd", "kp_factor", "n")
    check("#1 up=+1 恒等:all-up signed 主窗统计与 raw 逐项相等",
          all(mw_u[k] == rmw_u[k] for k in STATS), True)
    aar_s = [x["aar"] for x in res_down["per_tau"]["by_tau"]]
    aar_r = [x["aar"] for x in raw_down["per_tau"]["by_tau"]]
    check("#1/#2 down=−1 逐τ精确翻转:all-down 逐τ AAR == −raw AAR(先于聚合的事件级作用)",
          all(abs(a + b) < 1e-15 for a, b in zip(aar_s, aar_r)) and len(aar_s) > 0, True)
    check("#2 反向归一:all-down signed CAAR == −raw CAAR(raw 正超额→signed 负=逆修正方向)",
          (abs(mw_d["caar"] + rmw_d["caar"]) < 1e-15, mw_d["caar"] < 0 < rmw_d["caar"]),
          (True, True))
    check("#2 ADJ-BMP 主检验统计量同步翻转(非展示层翻转)",
          abs(mw_d["adj_bmp_car"] + rmw_d["adj_bmp_car"]) < 1e-12, True)

    # ── #8 signed 输入实改证明(与"只改最终 CAAR"的假实现可区分)───────────────────────
    check("#8 估计期残差实改:混合方向 ρ̄(行业内,est_ar_by_date 事件间相关)≠ raw ρ̄",
          res_mix["n_eff_rho"]["rho_bar"] != raw_mix["n_eff_rho"]["rho_bar"], True)
    rk_s = res_mix["robustness"]["corrado_rank"]["by_tau"][0]["t_rank"]
    rk_r = raw_mix["robustness"]["corrado_rank"]["by_tau"][0]["t_rank"]
    check("#8 秩输入实改:混合方向 τ0 秩统计量 ∉ {raw, −raw}(整序列重排,非末端翻转)",
          rk_s != rk_r and rk_s != -rk_r, True)
    check("#8 混合方向 CAAR ∉ {raw, −raw}(逐事件符号,展示层翻转不可及)",
          mw_m["caar"] != rmw_m["caar"] and mw_m["caar"] != -rmw_m["caar"], True)
    check("#8 csar_sd 不因乘 ±1 改变(PAP 原文:标准差数值不变,方向经分子作用)",
          mw_d["csar_sd"] == rmw_d["csar_sd"], True)
    rkd_s = res_down["robustness"]["corrado_rank"]["by_tau"][0]["t_rank"]
    rkd_r = raw_down["robustness"]["corrado_rank"]["by_tau"][0]["t_rank"]
    check("#8 all-down 秩统计量=−raw(估计窗+事件窗全序列翻转的秩镜像)",
          abs(rkd_s + rkd_r) < 1e-12, True)

    # ── #7(后半)raw 诊断层:零判决+消费 raw 平行对象 ────────────────────────────────
    dd = res_mix["diagnostic_dimensions"]
    check("#7 direction 单轴在场,层=up/down", sorted(dd["dims"].keys()) == ["direction"]
          and sorted(dd["dims"]["direction"]["layers"].keys()) == ["down", "up"], True)

    def _scan_key(obj, key):
        n_ = 0
        if isinstance(obj, dict):
            for k, v in obj.items():
                n_ += (k == key) + _scan_key(v, key)
        elif isinstance(obj, list):
            for v in obj:
                n_ += _scan_key(v, key)
        return n_

    def _scan_values(obj, vals):
        n_ = 0
        if isinstance(obj, dict):
            for v in obj.values():
                n_ += _scan_values(v, vals)
        elif isinstance(obj, list):
            for v in obj:
                n_ += _scan_values(v, vals)
        elif isinstance(obj, str):
            n_ += obj in vals
        return n_

    check("#7 诊断子树递归:零 verdict/verdict_note 键",
          (_scan_key(dd, "verdict"), _scan_key(dd, "verdict_note")), (0, 0))
    check("#7 诊断子树递归:零 SIG/NOT_SIG/AMBIGUOUS/INSUFFICIENT 分类值",
          _scan_values(dd["dims"], {"SIG", "NOT_SIG", "AMBIGUOUS", "INSUFFICIENT"}), 0)
    check("#7 display_basis=raw AR 声明在场(冻结 PAP v2)",
          dd.get("display_basis", "").startswith("raw AR"), True)
    check("#7 诊断层消费 raw 平行对象:signed 跑与 raw 跑诊断块逐字节同(主检验 signed 不外溢)",
          json.dumps(dd["dims"], sort_keys=True, default=str)
          == json.dumps(raw_mix["diagnostic_dimensions"]["dims"], sort_keys=True, default=str),
          True)

    # ── #13 集成三态 + #14 四态零判决影响 ────────────────────────────────────────────
    check("#13集成:all-up→SIG+ALIGNED / all-down→SIG+REVERSED",
          (res_up["verdict"], res_up["effect_alignment"]["value"],
           res_down["verdict"], res_down["effect_alignment"]["value"]),
          ("SIG", "ALIGNED", "SIG", "REVERSED"))
    res_ins = run(ev_down[:5], EXP20_KW)
    check("#13集成:INSUFFICIENT→UNAVAILABLE(统计量在场也不得猜方向)",
          (res_ins["verdict"], res_ins["effect_alignment"]["value"]), ("INSUFFICIENT", "UNAVAILABLE"))
    check("#13 effect_alignment 随主窗报告+角色=CONTEXT(field_roles 逐字)",
          (mw_d["effect_alignment"], mw_d["field_roles"]["effect_alignment"],
           res_down["effect_alignment"]["role"]), ("REVERSED", "CONTEXT", "CONTEXT"))
    for nm, r_ea, ev_, kw_ in (("all-down/REVERSED", res_down, ev_down, EXP20_KW),
                               ("all-up/ALIGNED", res_up, ev_up, EXP20_KW),
                               ("insufficient/UNAVAILABLE", res_ins, ev_down[:5], EXP20_KW)):
        r_off = run(ev_, dict(kw_, effect_alignment_source=None))
        check(f"#14 {nm}:alignment 开/关顶层 verdict 逐字节同(四态不产生不改变判决)",
              (r_ea["verdict"] == r_off["verdict"],
               r_ea["verdict_note"].startswith(r_off["verdict_note"])), (True, True))
        check(f"#14 {nm}:关闭 alignment → 零 effect_alignment 键(默认零新键)",
              _scan_key(r_off, "effect_alignment"), 0)

    # ── #3 SIG+REVERSED 措辞攻击(报告层)────────────────────────────────────────────
    rend_down = report_mod.render(res_down)
    check("#3 SIG+REVERSED:报告'支持'类措辞零命中", rend_down.count("支持"), 0)
    check("#3 SIG+REVERSED:强制警示句在场(显著证伪,禁作方向假设成立解读)",
          ("禁作方向假设成立解读" in rend_down, "SIG+ALIGNED" in rend_down), (True, False))
    check("#3 SIG+REVERSED:verdict_note 携带证伪句(runner 层已写入,非仅渲染层)",
          "显著证伪方向假设" in res_down["verdict_note"], True)
    rend_up = report_mod.render(res_up)
    check("#3 对照 SIG+ALIGNED:上下文句在场且不含证伪警示",
          ("SIG+ALIGNED,PAP 解释边界" in rend_up, "禁作方向假设成立解读" in rend_up),
          (True, False))
    check("#3 effect_alignment 行=CONTEXT·非 verdict 字段(报告显式声明)",
          "effect_alignment=REVERSED(CONTEXT·非 verdict 字段" in rend_down, True)

    # ── reporting⑥ signed CAAR 与 ADJ-BMP 符号不一致→并列披露 ─────────────────────────
    rng = random.Random(9)      # 预注册种子:该赋向 caar>0 而 adj_bmp<0(施工探测锚定)
    ev_seed9 = [dataclasses.replace(x, event_type_layer=rng.choice(["up", "down"]))
                for x in base_events]
    res_s9 = run(ev_seed9, EXP20_KW)
    mw_s9 = res_s9["car"]["main_window"]
    check("⑥符号不一致案例在场(caar>0>adj_bmp;种子9预注册)",
          (mw_s9["caar"] > 0, mw_s9["adj_bmp_car"] < 0), (True, True))
    check("⑥并列披露句写入 verdict_note(不得择一解释)",
          "并列披露,不得择一解释" in res_s9["verdict_note"], True)

    # ── #12 flat 泄漏拒跑(主事件流白名单外值;CAR 与 verdict 前拒)──────────────────────
    def _attack(events_bad, name):
        calls = {"n": 0}

        def _cv(*a, **k):
            calls["n"] += 1
            return _orig_verdict(*a, **k)

        rn._verdict = _cv
        try:
            run(events_bad, EXP20_KW)
            got = "未拒"
        except ValueError:
            got = "ValueError"
        finally:
            rn._verdict = _orig_verdict
        check(f"#12 {name} → fail-closed 拒绝运行", got, "ValueError")
        check(f"#12 {name}:攻击下 _verdict() 调用次数=0(校验先于 CAR 与顶层判决)", calls["n"], 0)

    _attack([dataclasses.replace(ev, event_type_layer="flat") for ev in base_events],
            "flat 泄漏进主事件流")
    _attack([dataclasses.replace(ev, event_type_layer=None) for ev in base_events],
            "null 层泄漏")
    _attack([dataclasses.replace(ev, event_type_layer="unknown") for ev in base_events],
            "unknown 层泄漏")
    _attack([dataclasses.replace(ev, event_type_layer="") for ev in base_events],
            "空串层泄漏")
    _attack([dataclasses.replace(ev, event_type_layer="预喜") for ev in base_events],
            "旧层名(预喜)泄漏")
    _attack(ev_mix + [dataclasses.replace(ev_mix[0], event_id="A:badflat",
                                          event_type_layer="flat")],
            "合法样本混入单条 flat")
    pap20_noaxes = dict(synth_pap(), _family_trial=1, bias_statement=EXP20_BIAS)
    try:
        run(ev_mix, EXP20_KW, pp=pap20_noaxes)
        check("#12 PAP 缺 diagnostic_dimensions.axes.direction(白名单不逐项一致)→ 拒", "未拒", "ValueError")
    except ValueError:
        check("#12 PAP 缺 diagnostic_dimensions.axes.direction(白名单不逐项一致)→ 拒",
              "ValueError", "ValueError")
    pap20_badaxes = dict(synth_pap(), _family_trial=1, bias_statement=EXP20_BIAS,
                         diagnostic_dimensions={"axes": {"direction": ["up", "down", "flat"]}})
    try:
        run(ev_mix, EXP20_KW, pp=pap20_badaxes)
        check("#12 PAP 白名单多出 flat(与引擎不逐项一致)→ 拒", "未拒", "ValueError")
    except ValueError:
        check("#12 PAP 白名单多出 flat(与引擎不逐项一致)→ 拒", "ValueError", "ValueError")
    try:
        run(ev_mix, dict(EXP20_KW, direction_display="signed"))
        check("#12 direction_display 白名单外值(signed)→ 拒(冻结不留运行时选择)", "未拒", "ValueError")
    except ValueError:
        check("#12 direction_display 白名单外值(signed)→ 拒(冻结不留运行时选择)",
              "ValueError", "ValueError")

    # ── #9 pap_sha256_assert 逐字断言 ────────────────────────────────────────────────
    from taosha.experiment.pap import canonical_pap_sha256
    pap20_sha = canonical_pap_sha256(pap20)
    try:
        run(ev_mix, EXP20_KW, pap_sha256_assert="0" * 64)
        check("#9 错误 digest 断言 → fail-closed 拒", "未拒", "ValueError")
    except ValueError:
        check("#9 错误 digest 断言 → fail-closed 拒", "ValueError", "ValueError")
    res_sha = run(ev_mix, EXP20_KW, pap_sha256_assert=pap20_sha)
    check("#9 正确 digest 断言(=引擎重算值)→ 放行且结果同",
          json.dumps(res_sha, sort_keys=True, default=str)
          == json.dumps(res_mix, sort_keys=True, default=str), True)

    # ── premend_params 审计如实(exp20 三参数入册)───────────────────────────────────
    check("审计:premend_params 记 exp20 全参数(含 signed/display/alignment)",
          res_mix["audit"]["premend_params"],
          {"st_policy": "reject", "verdict_policy": "adj_bmp_main_only", "nfv_structured": True,
           "postpone_policy": "unified_announcement", "diagnostic_dims": ["direction"],
           "direction_signed_main": True, "direction_display": "raw",
           "effect_alignment_source": "adj_bmp_sign"})

    # ── 特别验证⑦:默认路径零新键零回归(e2e 逐字节基线=官方 harness 另跑)──────────────
    res_def1 = rn.run_study(SyntheticReader(p, e), pap, benchmark_mode="market")
    res_def2 = rn.run_study(SyntheticReader(p, e), pap, benchmark_mode="market")
    check("⑦默认路径双跑逐字节相等(确定性)",
          json.dumps(res_def1, sort_keys=True, default=str)
          == json.dumps(res_def2, sort_keys=True, default=str), True)
    check("⑦默认路径零 exp20 新键(effect_alignment/diagnostic_dimensions/premend_params)",
          (_scan_key(res_def1, "effect_alignment"), _scan_key(res_def1, "diagnostic_dimensions"),
           _scan_key(res_def1, "premend_params")), (0, 0, 0))
    rend_def = report_mod.render(res_def1)
    check("⑦默认渲染零 exp20 段落(标题/漏斗/alignment 行)",
          ("exp20 业绩预告修正" in rend_def, "事件生成漏斗" in rend_def,
           "effect_alignment=" in rend_def), (False, False, False))

    # ── report 真锚 fail-closed(exp20 标题承 exp8 先例)────────────────────────────────
    res_t = json.loads(json.dumps(res_mix, default=str))
    res_t["audit"]["earnings_revision_selection"] = {"counters": {}}
    try:
        report_mod.render(res_t)
        check("report:selection 在场但缺真实 study_snapshot 锚 → fail-closed", "未拒", "SystemExit")
    except SystemExit:
        check("report:selection 在场但缺真实 study_snapshot 锚 → fail-closed",
              "SystemExit", "SystemExit")
    res_t["audit"]["study_snapshot"] = {"snapshot_id": 1, "digest": "d" * 8}
    rend_t = report_mod.render(res_t)
    check("report:真锚在场 → exp20 标题+漏斗段渲染",
          ("exp20 业绩预告修正·signed 事件版" in rend_t, "exp20 事件生成漏斗" in rend_t),
          (True, True))

print("=" * 60)
print(f"verify_earnings_revision_engine: {N - FAIL}/{N} PASS")
sys.exit(1 if FAIL else 0)
