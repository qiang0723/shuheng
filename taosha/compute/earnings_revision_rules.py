"""淘沙 · compute · exp20 业绩预告修正事件规则(冻结 PAP v2 event_def 逐字实现;纯函数零 I/O)。

冻结口径 = 台账 exp20 冻结 PAP v2(canonical digest
`e1d18dc1019d8c43563b762c3dec3cf7b4bccad1e25667721867c33bb1dd7fd5`,冻结令 2026-07-18 深夜六),
原文即口径,本模块一个数不改:
  · 样本源 = qbase forecast_snap 中 first_ann_date≠ann_date 的行 = 修正公告候选;
  · 来源链键 = (ts_code, end_date, first_ann_date);市场事件键 = (ts_code, ann_date),每键唯一;
  · 同日逐字段重复行仅在 L2 确定性折叠(L1 原始行不动;本函数即 L2);
  · 修正方向基准 B = 同链内事件日前最近一次公开披露(可为首披或前一修正),不取链首次披露;
  · 方向判定字段 = p_change_min/p_change_max:两边界均在取中点;仅一边界在回退该单值;
    两边界全空 = 数值不可判 fail-closed;同链同日多行须全部可判且标量一致,否则 fail-closed;
    当前值相对基准值:大于=up、小于=down、等于=flat;禁 net_profit、禁 type 文字回退
    (视图列面已不含二者,结构上防误用);
  · flat 两阶段语义(人令 2026-07-18 深夜三):候选方向分类阶段 flat=合法分类结果,计入 flat
    计数块后排除出主事件集,不因存在 flat 候选拒绝整次运行(泄漏 fail-closed 属引擎第二道闸);
  · fail-closed 全集(逐类计数,600856.SH 单独留痕):孤儿修正(链无首披行)/ann_date<first_ann_date
    /同期多链归属不明/基准或当前数值不可判/同日方向冲突/600856.SH 单位疑点;
  · 同日多链同方向折叠为一个市场事件(保留组成链审计清单);同日方向冲突整事件 fail-closed
    (方向=up/down;flat 不属于方向,不参与冲突判定,仅入计数块);
  · 不设修正幅度门;研究期 2013-01-01 ≤ ann_date < 2024-07-01。

判定次序(确定性,逐层归因对账消费;PAP reporting_commitments①):
  重复行折叠 → 缺链锚(first_ann_date 空)→ 时序违例 → 研究期 → 同期多链 → 600856.SH →
  孤儿 → 当前值可判 → 基准可判 → 方向分类(flat 排除)→ 同日折叠/方向冲突。
窄闸参考数(候选 12,569 / 基准B可判 5,225)仅对账参考,不是预写样本量;对不上不得改本规则,
异常即停报人(冻结令三)。
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

# 冻结参数(PAP v2 event_def 原文;不许运行时覆盖)
RESEARCH_START = dt.date(2013, 1, 1)     # 研究期下限(含)
RESEARCH_END = dt.date(2024, 7, 1)       # 研究期上限(不含;=holdout 线)
TICKER_FAIL_CLOSED = "600856.SH"         # 单位疑点单票留痕项(既裁 2026-07-17)
DIR_UP, DIR_DOWN, DIR_FLAT = "up", "down", "flat"

# fail-closed 六类(PAP reporting_commitments② 逐类计数键;命名入 audit,不得改写)
FC_ORPHAN = "orphan_no_first_disclosure"          # 孤儿修正:链无首披行
FC_TEMPORAL = "temporal_violation"                # ann_date < first_ann_date
FC_MULTI_CHAIN = "multi_chain_ambiguous"          # 同期多链归属不明
FC_VALUE = "value_undecidable"                    # 基准或当前数值不可判(含同日多行不一致)
FC_CONFLICT = "same_day_direction_conflict"       # 同日方向冲突(整市场事件)
FC_TICKER = "ticker_600856_fail_closed"           # 600856.SH 单票留痕
FAIL_CLOSED_CLASSES = (FC_ORPHAN, FC_TEMPORAL, FC_MULTI_CHAIN, FC_VALUE, FC_CONFLICT, FC_TICKER)

_ROW_KEYS = ("ts_code", "ann_date", "end_date", "first_ann_date", "p_change_min", "p_change_max")


def value_of(p_change_min, p_change_max) -> Optional[float]:
    """方向判定标量(冻结口径,人裁十项之二):两边界均在→中点;仅一边界在→该单值;
    全空→None(不可判)。不猜不补,禁 net_profit/type 回退。"""
    if p_change_min is not None and p_change_max is not None:
        return (float(p_change_min) + float(p_change_max)) / 2.0
    if p_change_min is not None:
        return float(p_change_min)
    if p_change_max is not None:
        return float(p_change_max)
    return None


def day_scalar(day_rows: list[dict]) -> tuple[Optional[float], Optional[str]]:
    """同链同日行集 → (标量, None) 或 (None, 不可判子因)。
    冻结口径:同链同日多行须**全部可判且标量一致**,否则 fail-closed。
    子因:'undecidable'=存在不可判行;'inconsistent'=均可判但标量不一致。"""
    vals = [value_of(r["p_change_min"], r["p_change_max"]) for r in day_rows]
    if any(v is None for v in vals):
        return None, "undecidable"
    if len({v for v in vals}) > 1:
        return None, "inconsistent"
    return vals[0], None


def _year(d: dt.date) -> str:
    return str(d.year)


class _Funnel:
    """逐层计数器(对账消费;纯计数,零判断)。"""

    def __init__(self):
        self.counters: dict = {}
        self.fc_by_class: dict = {c: 0 for c in FAIL_CLOSED_CLASSES}
        self.fc_by_class_year: dict = {c: {} for c in FAIL_CLOSED_CLASSES}

    def bump(self, key: str, n: int = 1):
        self.counters[key] = self.counters.get(key, 0) + n

    def fail(self, cls: str, year: str, n: int = 1):
        self.fc_by_class[cls] += n
        by = self.fc_by_class_year[cls]
        by[year] = by.get(year, 0) + n


def select_revision_events(rows: list[dict]) -> dict:
    """forecast 行集 → 修正市场事件 + 全量漏斗留痕(冻结纯函数;行=explore_reader_forecast 列面)。

    rows: [{ts_code, ann_date, end_date, first_ann_date, p_change_min, p_change_max}, ...]
          (日期=datetime.date;数值=float/Decimal/None;行序无要求,内部确定性排序)。
    返回 {"events": [...], "counters": {...}, "fail_closed": {...}, "flat": {...},
          "fold_audit_n": int, "itemized_600856": [...], "rejects_600856_n": int}。
    events 行 = {ts_code, ann_date, direction(up|down), event_id, member_chains:[...]}
    (member_chains=组成链审计清单,PAP reporting_commitments④)。"""
    fn = _Funnel()
    fn.bump("input_rows", len(rows))

    # ── L2 确定性折叠:同日逐字段重复行(L1 原始行不动)─────────────────────────
    uniq: dict = {}
    for r in rows:
        key = tuple(r[k] for k in _ROW_KEYS)
        if key not in uniq:
            uniq[key] = {k: r[k] for k in _ROW_KEYS}
    rows_u = sorted(uniq.values(),
                    key=lambda r: (r["ts_code"], r["ann_date"],
                                   r["end_date"] or dt.date.min,
                                   r["first_ann_date"] or dt.date.min))
    fn.bump("duplicate_rows_collapsed", len(rows) - len(rows_u))
    fn.bump("rows_after_dedup", len(rows_u))

    # ── 行级分拣:缺链锚 / 首披 / 时序违例 / 修正候选 ────────────────────────────
    chain_rows: dict = {}          # (ts, end, first) → [row](链成员=首披+修正;不含时序违例)
    candidates: list[dict] = []    # 修正候选行(first 在场且 ann>first)
    for r in rows_u:
        if r["first_ann_date"] is None or r["end_date"] is None:
            fn.bump("rows_missing_chain_anchor")      # 链锚缺失:无链归属,不进候选不作基准
            continue
        if r["ann_date"] < r["first_ann_date"]:
            fn.fail(FC_TEMPORAL, _year(r["ann_date"]))
            continue
        chain_rows.setdefault((r["ts_code"], r["end_date"], r["first_ann_date"]), []).append(r)
        if r["ann_date"] != r["first_ann_date"]:
            candidates.append(r)
    fn.bump("candidate_rows_all_periods", len(candidates))

    # ── 研究期(事件锚 ann_date;基准回看不受限)────────────────────────────────
    in_period: list[dict] = []
    for r in candidates:
        if r["ann_date"] < RESEARCH_START:
            fn.bump("candidate_rows_pre_research_period")
        elif r["ann_date"] >= RESEARCH_END:
            fn.bump("candidate_rows_post_research_period")   # 视图 holdout 已焊死;防御性计数
        else:
            in_period.append(r)
    fn.bump("candidate_rows_in_period", len(in_period))
    fn.bump("candidate_event_keys_in_period",
            len({(r["ts_code"], r["ann_date"]) for r in in_period}))   # 窄闸 12,569 对账层

    # ── 同期多链侦测:同 (ts_code,end_date) 多 first_ann_date → 归属不明 ─────────
    firsts_by_period_key: dict = {}
    for (ts, ed, fa) in chain_rows:
        firsts_by_period_key.setdefault((ts, ed), set()).add(fa)
    ambiguous_period_keys = {k for k, v in firsts_by_period_key.items() if len(v) > 1}

    # ── 逐(链,事件日)判定:600856 → 孤儿 → 当前可判 → 基准可判 → 方向 ─────────
    by_chain_day: dict = {}
    for r in in_period:
        by_chain_day.setdefault(
            ((r["ts_code"], r["end_date"], r["first_ann_date"]), r["ann_date"]), []).append(r)

    fn.bump("chain_day_candidates_in_period", len(by_chain_day))
    itemized_600856: list[dict] = []
    directed: list[dict] = []      # 方向已判(up/down)链日事件
    flat_chain_days = 0
    flat_years: dict = {}
    value_sub: dict = {"current_undecidable": 0, "current_inconsistent": 0,
                       "baseline_undecidable": 0, "baseline_inconsistent": 0}

    for (chain_key, ann_date), day_rows in sorted(
            by_chain_day.items(),
            key=lambda kv: (kv[0][0][0], kv[0][1], kv[0][0][1], kv[0][0][2])):
        ts, end_date, first_ann = chain_key
        yr = _year(ann_date)
        if (ts, end_date) in ambiguous_period_keys:
            fn.fail(FC_MULTI_CHAIN, yr)
            continue
        if ts == TICKER_FAIL_CLOSED:
            fn.fail(FC_TICKER, yr)
            itemized_600856.append({"ts_code": ts, "ann_date": ann_date.isoformat(),
                                    "end_date": end_date.isoformat(),
                                    "first_ann_date": first_ann.isoformat(),
                                    "note": "600856.SH 单位疑点单票 fail-closed(既裁留痕项)"})
            continue
        members = chain_rows.get(chain_key, [])
        if not any(m["ann_date"] == first_ann for m in members):
            fn.fail(FC_ORPHAN, yr)                      # 孤儿:链无首披行
            continue
        cur, sub = day_scalar(day_rows)
        if cur is None:
            fn.fail(FC_VALUE, yr)
            value_sub[f"current_{sub}"] += 1
            continue
        # 基准 B = 链内事件日前最近一次公开披露(首披或前一修正;不跳挑、不可判即 fail-closed)
        prior_dates = sorted({m["ann_date"] for m in members if m["ann_date"] < ann_date})
        base_date = prior_dates[-1]                     # 孤儿已排除 → 首披行在场,必非空
        base_rows = [m for m in members if m["ann_date"] == base_date]
        base, bsub = day_scalar(base_rows)
        if base is None:
            fn.fail(FC_VALUE, yr)
            value_sub[f"baseline_{bsub}"] += 1
            continue
        if cur > base:
            direction = DIR_UP
        elif cur < base:
            direction = DIR_DOWN
        else:
            flat_chain_days += 1                        # flat=合法分类结果:计数后排除,不拒跑
            flat_years[yr] = flat_years.get(yr, 0) + 1
            continue
        directed.append({"ts_code": ts, "ann_date": ann_date, "direction": direction,
                         "end_date": end_date, "first_ann_date": first_ann,
                         "baseline_ann_date": base_date,
                         "baseline_value": base, "current_value": cur})
    fn.bump("directed_chain_days", len(directed))

    # ── 市场事件折叠:(ts_code, ann_date) 每键唯一;同向折叠+组成链审计;冲突整事件拒 ──
    by_event_key: dict = {}
    for d in directed:
        by_event_key.setdefault((d["ts_code"], d["ann_date"]), []).append(d)
    events: list[dict] = []
    folded_multi = conflict_events = conflict_chain_days = 0
    for (ts, ann_date), ds in sorted(by_event_key.items()):
        dirs = {d["direction"] for d in ds}
        if len(dirs) > 1:
            conflict_events += 1
            conflict_chain_days += len(ds)
            fn.fail(FC_CONFLICT, _year(ann_date))       # 逐市场事件计数(整事件 fail-closed)
            continue
        if len(ds) > 1:
            folded_multi += 1
        events.append({
            "ts_code": ts, "ann_date": ann_date, "direction": ds[0]["direction"],
            "event_id": f"{ts}:{ann_date.strftime('%Y%m%d')}",
            "member_chains": [{
                "end_date": d["end_date"].isoformat(),
                "first_ann_date": d["first_ann_date"].isoformat(),
                "baseline_ann_date": d["baseline_ann_date"].isoformat(),
                "baseline_value": d["baseline_value"], "current_value": d["current_value"],
                "direction": d["direction"]} for d in sorted(
                    ds, key=lambda x: (x["end_date"], x["first_ann_date"]))],
        })
    fn.bump("events_after_fold", len(events))
    fn.bump("events_up", sum(1 for e in events if e["direction"] == DIR_UP))
    fn.bump("events_down", sum(1 for e in events if e["direction"] == DIR_DOWN))

    return {
        "events": events,
        "counters": fn.counters,
        "fail_closed": {
            "by_class": fn.fc_by_class,
            "by_class_year": {c: dict(sorted(y.items())) for c, y in fn.fc_by_class_year.items()},
            "value_undecidable_sub": value_sub,
            "note": "fail-closed 六类逐类计数(PAP reporting_commitments②);"
                    "same_day_direction_conflict 按市场事件计,其余按(链,事件日)候选计;"
                    "600856.SH 单独逐条留痕(itemized_600856)",
        },
        "flat": {
            "chain_day_flat": flat_chain_days,
            "by_year": dict(sorted(flat_years.items())),
            "note": "flat=候选方向分类阶段合法分类结果:计入本块后排除出主事件集,"
                    "不因存在 flat 候选拒绝整次运行(PAP v2 两阶段语义);不入方向判决不入主样本",
        },
        "fold_audit": {
            "events_folded_from_multi_chain": folded_multi,
            "conflict_events": conflict_events,
            "conflict_chain_days": conflict_chain_days,
            "note": "同日多链同方向折叠为一个市场事件(组成链审计=events[].member_chains;"
                    "人裁十项之九);同日方向冲突整事件 fail-closed;"
                    "flat 不属于方向,不参与冲突判定(仅入 flat 计数块)",
        },
        "itemized_600856": itemized_600856,
    }


if __name__ == "__main__":
    # 随件自检(攻击面在 harness/verify_earnings_revision_rules.py;此处仅冒烟)
    D = dt.date
    rows = [
        # 链 A:首披 + 上修(中点 5 → 15)
        {"ts_code": "000001.SZ", "ann_date": D(2020, 1, 10), "end_date": D(2019, 12, 31),
         "first_ann_date": D(2020, 1, 10), "p_change_min": 0.0, "p_change_max": 10.0},
        {"ts_code": "000001.SZ", "ann_date": D(2020, 4, 10), "end_date": D(2019, 12, 31),
         "first_ann_date": D(2020, 1, 10), "p_change_min": 10.0, "p_change_max": 20.0},
        # 链 B:首披 + 下修(单边回退 -30 → 中点 -50)
        {"ts_code": "000002.SZ", "ann_date": D(2021, 1, 8), "end_date": D(2020, 12, 31),
         "first_ann_date": D(2021, 1, 8), "p_change_min": -30.0, "p_change_max": None},
        {"ts_code": "000002.SZ", "ann_date": D(2021, 4, 2), "end_date": D(2020, 12, 31),
         "first_ann_date": D(2021, 1, 8), "p_change_min": -60.0, "p_change_max": -40.0},
    ]
    sel = select_revision_events(rows)
    assert sel["counters"]["events_after_fold"] == 2
    assert [e["direction"] for e in sorted(sel["events"], key=lambda e: e["ts_code"])] == ["up", "down"]
    assert sel["fail_closed"]["by_class"] == {c: 0 for c in FAIL_CLOSED_CLASSES}
    print("earnings_revision_rules 冒烟 OK:up/down 各 1、零 fail-closed(攻击面见 harness)")
