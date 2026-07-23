"""淘沙 · exp12 st_removal ST/风险警示完整撤销事件识别(纯函数,零 I/O)。

口径出处 = 冻结 PAP(taosha/docs/st-removal-pap-final-2026-07-23.json,
digest 62a387a290707985f2d50ee490d1ac83bccc6e6dc2e6d4241ced12e6791d4353,冻结令 2026-07-23)
event_def 原文即口径;数字参照 = PAP 草案单元只读漏斗复算(batch_id=7,641 仅对账参考非硬断言,
差异按血缘归因,不追数不改规则——冻结令三节)。
职责边界 = 只做事件识别(段位折叠→转换判定→主漏斗十一档)+ 摘星/戴星/ST→退市 NFV 报数;
不读收益、不判显著、不碰台账。

冻结 event_def 转录:
  · 事件识别 = 名称段位法:段 = GROUP BY (ts_code,start_date) 折叠孪生行,段边界 =
    LEAD(start_date),**不信任行级 end_date**(is_st PIT 修法同源)。
  · ST 名判据 = 名称含 'ST'(含 *ST/SST/S*ST/G*ST 等历史变体);退市名判据 = 后缀 '%退'
    (深市)或前缀 '退市%'(沪市)**双格式必须同时覆盖**(裁定四;008 视图仅后缀谓词不可
    原样搬作事件识别);段状态优先级 = 退市 > ST > 普通(单名同时命中双谓词按此定级)。
  · 事件仅指完整撤销:前段名称属 ST 风险状态(含 ST 且非退市)、后段名称不再属 ST 或退市
    状态(裁定二);*ST→ST 摘星未摘帽不计事件仅报数(NFV,destar_audit);ST→退、退市整理
    不得进入事件集(裁定四)。
  · 事件日锚 = 后段 ann_date(公告披露日)唯一;start_date 仅生效日+状态校验,不得回填
    (裁定三)。研究期 2011-01-01 ≤ ann_date < 2024-07-01(裁定一)。
  · 事件键 = (ts_code,ann_date) 每键唯一;重复、段内公告日冲突(distinct ann_date>1)或
    前后段状态不可判(段内 ST/非ST 混名)一律 fail-closed:涉事候选全部剔除并逐条留痕,
    不合并、不择一保留(裁定六)。
  · 主漏斗固定档序(reporting_commitments)= 入库行→段→有前段转换→完整摘帽候选→
    状态不可判→锚缺失→锚冲突→ann>start 校验→研究期外→事件键重复→最终事件集。

状态不可判实现注(fail-closed 从严,不善意改写):段内折叠名逐名定级后状态集 >1 种
= 'mixed'(含 ST/非ST 混名及一切跨级混名);潜在候选(前段可 ST、后段可普通)涉 mixed 段
→ 记入候选并以 state_unjudgeable fail-closed 剔除。batch 7 实测零,语义宽严不影响参照数。

依赖:仅标准库。输入行 = dict{alias: str, start_date: date|None, ann_date: date|None};
消费方(driver)负责视图行 → dict 映射与按票分组(行序 (start_date,alias,ann_date) 钉死);
本模块单票处理,跨票聚合在调用方(merge_selections;事件键唯一性系 (ts_code,ann_date),
重复只可能发生于票内,票级处理即完备)。
"""
from __future__ import annotations

import datetime as dt

# ── 冻结 PAP 参数(digest 62a387a2…4353;口径唯一,禁散落魔法数)────────────────────
ANN_DATE_START = dt.date(2011, 1, 1)     # 研究期下界(含;裁定一)
ANN_DATE_END = dt.date(2024, 7, 1)       # 上界(不含;==holdout 焊死线)
DELIST_SUFFIX = "退"                      # 深市退市谓词:后缀 '%退'(裁定四)
DELIST_PREFIX = "退市"                    # 沪市退市谓词:前缀 '退市%'(裁定四)
ST_TOKEN = "ST"                           # ST 名判据:名称含 'ST'
STAR_TOKEN = "*ST"                        # 星标判据(摘星/戴星 NFV;*ST/S*ST/G*ST 均含 '*ST')

# 主漏斗互斥主原因(reporting_commitments 固定档序;reason 值同为 rejects 留痕键)
REASON_UNJUDGEABLE = "state_unjudgeable_fail_closed"
REASON_ANCHOR_MISSING = "anchor_missing"
REASON_ANCHOR_CONFLICT = "anchor_conflict_fail_closed"
REASON_ANN_AFTER_START = "ann_after_start_fail_closed"
REASON_OUT_OF_PERIOD = "out_of_period"
REASON_DUPLICATE_KEY = "event_key_duplicate_fail_closed"


