"""exp20 earnings_revision L2 规则攻击自检(冻结令 2026-07-18 深夜六 令三③;零 DB,合成域)。

预注册攻击 fixture 清单(交付档 §5+§7.3)本件覆盖规则层各组:
  #6 方向判定全分支:单边界回退该单值/两边界全空不可判 fail-closed/中点相等 flat 仅计数/
     同链同日多行标量不一致 fail-closed(白名单外值泄漏属引擎层,见 verify_earnings_revision_engine)。
  #11(规则半):flat 候选正常计数排除,不终止运行,主事件集不含 flat。
  另:fail-closed 六类逐类(孤儿/时序违例/多链归属/数值不可判/同日方向冲突/600856.SH 逐条留痕)、
  L2 确定性折叠(重复行)、研究期边界(含防御性 post 计数)、基准B=事件日前最近披露(非链首)、
  同日多链同向折叠+组成链审计/方向冲突整事件拒、行序无关确定性。
用法: python taosha/harness/verify_earnings_revision_rules.py
"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.compute.earnings_revision_rules import (          # noqa: E402
    FAIL_CLOSED_CLASSES, FC_CONFLICT, FC_MULTI_CHAIN, FC_ORPHAN, FC_TEMPORAL, FC_TICKER,
    FC_VALUE, RESEARCH_END, RESEARCH_START, day_scalar, select_revision_events, value_of,
)

FAIL = 0
N = 0


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    if not ok:
        FAIL += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


D = dt.date


def row(ts, ann, end, first, pmin, pmax):
    return {"ts_code": ts, "ann_date": ann, "end_date": end, "first_ann_date": first,
            "p_change_min": pmin, "p_change_max": pmax}


def chain(ts, end, first, *revs, first_vals=(0.0, 10.0)):
    """首披行 + 逐修正行((ann_date, pmin, pmax))。"""
    out = [row(ts, first, end, first, *first_vals)]
    for (ann, pmin, pmax) in revs:
        out.append(row(ts, ann, end, first, pmin, pmax))
    return out


# ── 冻结参数实物 ────────────────────────────────────────────────────────────────
check("冻结研究期=[2013-01-01, 2024-07-01)", (RESEARCH_START, RESEARCH_END),
      (D(2013, 1, 1), D(2024, 7, 1)))
check("fail-closed 六类键集(reporting②)", sorted(FAIL_CLOSED_CLASSES),
      sorted([FC_ORPHAN, FC_TEMPORAL, FC_MULTI_CHAIN, FC_VALUE, FC_CONFLICT, FC_TICKER]))

# ── #6 方向判定标量全分支(value_of/day_scalar)──────────────────────────────────
check("#6两边界均在→中点", value_of(10.0, 20.0), 15.0)
check("#6仅min在→回退该单值", value_of(-30.0, None), -30.0)
check("#6仅max在→回退该单值", value_of(None, 7.0), 7.0)
check("#6两边界全空→None(不可判,不猜不补)", value_of(None, None), None)
check("#6同日多行全可判且一致→标量", day_scalar([row("A", D(2020, 1, 1), None, None, 10.0, 20.0),
                                                row("A", D(2020, 1, 1), None, None, 15.0, 15.0)]),
      (15.0, None))
check("#6同日多行含不可判行→fail-closed(undecidable)",
      day_scalar([row("A", D(2020, 1, 1), None, None, 10.0, 20.0),
                  row("A", D(2020, 1, 1), None, None, None, None)]), (None, "undecidable"))
check("#6同日多行均可判但不一致→fail-closed(inconsistent)",
      day_scalar([row("A", D(2020, 1, 1), None, None, 10.0, 20.0),
                  row("A", D(2020, 1, 1), None, None, 0.0, 10.0)]), (None, "inconsistent"))

# ── 基础三链:up / down / flat(#11 规则半)─────────────────────────────────────────
E19, E20 = D(2019, 12, 31), D(2020, 12, 31)
rows_updown = (chain("000001.SZ", E19, D(2020, 1, 10), (D(2020, 4, 10), 10.0, 20.0))       # 5→15 up
               + chain("000002.SZ", E20, D(2021, 1, 8), (D(2021, 4, 2), -60.0, -40.0),
                       first_vals=(-30.0, None)))                                          # -30→-50 down
sel = select_revision_events(rows_updown)
check("up/down 基础链:事件 2、方向正确",
      (sel["counters"]["events_after_fold"],
       sorted((e["ts_code"], e["direction"]) for e in sel["events"])),
      (2, [("000001.SZ", "up"), ("000002.SZ", "down")]))
check("基础链零 fail-closed 零 flat",
      (sel["fail_closed"]["by_class"], sel["flat"]["chain_day_flat"]),
      ({c: 0 for c in FAIL_CLOSED_CLASSES}, 0))
check("基准B审计入 member_chains(baseline=首披 5.0,当前 15.0)",
      (sel["events"][0]["member_chains"][0]["baseline_value"],
       sel["events"][0]["member_chains"][0]["current_value"]), (5.0, 15.0))
check("event_id 形制=ts:yyyymmdd", sel["events"][0]["event_id"], "000001.SZ:20200410")

# #11 flat 候选:中点相等 → 合法分类,计数后排除,不终止、其余事件照常产出
rows_flat = rows_updown + chain("000003.SZ", E20, D(2021, 1, 9), (D(2021, 3, 9), 5.0, 5.0),
                                first_vals=(0.0, 10.0))                                    # 5→5 flat
sel = select_revision_events(rows_flat)
check("#11 flat=合法分类:计数块=1(按年)、不终止",
      (sel["flat"]["chain_day_flat"], sel["flat"]["by_year"]), (1, {"2021": 1}))
check("#11 flat 排除出主事件集,up/down 照常",
      (sel["counters"]["events_after_fold"],
       all(e["direction"] in ("up", "down") for e in sel["events"])), (2, True))
check("#11 flat 不入 fail-closed(非拒跑事由)",
      sel["fail_closed"]["by_class"], {c: 0 for c in FAIL_CLOSED_CLASSES})

# ── fail-closed 六类逐类 ─────────────────────────────────────────────────────────
# ①孤儿修正:链无首披行(修正行在,first_ann_date 所指行缺席)
sel = select_revision_events([row("000004.SZ", D(2020, 4, 10), E19, D(2020, 1, 10), 10.0, 20.0)])
check("①孤儿(链无首披行)→fail-closed 逐类计数",
      (sel["fail_closed"]["by_class"][FC_ORPHAN], sel["counters"]["events_after_fold"]), (1, 0))
# ②时序违例:ann_date < first_ann_date
sel = select_revision_events(rows_updown
                             + [row("000005.SZ", D(2020, 1, 5), E19, D(2020, 1, 10), 1.0, 2.0)])
check("②时序违例(ann<first)→fail-closed,其余照常",
      (sel["fail_closed"]["by_class"][FC_TEMPORAL], sel["counters"]["events_after_fold"]), (1, 2))
# ③同期多链归属不明:同 (ts,end) 两个 first_ann_date
rows_mc = (chain("000006.SZ", E19, D(2020, 1, 10), (D(2020, 4, 10), 10.0, 20.0))
           + chain("000006.SZ", E19, D(2020, 2, 10), (D(2020, 5, 10), 30.0, 40.0)))
sel = select_revision_events(rows_mc)
check("③同期多链(同 ts,end 双 first)→归属不明,两链日全拒",
      (sel["fail_closed"]["by_class"][FC_MULTI_CHAIN], sel["counters"]["events_after_fold"]), (2, 0))
# ④数值不可判:当前行全空 / 基准行全空(子因分记)
sel = select_revision_events(chain("000007.SZ", E19, D(2020, 1, 10), (D(2020, 4, 10), None, None)))
check("④当前值不可判→fail-closed(子因 current_undecidable)",
      (sel["fail_closed"]["by_class"][FC_VALUE],
       sel["fail_closed"]["value_undecidable_sub"]["current_undecidable"]), (1, 1))
sel = select_revision_events(chain("000008.SZ", E19, D(2020, 1, 10), (D(2020, 4, 10), 10.0, 20.0),
                                   first_vals=(None, None)))
check("④基准B不可判→fail-closed(子因 baseline_undecidable)",
      (sel["fail_closed"]["by_class"][FC_VALUE],
       sel["fail_closed"]["value_undecidable_sub"]["baseline_undecidable"]), (1, 1))
# ⑤同日方向冲突:同 (ts,ann_date) 两链一 up 一 down → 整市场事件拒
rows_cf = (chain("000009.SZ", E19, D(2020, 1, 10), (D(2020, 4, 10), 10.0, 20.0))            # up
           + chain("000009.SZ", E20, D(2020, 2, 10), (D(2020, 4, 10), -60.0, -40.0),
                   first_vals=(-10.0, 0.0)))                                                # down 同日
sel = select_revision_events(rows_cf)
check("⑤同日方向冲突→整事件 fail-closed(按市场事件计 1)",
      (sel["fail_closed"]["by_class"][FC_CONFLICT], sel["fold_audit"]["conflict_events"],
       sel["fold_audit"]["conflict_chain_days"], sel["counters"]["events_after_fold"]),
      (1, 1, 2, 0))
# ⑤bis flat 不参与冲突判定:同日一 up 一 flat → up 成事件,flat 只计数
rows_uf = (chain("000010.SZ", E19, D(2020, 1, 10), (D(2020, 4, 10), 10.0, 20.0))            # up
           + chain("000010.SZ", E20, D(2020, 2, 10), (D(2020, 4, 10), 5.0, 5.0),
                   first_vals=(0.0, 10.0)))                                                 # flat 同日
sel = select_revision_events(rows_uf)
check("⑤bis flat 不属方向不参与冲突:up 成事件+flat 计数",
      (sel["counters"]["events_after_fold"], sel["events"][0]["direction"],
       sel["flat"]["chain_day_flat"], sel["fail_closed"]["by_class"][FC_CONFLICT]),
      (1, "up", 1, 0))
# ⑥600856.SH 单票 fail-closed 逐条留痕
sel = select_revision_events(chain("600856.SH", E19, D(2020, 1, 10), (D(2020, 4, 10), 10.0, 20.0)))
check("⑥600856.SH→fail-closed+逐条留痕",
      (sel["fail_closed"]["by_class"][FC_TICKER], len(sel["itemized_600856"]),
       sel["itemized_600856"][0]["ann_date"]), (1, 1, "2020-04-10"))

# ── 基准B=事件日前最近披露(非链首)───────────────────────────────────────────────
rows_b = chain("000011.SZ", E19, D(2020, 1, 10),
               (D(2020, 2, 10), 20.0, 20.0),      # 修正1: 5→20 up
               (D(2020, 4, 10), 10.0, 10.0))      # 修正2: 基准=修正1(20),10<20 → down
sel = select_revision_events(rows_b)
ev2 = [e for e in sel["events"] if e["ann_date"] == D(2020, 4, 10)][0]
check("基准B=前一修正(20.0)非链首(5.0)→修正2 判 down",
      (ev2["direction"], ev2["member_chains"][0]["baseline_ann_date"],
       ev2["member_chains"][0]["baseline_value"]), ("down", "2020-02-10", 20.0))
check("同链两修正=两市场事件(链日各判)", sel["counters"]["events_after_fold"], 2)

# ── 研究期边界(事件锚 ann_date;基准回看不受限)─────────────────────────────────
rows_p = (chain("000012.SZ", D(2012, 12, 31), D(2012, 11, 1), (D(2012, 12, 20), 10.0, 20.0))  # pre
          + chain("000013.SZ", E19, D(2012, 12, 20), (D(2013, 1, 1), 10.0, 20.0)))            # 界上
sel = select_revision_events(rows_p)
check("研究期:2012 事件剔(pre 计数)、2013-01-01 界上入且基准可回看 2012 首披",
      (sel["counters"].get("candidate_rows_pre_research_period", 0),
       sel["counters"]["events_after_fold"], sel["events"][0]["ann_date"]),
      (1, 1, D(2013, 1, 1)))
sel = select_revision_events(chain("000014.SZ", E20, D(2024, 1, 10), (D(2024, 7, 1), 10.0, 20.0)))
check("研究期:2024-07-01 界上剔(防御性 post 计数;视图 holdout 已焊死)",
      (sel["counters"].get("candidate_rows_post_research_period", 0),
       sel["counters"]["events_after_fold"]), (1, 0))

# ── L2 确定性折叠:同日逐字段重复行仅折叠、计数留痕 ─────────────────────────────
sel = select_revision_events(rows_updown + [dict(rows_updown[1])])   # 复制一条修正行
check("重复行折叠:collapsed=1,事件不重复",
      (sel["counters"]["duplicate_rows_collapsed"], sel["counters"]["events_after_fold"]), (1, 2))

# ── 同日多链同方向折叠:一个市场事件+组成链审计 ─────────────────────────────────
rows_fold = (chain("000015.SZ", E19, D(2020, 1, 10), (D(2020, 4, 10), 10.0, 20.0))
             + chain("000015.SZ", E20, D(2020, 2, 10), (D(2020, 4, 10), 30.0, 40.0),
                     first_vals=(0.0, 10.0)))     # 两链同日同向 up
sel = select_revision_events(rows_fold)
check("同日多链同向→折叠一个市场事件(每键唯一)+组成链审计=2 条",
      (sel["counters"]["events_after_fold"], sel["fold_audit"]["events_folded_from_multi_chain"],
       len(sel["events"][0]["member_chains"])), (1, 1, 2))
check("组成链审计含两条链的 end_date(升序钉死)",
      [m["end_date"] for m in sel["events"][0]["member_chains"]],
      ["2019-12-31", "2020-12-31"])

# ── 行序无关确定性(输入乱序 → 输出逐字节同)────────────────────────────────────
big = rows_flat + rows_b + rows_fold + rows_p
a = json.dumps(select_revision_events(big), ensure_ascii=False, sort_keys=True, default=str)
b = json.dumps(select_revision_events(list(reversed(big))), ensure_ascii=False, sort_keys=True,
               default=str)
check("行序无关确定性:正序/逆序输入结果逐字节同", a == b, True)

# ── 缺链锚行:不进候选不作基准,计数留痕 ─────────────────────────────────────────
sel = select_revision_events(rows_updown + [row("000016.SZ", D(2020, 4, 10), None, None, 1.0, 2.0)])
check("缺链锚(first/end 空)行:计数留痕、不产事件不干扰",
      (sel["counters"].get("rows_missing_chain_anchor", 0), sel["counters"]["events_after_fold"]),
      (1, 2))

print("=" * 60)
print(f"verify_earnings_revision_rules: {N - FAIL}/{N} PASS")
sys.exit(1 if FAIL else 0)
