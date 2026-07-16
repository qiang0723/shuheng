"""holder_sell 事件规则攻击性 fixture 自检(规则 v2,人裁 2026-07-16;零DB;唯一文件读取=冻结裁决表实物)。
三证:①真首次收(含对抗性负语境) ②六类全拒 ③同计划自动去重仅 id/强键/裁决表(A5)。
v2 增:A1–A3 真实泄漏反例(语料实物标题)/A4 PIT 归属/A5 中键降诊断+裁决表/A6 fwp 门(人令:不只测合成标题)。
改判注记(人裁 2026-07-16,非删除):v1"暨字但无污染词→FIRST"改 CLS_FWP(A6);v1 中键 30 日自动剔改
仅诊断(A5);v1 跨票同 id 保输入序改 PIT 归属 fail-closed(A4)。
用法: python taosha/harness/verify_holder_sell_rules.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.compute.holder_sell_rules import (  # noqa: E402
    ADJUDICATION_FILE, CLS_COMBO, CLS_FIRST, CLS_FWP, CLS_HALFWAY, CLS_PROGRESS,
    CLS_PROGRESS_REACHED, CLS_RESULT, CLS_REVISION, CLS_SUSPECT, CLS_TERMINATION,
    classify_event_title, load_adjudication, select_first_events)

FAIL = 0
N = 0


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    if not ok:
        FAIL += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


# ── 证一:真首次收(正例,含对抗性负语境;含 v2 真实语料正例) ─────────────────
check("首次·标准预披露", classify_event_title("关于持股5%以上股东减持股份计划的预披露公告"), CLS_FIRST)
check("首次·计划公告无预披露字样", classify_event_title("股东减持股份计划公告"), CLS_FIRST)
check("首次·提示性公告", classify_event_title("关于持股5%以上股东股份减持计划的提示性公告"), CLS_FIRST)
check("首次·对抗:限售期满后减持(负语境掩码)",
      classify_event_title("部分董事及高级管理人员股权激励所获股票限售期满后减持股份计划的公告"), CLS_FIRST)
check("首次·对抗:锁定期届满后拟减持",
      classify_event_title("关于控股股东所持股份锁定期届满后减持计划的预披露公告"), CLS_FIRST)
check("首次·对抗:股权激励持有期满后减持计划",
      classify_event_title("董事高级管理人员股权激励所获股票持有期满后集中竞价减持股份计划公告"), CLS_FIRST)
check("首次·A1对抗:限售期到期后减持(掩码扩'到期')",
      classify_event_title("关于控股股东限售期到期后减持股份计划的预披露公告"), CLS_FIRST)
check("首次·A1对抗:纾困资管计划到期披露新减持计划(语料实物)",
      classify_event_title("关于公司持股5%以上股东资管7号纾困计划到期按规定披露集中竞价减持股份计划公告"), CLS_FIRST)
check("首次·A1对抗:资产管理计划到期减持(语料实物,非计划结果语境)",
      classify_event_title("关于兴证资管鑫众25号集合资产管理计划到期减持公司股份的公告"), CLS_FIRST)
check("首次·A2对抗:拟减持达到2%(新计划表述不判进展)",
      classify_event_title("关于股东拟减持达到2%股份的预披露公告"), CLS_FIRST)
check("首次·A2对抗:不超过1%=计划上限非进展(语料实物300184)",
      classify_event_title("关于持股5%以上股东、董事减持公司股份不超过1%的预披露公告"), CLS_FIRST)
check("首次·A3对抗:无关修正语境不误杀(修正锚定减持语境)",
      classify_event_title("关于修正后土地评估事项暨股东减持计划的公告"), CLS_FIRST)
check("拒·对抗:计划结果(非紧邻)仍兜底剔除",
      classify_event_title("上海电力股份有限公司股东减持股份计划结果公告"), CLS_SUSPECT)

# ── 证二:六类全拒(反例;v2 增真实泄漏行) ────────────────────────────────────
check("拒·时间过半", classify_event_title("关于股东减持计划时间过半的公告"), CLS_HALFWAY)
check("拒·数量过半", classify_event_title("关于持股5%以上股东减持股份达到1%暨减持计划减持数量过半的公告"), CLS_HALFWAY)
check("拒·进展(换源防线)", classify_event_title("关于控股股东减持计划实施进展的公告"), CLS_PROGRESS)
check("拒·实施情况", classify_event_title("关于股东减持计划实施情况的公告"), CLS_PROGRESS)
check("拒·计划期满", classify_event_title("关于公司持股5%以上股东股份减持计划期满的公告"), CLS_RESULT)
check("拒·期满未减持", classify_event_title("关于董事、高级管理人员减持计划期满未减持公司股份的公告"), CLS_RESULT)
check("拒·减持结果", classify_event_title("旭升集团控股股东提前结束减持计划暨减持股份结果公告"), CLS_TERMINATION)
check("拒·减持完毕", classify_event_title("关于公司高级管理人员减持股份计划完毕的公告"), CLS_RESULT)
check("拒·提前终止", classify_event_title("关于公司控股股东减持计划提前终止的公告"), CLS_TERMINATION)
check("拒·更正", classify_event_title("关于《持股5%以上股东减持预披露公告》的更正公告"), CLS_REVISION)
check("拒·修订", classify_event_title("关于股东减持计划的修订公告"), CLS_REVISION)
check("拒·补充", classify_event_title("关于股东减持股份计划的补充公告"), CLS_REVISION)
check("拒·延期", classify_event_title("关于股东减持计划延期实施的公告"), CLS_REVISION)
check("拒·A1真实泄漏:减持计划到期(语料81行型,002426同键行)",
      classify_event_title("关于控股股东前次股份减持计划到期的公告"), CLS_RESULT)
check("拒·A1真实泄漏:董监高减持公司股份计划到期(语料实物,宽间隔)",
      classify_event_title("关于公司董事、高级管理人员减持公司股份计划到期的公告"), CLS_RESULT)
check("拒·A1真实泄漏:减持所持其他上市公司股份计划到期(语料实物)",
      classify_event_title("天通股份关于减持公司所持其他上市公司股份计划到期的公告"), CLS_RESULT)
check("拒·A1兜底:未锚定'到期'→suspect不静默",
      classify_event_title("关于股东到期事项暨减持相关事宜的公告"), CLS_SUSPECT)
check("拒·A2真实泄漏:达到1%无预披露(语料300736)",
      classify_event_title("关于实际控制人之一致行动人减持计划减持股份比例达到1%的公告"), CLS_PROGRESS_REACHED)
check("拒·A2:累计超过N%无预披露",
      classify_event_title("关于控股股东减持公司股份累计超过1%的公告"), CLS_PROGRESS_REACHED)
check("拒·A3真实泄漏:减持预披露的修正公告(语料300505)",
      classify_event_title("关于公司控股股东及部分股东减持股份预披露的修正公告"), CLS_REVISION)
check("拒·混合:终止暨后续预披露",
      classify_event_title("关于公司控股股东减持计划提前终止暨后续减持计划的预披露公告"), CLS_COMBO)
check("拒·混合:期满及未来预披露",
      classify_event_title("关于公司控股股东减持计划期满及未来减持计划预披露的公告"), CLS_COMBO)
check("拒·混合:真实并披含提前终止(语料002047,A6定义外)",
      classify_event_title("关于持股5%以上股东被动减持计划提前终止、后续被动减持计划预披露暨一致行动人持股比例变动超过1%的公告"),
      CLS_COMBO)
check("拒·兜底:非计划语境终止+预披露→suspect不静默",
      classify_event_title("关于终止募投项目暨控股股东股份减持计划预披露的公告"), CLS_SUSPECT)
check("拒·兜底:泛完成词→suspect",
      classify_event_title("关于完成工商变更登记暨股东减持计划的公告"), CLS_SUSPECT)

# ── A6:first_with_progress 判类(真实语料标题) ────────────────────────────────
check("fwp·达到1%及后续预披露(语料002298)",
      classify_event_title("关于控股股东减持股份达到1%及后续减持股份预披露的公告"), CLS_FWP)
check("fwp·词序倒装:预披露暨达到1%(语料300256)",
      classify_event_title("关于持股5%以上股东被动减持的预披露暨减持股份达到1%的公告"), CLS_FWP)
check("fwp·超过1%暨预披露(语料000034)",
      classify_event_title("关于股东减持比例超过1%暨减持股份的预披露公告"), CLS_FWP)
check("fwp·改判注记:v1'暨字但无污染词→FIRST'按A6改CLS_FWP(人裁2026-07-16)",
      classify_event_title("关于股东减持股份达到1%暨减持计划的预披露公告"), CLS_FWP)
check("fwp·无预披露字面但含新计划指示(语料实物,A2原文'不含指示'才归进展;表外fail-closed)",
      classify_event_title("关于持股5%以上股东减持股份超过1%及未来减持计划的公告"), CLS_FWP)
check("fwp·暨后续减持计划(语料实物,同上)",
      classify_event_title("关于持股5%以上股东通过大宗交易减持公司股份超过1%暨后续减持计划的公告"), CLS_FWP)
check("拒·A2纯进展:达到1%无任何新计划指示(语料实物)",
      classify_event_title("关于股东减持计划减持股份比例达到1%的公告"), CLS_PROGRESS_REACHED)

# ── 证三:流水线(A4/A5/A6/强键/比例门/确定性) ────────────────────────────────
ROW = dict(ts_code="000001.SZ", stock_code="000001", holder_name="张三",
           reduce_ratio_max_pct=2.0, reduce_period_start="2023-02-01",
           reduce_period_end="2023-07-31", title="关于股东减持股份计划的预披露公告")


def row(**kw):
    r = dict(ROW)
    r.update(kw)
    return r


# 强键同计划隔日再披 → 仅首条(v1 行为不变)
res = select_first_events([
    row(announcement_id="A1", valid_time="2023-01-10T09:00:00+00:00"),
    row(announcement_id="A2", valid_time="2023-01-11T09:00:00+00:00"),
])
check("同计划强键:两公告→1事件", res["counters"]["events"], 1)
check("同计划强键:被剔理由", [x["reason"] for x in res["rejects"]], ["same_plan_strong_key"])
check("同计划强键:保最早", res["events"][0]["announcement_ids"], ["A1"])

# A5 改判:中键(票,股东,比例)30日内不再自动剔 → 两事件+诊断清单留痕(人裁 2026-07-16)
res = select_first_events([
    row(announcement_id="B1", valid_time="2023-01-10T09:00:00+00:00",
        reduce_period_start=None, reduce_period_end=None),
    row(announcement_id="B2", valid_time="2023-02-05T09:00:00+00:00",
        reduce_period_start=None, reduce_period_end=None),
    row(announcement_id="B3", valid_time="2023-06-01T09:00:00+00:00",
        reduce_period_start=None, reduce_period_end=None),
])
check("A5:中键30日内不自动剔(改判)→3事件", res["counters"]["events"], 3)
check("A5:零pair剔除", [x["reason"] for x in res["rejects"]], [])
check("A5:诊断清单捕获≤30日对", res["counters"]["midkey_diag_pairs"], 1)
check("A5:诊断对=(B1,B2)",
      (res["diagnostics"]["midkey_candidates_30d"][0]["prev_announcement_id"],
       res["diagnostics"]["midkey_candidates_30d"][0]["announcement_id"]), ("B1", "B2"))

# A5:裁决表在册对剔后续(same_plan/ambiguous 两理由)
ADJ = {"pair_drops": [
    {"drop": "B2", "keep": "B1", "verdict": "same_plan_adjudicated"},
    {"drop": "B3", "keep": "B1", "verdict": "ambiguous_possible_duplicate"},
], "first_with_progress": {}}
res = select_first_events([
    row(announcement_id="B1", valid_time="2023-01-10T09:00:00+00:00"),
    row(announcement_id="B2", valid_time="2023-02-05T09:00:00+00:00",
        reduce_period_start="2023-03-01", reduce_period_end="2023-08-31"),
    row(announcement_id="B3", valid_time="2023-06-01T09:00:00+00:00",
        reduce_period_start="2023-07-01", reduce_period_end="2023-12-31"),
], adjudication=ADJ)
check("A5:裁决表剔后续→1事件", res["counters"]["events"], 1)
check("A5:剔除理由=裁决表判定", sorted(x["reason"] for x in res["rejects"]),
      ["ambiguous_possible_duplicate", "same_plan_adjudicated"])
check("A5:保最早", res["events"][0]["announcement_ids"], ["B1"])

# 同日两股东两计划 → 均保留,合并为同一市场事件日(v1 行为不变)
res = select_first_events([
    row(announcement_id="C1", holder_name="张三", valid_time="2023-03-01T09:00:00+00:00"),
    row(announcement_id="C2", holder_name="李四", reduce_ratio_max_pct=3.0,
        valid_time="2023-03-01T10:00:00+00:00"),
])
check("同日双股东:1事件日", res["counters"]["events"], 1)
check("同日双股东:n_ann=2", res["events"][0]["n_ann"], 2)

# 比例门:未解析 fail-closed / 0.5%拒 / 恰1.0%过(v1 行为不变)
res = select_first_events([
    row(announcement_id="D1", reduce_ratio_max_pct=None, holder_name=None,
        valid_time="2023-04-01T09:00:00+00:00"),
    row(announcement_id="D2", reduce_ratio_max_pct=0.5, holder_name=None,
        valid_time="2023-04-02T09:00:00+00:00"),
    row(announcement_id="D3", reduce_ratio_max_pct=1.0, holder_name=None,
        valid_time="2023-04-03T09:00:00+00:00"),
])
check("比例门:仅≥1%成事件", res["counters"]["events"], 1)
check("比例门:剔除理由集",
      sorted(x["reason"] for x in res["rejects"]),
      ["ratio_below_gate", "ratio_unparsed_fail_closed"])

# A4 改判:跨票同id按公告日PIT上市窗归属(禁输入序;招商南油形状,真实aid)
LISTING = {"600087.SH": {"list_status": "D", "list_date": "1997-07-04", "delist_date": "2014-06-27"},
           "601975.SH": {"list_status": "L", "list_date": "2019-01-14", "delist_date": None}}
res = select_first_events([
    row(announcement_id="1208000738", stock_code="600087", ts_code="600087.SH",
        valid_time="2020-06-15T16:00:00+00:00"),
    row(announcement_id="1208000738", stock_code="601975", ts_code="601975.SH",
        valid_time="2020-06-15T16:00:00+00:00"),
], listing=LISTING)
check("A4:唯一PIT命中→1事件归601975", res["events"][0]["ts_code"], "601975.SH")
check("A4:conflict留痕pit_unique",
      res["conflicts"], [{"announcement_id": "1208000738", "resolution": "pit_unique",
                          "kept": "601975", "dropped": ["600087"]}])
check("A4:输入序首行(600087)被拒",
      [x["reason"] for x in res["rejects"]], ["pit_attribution_other_code"])
# 多命中 → fail-closed 全剔
L2 = {"600087.SH": {"list_status": "L", "list_date": "1997-07-04", "delist_date": None},
      "601975.SH": {"list_status": "L", "list_date": "2019-01-14", "delist_date": None}}
res = select_first_events([
    row(announcement_id="X1", stock_code="600087", ts_code="600087.SH",
        valid_time="2020-06-15T16:00:00+00:00"),
    row(announcement_id="X1", stock_code="601975", ts_code="601975.SH",
        valid_time="2020-06-15T16:00:00+00:00"),
], listing=L2)
check("A4:多命中fail-closed→0事件", res["counters"]["events"], 0)
check("A4:多命中理由", sorted(set(x["reason"] for x in res["rejects"])), ["pit_attribution_unresolved"])
# 无listing → fail-closed(禁退回输入序)
res = select_first_events([
    row(announcement_id="X2", stock_code="600087", ts_code="600087.SH",
        valid_time="2020-06-15T16:00:00+00:00"),
    row(announcement_id="X2", stock_code="601975", ts_code="601975.SH",
        valid_time="2020-06-15T16:00:00+00:00"),
])
check("A4:无listing→fail-closed 0事件", res["counters"]["events"], 0)
# 同代码重复id → 保输入序首条(v1 行为不变,非跨代码)
res = select_first_events([
    row(announcement_id="X3", valid_time="2023-05-01T09:00:00+00:00"),
    row(announcement_id="X3", valid_time="2023-05-01T09:00:00+00:00"),
])
check("同代码重复id:1事件+dup留痕",
      (res["counters"]["events"], [x["reason"] for x in res["rejects"]]),
      (1, ["dup_announcement_id"]))

# A6:fwp 裁决表门(过门比例覆写/表外 fail-closed/未过拒/进展数字陷阱)
FWP_TITLE = "关于控股股东减持股份达到1%及后续减持股份预披露的公告"
ADJ6 = {"pair_drops": [], "first_with_progress": {
    "F1": {"pass": True, "new_plan_ratio_pct": 2.0},
    "F2": {"pass": False, "reason": "pdf_text_unextractable"},
    "F4": {"pass": True, "new_plan_ratio_pct": 0.5},
}}
res = select_first_events([
    row(announcement_id="F1", title=FWP_TITLE, reduce_ratio_max_pct=0.5,
        valid_time="2023-06-01T09:00:00+00:00"),                       # 过门:覆写2.0≥1%
    row(announcement_id="F2", title=FWP_TITLE, holder_name="李四",
        valid_time="2023-06-02T09:00:00+00:00"),                       # 未过:fail-closed
    row(announcement_id="F3", title=FWP_TITLE, holder_name="王五",
        valid_time="2023-06-03T09:00:00+00:00"),                       # 表外:fail-closed
    row(announcement_id="F4", title=FWP_TITLE, holder_name="赵六", reduce_ratio_max_pct=5.0,
        valid_time="2023-06-04T09:00:00+00:00"),                       # 陷阱:parsed5.0系进展数,计划比例0.5<门
], adjudication=ADJ6)
check("A6:仅过门且计划比例≥1%者成事件", res["counters"]["events"], 1)
check("A6:F1过门(0.5被覆写2.0)", res["events"][0]["announcement_ids"], ["F1"])
check("A6:拒因三态",
      sorted(x["reason"] for x in res["rejects"]),
      ["fwp_not_adjudicated", "fwp_rejected_pdf_text_unextractable", "ratio_below_gate"])
# 无裁决表 → fwp 全 fail-closed
res = select_first_events([row(announcement_id="F5", title=FWP_TITLE,
                               valid_time="2023-06-05T09:00:00+00:00")])
check("A6:无裁决表→fwp全拒", [x["reason"] for x in res["rejects"]], ["fwp_not_adjudicated"])

# 污染类混入流水线 → 全拒不进事件(v1 行为不变)
res = select_first_events([
    row(announcement_id="G1", title="关于股东减持计划时间过半的公告",
        valid_time="2023-06-01T09:00:00+00:00"),
    row(announcement_id="G2", title="关于股东减持计划提前终止的公告",
        valid_time="2023-06-02T09:00:00+00:00"),
])
check("污染类入流水线:0事件", res["counters"]["events"], 0)

# ── 冻结裁决表实物:SHA 前置断言 + 人裁处置数逐项核 ───────────────────────────
_ADJ_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "compute", ADJUDICATION_FILE)
_raw = open(_ADJ_PATH, "rb").read()
adj_real = load_adjudication(_raw)
check("裁决表:SHA前置断言通过(实物未改)", isinstance(adj_real, dict), True)
try:
    load_adjudication(_raw + b" ")
    check("裁决表:改动即拒", "accepted", "rejected")
except ValueError:
    check("裁决表:改动即拒", "rejected", "rejected")
_drops = adj_real["pair_drops"]
check("裁决表:pair_drops总数=54", len(_drops), 54)
check("裁决表:item2b同计划坐实13",
      sum(1 for p in _drops if p["tag"] == "item2b" and p["verdict"] == "same_plan_adjudicated"), 13)
check("裁决表:item2b疑似+证据不足33",
      sum(1 for p in _drops if p["tag"] == "item2b" and p["verdict"] == "ambiguous_possible_duplicate"), 33)
_dropset = {p["drop"] for p in _drops}
check("裁决表:300143新计划(1207901152)未被剔(人令恢复)", "1207901152" in _dropset, False)
check("裁决表:301182新计划(1220023184)未被剔(人令恢复)", "1220023184" in _dropset, False)
_fwp = adj_real["first_with_progress"]
check("裁决表:fwp核验12行", len(_fwp), 12)
check("裁决表:fwp过门9行", sum(1 for v in _fwp.values() if v["pass"]), 9)

# 确定性:同输入双跑逐字节同(含裁决表+listing 全参数面)
r1 = json.dumps(select_first_events(
    [row(announcement_id="H1", valid_time="2023-07-01T09:00:00+00:00"),
     row(announcement_id="H2", holder_name="李四", valid_time="2023-07-02T09:00:00+00:00")],
    listing=LISTING, adjudication=adj_real), sort_keys=True, ensure_ascii=False)
r2 = json.dumps(select_first_events(
    [row(announcement_id="H1", valid_time="2023-07-01T09:00:00+00:00"),
     row(announcement_id="H2", holder_name="李四", valid_time="2023-07-02T09:00:00+00:00")],
    listing=LISTING, adjudication=adj_real), sort_keys=True, ensure_ascii=False)
check("确定性:双跑逐字节同", r1 == r2, True)

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