def name_state(alias) -> str:
    """单名定级(冻结谓词;段状态优先级=退市>ST>普通,单名双命中按此定级)。
    空名/非字符串 → 'unknown'(fail-closed:含此名的段=不可判,不猜不补)。"""
    if not isinstance(alias, str) or not alias.strip():
        return "unknown"
    a = alias.strip()
    if a.endswith(DELIST_SUFFIX) or a.startswith(DELIST_PREFIX):
        return "delist"
    if ST_TOKEN in a:
        return "st"
    return "normal"


def has_star(alias) -> bool:
    """星标判据(NFV 摘星/戴星用;*ST/S*ST/G*ST 均含字面 '*ST',SST 无星不命中)。"""
    return isinstance(alias, str) and STAR_TOKEN in alias


def fold_segments(rows: list[dict]) -> tuple[list[dict], int]:
    """单票行 → 段(GROUP BY start_date 折叠孪生 + 隐式 LEAD 边界=列表序;冻结 event_def)。

    rows 按 (start_date,alias,ann_date) 升序(调用方钉死);start_date 为 None 的行
    不可折叠 → 计数剔除(start_missing_rows,留痕计数;batch 7 实测零)。
    返回 (segments, start_missing_rows);segment =
    {start_date, names:排序名列表, anns:排序非空锚列表, state, star_any, star_all, n_rows}。
    """
    start_missing = 0
    by_start: dict = {}
    order: list = []
    for r in rows:
        sd = r.get("start_date")
        if sd is None:
            start_missing += 1
            continue
        if sd not in by_start:
            by_start[sd] = {"names": set(), "anns": set()}
            order.append(sd)
        by_start[sd]["names"].add(r.get("alias"))
        if r.get("ann_date") is not None:
            by_start[sd]["anns"].add(r["ann_date"])
    segments = []
    for sd in sorted(order):
        g = by_start[sd]
        names = sorted(str(x) for x in g["names"])
        states = {name_state(x) for x in g["names"]}
        segments.append({
            "start_date": sd,
            "names": names,
            "anns": sorted(g["anns"]),
            "state": next(iter(states)) if len(states) == 1 else "mixed",
            "star_any": any(has_star(x) for x in g["names"]),
            "star_all": all(has_star(x) for x in g["names"]) and bool(names),
            "n_rows": len(g["names"])})
    return segments, start_missing


def _rec(ts_code: str, prev: dict, cur: dict) -> dict:
    """候选留痕记录(前后段全量几何;确定性=输入唯一决定输出)。"""
    anchor = cur["anns"][0] if len(cur["anns"]) == 1 else None
    return {"ts_code": ts_code,
            "prev_start_date": prev["start_date"].isoformat(),
            "prev_names": prev["names"], "prev_state": prev["state"],
            "cur_start_date": cur["start_date"].isoformat(),
            "cur_names": cur["names"], "cur_state": cur["state"],
            "ann_date": anchor.isoformat() if anchor else None,
            "anns_distinct": [d.isoformat() for d in cur["anns"]],
            "gap_days": ((cur["start_date"] - anchor).days if anchor else None)}


