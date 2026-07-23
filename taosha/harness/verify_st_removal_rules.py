"""exp12 st_removal 规则层预注册攻击 fixture(冻结令 2026-07-23 三节;零 DB,合成行)。

攻击面(令:退市双谓词/摘星排除/冲突与重复 fail-closed;+冻结 event_def 全谓词):
  ① 名称定级谓词:ST 变体(*ST/SST/S*ST/G*ST)/退市双格式(后缀%退+前缀退市%)/优先级
    退市>ST>普通(单名双命中)/空名 fail-closed;
  ② 完整撤销事件:ST→普通=事件;摘星 *ST→ST 非事件仅报数;戴星 ST→*ST 报数;
    ST→退(后缀)与 ST→退市(前缀)均非事件仅报数——**仅后缀谓词会把前缀退市名误判普通
    =假事件,双谓词修正为非事件**(窄闸实测 46 例泄漏的规则化);
  ③ 段位折叠:孪生行折叠/段边界=列表序(LEAD 等价)/start 缺失行计数/首段无前段;
  ④ fail-closed 六类:状态不可判(段内混名)/锚缺失/锚冲突(段内多 ann)/ann>start/
    研究期边界(2011-01-01 含,2024-07-01 不含)/事件键重复全剔不择一;
  ⑤ 漏斗恒等式+确定性双跑。
用法: python taosha/harness/verify_st_removal_rules.py
"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.compute.st_removal_rules import (                              # noqa: E402
    funnel_identity_ok, merge_selections, name_state, has_star,
    run_funnel, select_st_removal_events)

FAIL = 0
N = 0


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    if not ok:
        FAIL += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


def R(alias, start, ann):
    return {"alias": alias,
            "start_date": dt.date.fromisoformat(start) if start else None,
            "ann_date": dt.date.fromisoformat(ann) if ann else None}


# ── ① 名称定级谓词 ───────────────────────────────────────────────────────────
check("①ST 基本", name_state("ST丰华"), "st")
check("①*ST 变体", name_state("*ST海源"), "st")
check("①SST 变体(无星)", name_state("SST前锋"), "st")
check("①S*ST 变体", name_state("S*ST北亚"), "st")
check("①G*ST 变体", name_state("G*ST金城"), "st")
check("①普通名", name_state("万科A"), "normal")
check("①退市后缀(深市)", name_state("美都退"), "delist")
check("①退市前缀(沪市)——008 仅后缀谓词误判普通,双谓词修正", name_state("退市美都"), "delist")
check("①优先级 退市>ST(单名双命中)", name_state("退市ST甲"), "delist")
check("①优先级 后缀退>ST", name_state("ST甲退"), "delist")
check("①空名 fail-closed → unknown", name_state(""), "unknown")
check("①None 名 fail-closed → unknown", name_state(None), "unknown")
check("①星标判据(*ST/S*ST 命中,SST 不命中)",
      (has_star("*ST海源"), has_star("S*ST北亚"), has_star("SST前锋")), (True, True, False))

# ── ② 完整撤销 / 摘星 / 戴星 / 退市双谓词 ───────────────────────────────────
# A票: ST→普通,锚在研究期内 → 唯一事件
sel = run_funnel("000001.SZ", [R("ST丰华", "2012-01-10", "2012-01-06"),
                               R("丰华股份", "2015-06-10", "2015-06-08")])
check("②完整撤销=事件", (sel["counters"]["final_events"],
                          sel["events"][0]["ann_date"]), (1, "2015-06-08"))
check("②gap_days=2", sel["events"][0]["gap_days"], 2)

# 摘星 *ST→ST: 非事件,destar 报数(全史+窗内锚干净)
sel = run_funnel("000002.SZ", [R("*ST海源", "2012-01-10", "2012-01-06"),
                               R("ST海源", "2013-05-10", "2013-05-07")])
check("②摘星非事件仅报数", (sel["counters"]["final_events"], sel["counters"]["destar_all"],
                            sel["counters"]["destar_in_window_clean_anchor"]), (0, 1, 1))
# 摘星窗外(2010) → destar_all 计、窗内不计
sel = run_funnel("000002.SZ", [R("*ST甲", "2009-01-10", "2009-01-06"),
                               R("ST甲", "2010-05-10", "2010-05-07")])
check("②摘星窗外只计全史", (sel["counters"]["destar_all"],
                            sel["counters"]["destar_in_window_clean_anchor"]), (1, 0))
# 戴星 ST→*ST
sel = run_funnel("000003.SZ", [R("ST乙", "2012-01-10", "2012-01-06"),
                               R("*ST乙", "2013-05-10", "2013-05-07")])
check("②戴星报数非事件", (sel["counters"]["star_on_all"],
                          sel["counters"]["final_events"]), (1, 0))
# ST→退(后缀,深市)
sel = run_funnel("000004.SZ", [R("ST丙", "2012-01-10", "2012-01-06"),
                               R("丙退", "2015-06-10", "2015-06-08")])
check("②ST→退(后缀)非事件报数", (sel["counters"]["st_to_delist_all"],
                                 sel["counters"]["final_events"],
                                 sel["counters"]["removal_candidates"]), (1, 0, 0))
# ST→退市(前缀,沪市)——攻击:仅后缀谓词会误判 '退市丁'='normal' → 假事件;双谓词必须拒
sel = run_funnel("600001.SH", [R("ST丁", "2012-01-10", "2012-01-06"),
                               R("退市丁", "2015-06-10", "2015-06-08")])
check("②ST→退市(前缀)非事件报数(双谓词攻击拒)",
      (sel["counters"]["st_to_delist_all"], sel["counters"]["final_events"],
       sel["counters"]["removal_candidates"]), (1, 0, 0))
# 退市整理段后再改名 → 前段=delist 非 st,不构成候选
sel = run_funnel("600002.SH", [R("退市戊", "2015-01-10", "2015-01-08"),
                               R("戊科技", "2016-06-10", "2016-06-08")])
check("②退市段→普通 非候选(前段非 ST)", sel["counters"]["removal_candidates"], 0)

# ── ③ 段位折叠 ──────────────────────────────────────────────────────────────
# 孪生行(同 start 同名同锚)折叠为一段;三段两转换
sel = run_funnel("000005.SZ", [R("ST己", "2012-01-10", "2012-01-06"),
                               R("ST己", "2012-01-10", "2012-01-06"),
                               R("己股份", "2015-06-10", "2015-06-08"),
                               R("己新材", "2018-03-10", "2018-03-07")])
check("③孪生折叠(4行→3段2转换)", (sel["counters"]["input_rows"], sel["counters"]["segments"],
                                   sel["counters"]["transitions_with_prev"]), (4, 3, 2))
check("③折叠后事件唯一", sel["counters"]["final_events"], 1)
# start 缺失行计数、不折叠
sel = run_funnel("000006.SZ", [R("ST庚", None, "2012-01-06"),
                               R("ST庚", "2012-01-10", "2012-01-06"),
                               R("庚实业", "2015-06-10", "2015-06-08")])
check("③start 缺失行计数留痕", (sel["counters"]["start_missing_rows"],
                                sel["counters"]["segments"],
                                sel["counters"]["final_events"]), (1, 2, 1))
# 首段无前段
sel = run_funnel("000007.SZ", [R("辛股份", "2012-01-10", "2012-01-06")])
check("③首段无前段(1段0转换0候选)", (sel["counters"]["segments"],
                                     sel["counters"]["transitions_with_prev"],
                                     sel["counters"]["removal_candidates"]), (1, 0, 0))

# ── ④ fail-closed 六类 ──────────────────────────────────────────────────────
# 状态不可判:后段孪生混名(普通+ST)
sel = run_funnel("000008.SZ", [R("ST壬", "2012-01-10", "2012-01-06"),
                               R("壬股份", "2015-06-10", "2015-06-08"),
                               R("ST壬", "2015-06-10", "2015-06-08")])
check("④状态不可判 fail-closed(候选计入+剔除)",
      (sel["counters"]["removal_candidates"],
       sel["counters"]["state_unjudgeable_fail_closed"],
       sel["counters"]["final_events"]), (1, 1, 0))
check("④不可判逐条留痕", sel["rejects"][0]["reason"], "state_unjudgeable_fail_closed")
# 前段混名(ST+普通)同不可判
sel = run_funnel("000008.SZ", [R("ST壬", "2012-01-10", "2012-01-06"),
                               R("壬集团", "2012-01-10", "2012-01-06"),
                               R("壬股份", "2015-06-10", "2015-06-08")])
check("④前段混名同不可判", (sel["counters"]["state_unjudgeable_fail_closed"],
                            sel["counters"]["final_events"]), (1, 0))
# 锚缺失(ann 全空,覆盖边界留痕)
sel = run_funnel("000009.SZ", [R("ST癸", "2009-01-10", None),
                               R("癸股份", "2010-03-10", None)])
check("④锚缺失留痕", (sel["counters"]["anchor_missing"],
                      sel["counters"]["final_events"]), (1, 0))
# 锚冲突(段内孪生 distinct ann>1)
sel = run_funnel("000010.SZ", [R("ST子", "2012-01-10", "2012-01-06"),
                               R("子股份", "2015-06-10", "2015-06-08"),
                               R("子股份", "2015-06-10", "2015-06-05")])
check("④锚冲突 fail-closed", (sel["counters"]["anchor_conflict_fail_closed"],
                              sel["counters"]["final_events"]), (1, 0))
# ann>start 校验
sel = run_funnel("000011.SZ", [R("ST丑", "2012-01-10", "2012-01-06"),
                               R("丑股份", "2015-06-10", "2015-06-12")])
check("④ann>start fail-closed", (sel["counters"]["ann_after_start_fail_closed"],
                                 sel["counters"]["final_events"]), (1, 0))
# ann==start(gap0)合法
sel = run_funnel("000011.SZ", [R("ST丑", "2012-01-10", "2012-01-06"),
                               R("丑股份", "2015-06-10", "2015-06-10")])
check("④ann==start 合法(gap0)", (sel["counters"]["final_events"],
                                 sel["events"][0]["gap_days"]), (1, 0))
# 研究期边界:2011-01-01 含 / 2024-07-01 不含 / 2010 期外 / 2024-06-30 含
for ann, start, want_in in (("2011-01-01", "2011-01-04", 1), ("2024-06-30", "2024-07-02", 1),
                            ("2024-07-01", "2024-07-03", 0), ("2010-06-01", "2010-06-03", 0)):
    sel = run_funnel("000012.SZ", [R("ST寅", "2009-01-10", "2009-01-06"),
                                   R("寅股份", start, ann)])
    check(f"④研究期边界 ann={ann} → {'入' if want_in else '期外'}",
          (sel["counters"]["final_events"],
           sel["counters"]["out_of_period"]), (want_in, 1 - want_in))
# 事件键重复:同票两段同 ann 全剔不择一
sel = run_funnel("000013.SZ", [R("ST卯", "2012-01-10", "2012-01-06"),
                               R("卯股份", "2015-06-10", "2015-06-08"),
                               R("ST卯", "2016-01-10", "2016-01-06"),
                               R("卯科技", "2016-06-10", "2015-06-08")])
check("④事件键重复全剔不择一", (sel["counters"]["duplicate_event_keys"],
                                sel["counters"]["event_key_duplicate_fail_closed"],
                                sel["counters"]["final_events"]), (1, 2, 0))
check("④重复逐条留痕(2条同reason)",
      sorted(r["reason"] for r in sel["rejects"]),
      ["event_key_duplicate_fail_closed", "event_key_duplicate_fail_closed"])

# ── ⑤ 恒等式 + 聚合 + 确定性 ────────────────────────────────────────────────
ALL = [
    ("000001.SZ", [R("ST丰华", "2012-01-10", "2012-01-06"),
                   R("丰华股份", "2015-06-10", "2015-06-08")]),
    ("000002.SZ", [R("*ST海源", "2012-01-10", "2012-01-06"),
                   R("ST海源", "2013-05-10", "2013-05-07")]),
    ("600001.SH", [R("ST丁", "2012-01-10", "2012-01-06"),
                   R("退市丁", "2015-06-10", "2015-06-08")]),
    ("000010.SZ", [R("ST子", "2012-01-10", "2012-01-06"),
                   R("子股份", "2015-06-10", "2015-06-08"),
                   R("子股份", "2015-06-10", "2015-06-05")]),
    ("000013.SZ", [R("ST卯", "2012-01-10", "2012-01-06"),
                   R("卯股份", "2015-06-10", "2015-06-08"),
                   R("ST卯", "2016-01-10", "2016-01-06"),
                   R("卯科技", "2016-06-10", "2015-06-08")]),
]
merged = merge_selections([select_st_removal_events(ts, rows) for ts, rows in ALL])
check("⑤跨票聚合恒等式", funnel_identity_ok(merged["counters"]), True)
check("⑤跨票计数(候选4=事件1+锚冲突1+键重复2)",
      (merged["counters"]["removal_candidates"], merged["counters"]["final_events"],
       merged["counters"]["anchor_conflict_fail_closed"],
       merged["counters"]["event_key_duplicate_fail_closed"]), (4, 1, 1, 2))
check("⑤reject_reasons 计数",
      merged["reject_reasons"],
      {"anchor_conflict_fail_closed": 1, "event_key_duplicate_fail_closed": 2})
d1 = json.dumps(merge_selections([select_st_removal_events(ts, r) for ts, r in ALL]),
                sort_keys=True, default=str)
d2 = json.dumps(merge_selections([select_st_removal_events(ts, r) for ts, r in ALL]),
                sort_keys=True, default=str)
check("⑤确定性双跑逐字节同", d1 == d2, True)

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