def run_funnel(ts_code: str, rows: list[dict]) -> dict:
    """单票完整主漏斗(reporting_commitments 固定档序,互斥主原因)+ NFV 报数。

    返回 {"events","rejects","counters"}:events/rejects 携带前后段全量几何,
    确定性 = 输入行序唯一决定输出(纯函数,双跑同)。
    NFV 计数(不入事件集,仅报数,裁定二/四):destar_all(*ST→ST 摘星未摘帽全史)/
    destar_in_window_clean_anchor(其中锚唯一且研究期内)/star_on_all(ST→*ST 戴星全史)/
    st_to_delist_all(ST→退市全史,含退市整理)。
    """
    segments, start_missing = fold_segments(rows)
    g = {"input_rows": len(rows), "start_missing_rows": start_missing,
         "segments": len(segments),
         "transitions_with_prev": max(len(segments) - 1, 0),
         "removal_candidates": 0,
         REASON_UNJUDGEABLE: 0, REASON_ANCHOR_MISSING: 0, REASON_ANCHOR_CONFLICT: 0,
         REASON_ANN_AFTER_START: 0, REASON_OUT_OF_PERIOD: 0,
         "duplicate_event_keys": 0, REASON_DUPLICATE_KEY: 0,
         "final_events": 0,
         "destar_all": 0, "destar_in_window_clean_anchor": 0,
         "star_on_all": 0, "st_to_delist_all": 0}
    events: list[dict] = []
    rejects: list[dict] = []
    survivors: list[dict] = []
    for k in range(1, len(segments)):
        prev, cur = segments[k - 1], segments[k]
        # ── NFV 报数(不改事件集;裁定二/四)──
        if prev["state"] == "st" and cur["state"] == "st":
            if prev["star_any"] and not cur["star_any"]:
                g["destar_all"] += 1                      # *ST→ST 摘星未摘帽
                if (len(cur["anns"]) == 1
                        and ANN_DATE_START <= cur["anns"][0] < ANN_DATE_END):
                    g["destar_in_window_clean_anchor"] += 1
            if not prev["star_any"] and cur["star_any"]:
                g["star_on_all"] += 1                     # ST→*ST 戴星
        if prev["state"] == "st" and cur["state"] == "delist":
            g["st_to_delist_all"] += 1                    # ST→退市(不入事件集,裁定四)
        # ── 完整摘帽候选判定(前段 ST 状态→后段普通;mixed 涉事=候选+不可判 fail-closed)──
        clean_candidate = prev["state"] == "st" and cur["state"] == "normal"
        unjudgeable_candidate = (
            (prev["state"] == "mixed" or cur["state"] == "mixed")
            and any(name_state(x) == "st" for x in prev["names"])
            and any(name_state(x) == "normal" for x in cur["names"]))
        if not (clean_candidate or unjudgeable_candidate):
            continue
        g["removal_candidates"] += 1
        rec = _rec(ts_code, prev, cur)
        # ① 状态不可判(裁定六,fail-closed)
        if unjudgeable_candidate:
            g[REASON_UNJUDGEABLE] += 1
            rejects.append(dict(rec, reason=REASON_UNJUDGEABLE))
            continue
        # ② 锚缺失(ann 全空=覆盖边界,留痕;裁定一)
        if not cur["anns"]:
            g[REASON_ANCHOR_MISSING] += 1
            rejects.append(dict(rec, reason=REASON_ANCHOR_MISSING))
            continue
        # ③ 锚冲突(段内 distinct ann>1,fail-closed;裁定六)
        if len(cur["anns"]) > 1:
            g[REASON_ANCHOR_CONFLICT] += 1
            rejects.append(dict(rec, reason=REASON_ANCHOR_CONFLICT))
            continue
        anchor = cur["anns"][0]
        # ④ ann>start 校验(ann 严格≤start;fail-closed;裁定三)
        if anchor > cur["start_date"]:
            g[REASON_ANN_AFTER_START] += 1
            rejects.append(dict(rec, reason=REASON_ANN_AFTER_START))
            continue
        # ⑤ 研究期(裁定一)
        if not (ANN_DATE_START <= anchor < ANN_DATE_END):
            g[REASON_OUT_OF_PERIOD] += 1
            rejects.append(dict(rec, reason=REASON_OUT_OF_PERIOD))
            continue
        survivors.append(rec)
    # ⑥ 事件键重复((ts_code,ann_date) 全剔逐条留痕,不合并不择一;裁定六)
    by_ann: dict[str, list[dict]] = {}
    for rec in survivors:
        by_ann.setdefault(rec["ann_date"], []).append(rec)
    for ann_key in sorted(by_ann):
        grp = by_ann[ann_key]
        if len(grp) > 1:
            g["duplicate_event_keys"] += 1
            g[REASON_DUPLICATE_KEY] += len(grp)
            for rec in grp:
                rejects.append(dict(rec, reason=REASON_DUPLICATE_KEY,
                                    n_colliding=len(grp)))
            continue
        g["final_events"] += 1
        events.append(grp[0])
    return {"events": events, "rejects": rejects, "counters": g}


def funnel_identity_ok(c: dict) -> bool:
    """主漏斗恒等式(reporting_commitments:计数+恒等式+明确分母):
    候选 − 状态不可判 − 锚缺失 − 锚冲突 − ann>start − 期外 − 键重复剔除 == 最终事件集。"""
    return (c["removal_candidates"]
            - c[REASON_UNJUDGEABLE] - c[REASON_ANCHOR_MISSING]
            - c[REASON_ANCHOR_CONFLICT] - c[REASON_ANN_AFTER_START]
            - c[REASON_OUT_OF_PERIOD] - c[REASON_DUPLICATE_KEY]
            ) == c["final_events"]


def select_st_removal_events(ts_code: str, rows: list[dict]) -> dict:
    """单票事件识别全流水线(段位折叠→主漏斗→NFV 报数)。
    rows = 该票 explore_reader_namechange(_snap) 行按 (start_date,alias,ann_date) 升序
    (调用方保证排序;None start 行入 start_missing 计数)。"""
    return run_funnel(ts_code, rows)


def merge_selections(per_security: list[dict]) -> dict:
    """跨票聚合(调用方逐票流式喂 select_st_removal_events 结果):
    events/rejects 全量拼接(票内已按段序,票间按调用方喂入序=ts_code 序);
    counters 逐键求和 + reject_reasons 计数。纯函数,不排序不改行。"""
    events, rejects = [], []
    counters: dict = {}
    for sel in per_security:
        events.extend(sel["events"])
        rejects.extend(sel["rejects"])
        for k, v in sel["counters"].items():
            counters[k] = counters.get(k, 0) + v
    reasons: dict = {}
    for r in rejects:
        reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    return {"events": events, "rejects": rejects, "counters": counters,
            "reject_reasons": reasons}
