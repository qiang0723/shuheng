"""holder_sell(exp4) 事件识别确定性规则 v2 — 六类判别 + 首次计划识别/关联/去重(纯函数,零I/O)。
规则 v2 冻结于人裁 2026-07-16(A1–A6,docs/holder-sell-rules-v2-ruling-2026-07-16.md);
v1(§2B 版)已被人令显式作废(原因=PDF 攻击核验发现词形泄漏/真实新计划误删/错误 PIT 归属)。
口径出处:exp4 冻结 PAP(event_def=减持计划首次预披露公告,减持比例≥总股本1%;T+1日级;sample_gate=30)。

v2 要点(对 v1 的全部改动,人裁原文即口径):
  A1 "减持…计划…到期"入结果类;负语境掩码扩"…到期"与"资管/纾困/信托计划到期"(真首披保护);
  A2 既往减持"达到/累计/超过N%"且无预披露→进展类(progress_reached);"拟减持…"前掩不误杀新计划;
  A3 减持语境"修正"入修订类(锚定,不因无关修正误杀首次);
  A4 跨代码同 announcement_id 按公告日 PIT 上市窗归属:唯一命中保留,无/多命中 fail-closed 留痕,禁输入序;
  A5 中键 30 日窗降级为诊断清单,不改变事件集合;自动去重仅 id 重复/强键/冻结裁决表在册对;
  A6 "达到N%暨预披露"单列 first_with_progress 子类,逐行裁决表门(1%门取新计划比例),表外 fail-closed。
裁决表=holder_sell_adjudication_exp4_v1.json,SHA256 前置断言焊死(本次 exp4 不可变,人令边界)。
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re

#: 冻结裁决表(A5/A6 人工逐对/逐行判定实物;与本模块同目录)。运行前冻结,改动即拒。
ADJUDICATION_FILE = "holder_sell_adjudication_exp4_v1.json"
ADJUDICATION_SHA256 = "78847ed14a017482c4a71b723f0593965e60e3dff9f5222ab81f8ce3f218751e"

# ── 负语境掩码:非"减持计划结果"语境(真首披保护,A1) ─────────────────────────
_RE_MASK = re.compile(r"(限售|锁定|解禁|禁售|持有)[^，。；]{0,8}?(期满|届满|到期)")
_RE_MASK_AMC = re.compile(r"(资管|资产管理|纾困|信托|理财)[^，。；]{0,16}?计划到期")
# A2:拟/预计减持…= 新计划表述,达到N%匹配前掩,防"拟减持达到N%"误判进展
_RE_INTEND = re.compile(r"(拟|预计)[^，。；]{0,4}减持")

# ── 六类锚定正则(优先序自上而下,首中即判) ─────────────────────────────────
_RE_REVISION = re.compile(
    r"更正|修订|补充"
    r"|减持[^，。；]{0,12}修正|修正[^，。；]{0,4}减持"
    r"|减持(股份)?计划[^，。；]{0,4}(变更|调整|延期)"
    r"|(变更|调整|延期)[^，。；]{0,2}减持(股份)?计划")
_RE_TERMINATION = re.compile(
    r"减持(股份)?计划[^，。；]{0,8}(提前)?(终止|结束)"
    r"|(提前)?(终止|结束)[^，。；]{0,8}减持"
    r"|提前终止")
_RE_HALFWAY = re.compile(r"(时间|数量)过半")
_RE_PROGRESS = re.compile(r"进展|实施情况")  # 采集 title 筛已构造性排除,规则仍设防(换源防线)
_RE_RESULT = re.compile(
    r"减持(股份)?结果"
    r"|减持[^，。；]{0,12}计划[^，。；]{0,8}(期满|届满|到期)"
    r"|期满未减持"
    r"|减持(股份)?(计划)?[^，。；]{0,4}完毕"
    r"|减持完成")
# A2/A6:既往减持达到/累计/超过 N%(不超过=计划上限表述,负向排除)
_RE_REACHED = re.compile(
    r"减持[^，。；]{0,12}(达到|累计超过|累计达到|(?<!不)超过)[^，。；]{0,8}[0-9０-９.．]+\s*[%％]")
_RE_PREDISCLOSE = re.compile(r"预披露")  # A6 并披指示(词序任意;裁决表门兜底,表外 fail-closed)
# 混合标题指示:污染核心命中 且 出现"暨/及(后续|未来|新)…预披露"式新计划并披指示
_RE_NEWPLAN_IND = re.compile(
    r"(暨|及)[^，。；]{0,16}预披露|(后续|未来|新)[^，。；]{0,12}减持[^，。；]{0,10}预披露")
# 广义污染词(fail-closed 兜底面;A1 增"到期")。"修正"不入兜底:人裁 A3 明令不得因
# 无关事项出现"修正"误杀首次(修订判定仅走上方锚定;冻结语料"修正"行仅 1 条且被锚定命中)。
_RE_BROAD = re.compile(
    r"过半|进展|期满|届满|到期|结果|完毕|完成|终止|结束|更正|修订|补充|变更|调整|延期|实施")

CLS_FIRST = "first_candidate"
CLS_FWP = "first_with_progress"      # A6 单列子类(进裁决表门,不成新假设不独立 verdict)
CLS_REVISION = "revision"
CLS_TERMINATION = "termination"
CLS_HALFWAY = "halfway"
CLS_PROGRESS = "progress"
CLS_PROGRESS_REACHED = "progress_reached"  # A2 进展类之"达到N%"子标签
CLS_RESULT = "result"
CLS_COMBO = "combo_ambiguous"
CLS_SUSPECT = "suspect_unresolved"

#: 除首次(含 fwp 子类)外全部为污染/剔除类
POLLUTION_CLASSES = (CLS_REVISION, CLS_TERMINATION, CLS_HALFWAY, CLS_PROGRESS,
                     CLS_PROGRESS_REACHED, CLS_RESULT, CLS_COMBO, CLS_SUSPECT)


def load_adjudication(data: bytes) -> dict:
    """裁决表前置断言(纯函数:bytes→dict):SHA256 与冻结常量不符即拒(fail-closed,不可变边界)。"""
    got = hashlib.sha256(data).hexdigest()
    if got != ADJUDICATION_SHA256:
        raise ValueError(f"裁决表 SHA256 不符:got={got} want={ADJUDICATION_SHA256};"
                         "冻结实物被改动,拒绝运行(人令 2026-07-16 不可变边界)")
    return json.loads(data)


def classify_event_title(title: str) -> str:
    """标题 → 六类+fwp+两剔除类。确定性:纯文本、无外部状态。"""
    t = re.sub(r"\s+", "", title or "")
    t = _RE_MASK.sub("◇", t)
    t = _RE_MASK_AMC.sub("◇", t)
    if _RE_REVISION.search(t):
        return CLS_REVISION
    core = (_RE_TERMINATION.search(t) or _RE_HALFWAY.search(t)
            or _RE_PROGRESS.search(t) or _RE_RESULT.search(t))
    if core and _RE_NEWPLAN_IND.search(t):
        return CLS_COMBO
    if _RE_TERMINATION.search(t):
        return CLS_TERMINATION
    if _RE_HALFWAY.search(t):
        return CLS_HALFWAY
    if _RE_PROGRESS.search(t):
        return CLS_PROGRESS
    if _RE_RESULT.search(t):
        return CLS_RESULT
    if _RE_REACHED.search(_RE_INTEND.sub("◇", t)):
        return CLS_FWP if _RE_PREDISCLOSE.search(t) else CLS_PROGRESS_REACHED
    if _RE_BROAD.search(t):
        return CLS_SUSPECT
    return CLS_FIRST


_BJT = dt.timezone(dt.timedelta(hours=8))


def bj_event_date(valid_time_iso: str) -> dt.date:
    """UTC ISO 时间戳 → 京时日历日(事件日)。PAP=T+1 日级无盘中分支。"""
    return dt.datetime.fromisoformat(valid_time_iso).astimezone(_BJT).date()


def _as_date(v):
    """date/ISO 串/None → date/None(listing 字段归一)。"""
    if v is None or isinstance(v, dt.date):
        return v
    return dt.date.fromisoformat(str(v)[:10])


def _pit_listed(info: dict | None, d: dt.date) -> bool:
    """公告日 d 在 ts_code 的 PIT 上市窗内(list_date ≤ d < delist_date;delist 空=在市)。"""
    if not info:
        return False
    ld, dd = _as_date(info.get("list_date")), _as_date(info.get("delist_date"))
    if ld is None or d < ld:
        return False
    return dd is None or d < dd


def _dedup_and_attribute(rows, listing, rejects, conflicts):
    """步1(A4):announcement_id 去重+跨代码 PIT 归属。
    同代码重复=保输入序首条;跨代码=公告日 PIT 上市窗唯一命中保留,无/多命中 fail-closed 全剔留痕。"""
    groups: dict = {}
    order: list = []
    for r in rows:
        aid = r.get("announcement_id")
        if aid not in groups:
            groups[aid] = []
            order.append(aid)
        groups[aid].append(r)
    uniq: list[dict] = []
    for aid in order:
        grp = groups[aid]
        codes = {g.get("stock_code") for g in grp}
        if len(codes) == 1:
            uniq.append(grp[0])
            for g in grp[1:]:
                rejects.append({"announcement_id": aid, "reason": "dup_announcement_id"})
            continue
        # 跨代码同 id:按公告日 PIT 上市窗归属(禁输入序,人裁 A4)
        d = bj_event_date(grp[0]["valid_time"])
        hits = [g for g in grp if _pit_listed((listing or {}).get(g.get("ts_code")), d)]
        if len(hits) == 1:
            uniq.append(hits[0])
            dropped = sorted(g.get("stock_code") for g in grp if g is not hits[0])
            conflicts.append({"announcement_id": aid, "resolution": "pit_unique",
                              "kept": hits[0].get("stock_code"), "dropped": dropped})
            for g in grp:
                if g is not hits[0]:
                    rejects.append({"announcement_id": aid, "reason": "pit_attribution_other_code"})
        else:
            conflicts.append({"announcement_id": aid, "resolution": "pit_unresolved",
                              "kept": None, "dropped": sorted(codes),
                              "n_hits": len(hits)})
            for _ in grp:
                rejects.append({"announcement_id": aid, "reason": "pit_attribution_unresolved"})
    return uniq


def _apply_adjudication(firsts, fwp_flags, adjudication, rejects):
    """步3(A5/A6):冻结裁决表。pair_drops 在册对剔后续;fwp 行逐行门(表外/未过=fail-closed),
    过门者 1% 门比例改取裁决表新计划比例。返回 (存活行, 比例覆写表)。"""
    adj = adjudication or {}
    drop_map = {p["drop"]: p["verdict"] for p in adj.get("pair_drops", [])}
    fwp_map = adj.get("first_with_progress", {})
    kept: list[dict] = []
    ratio_override: dict = {}
    for r in firsts:
        aid = r.get("announcement_id")
        if aid in drop_map:
            rejects.append({"announcement_id": aid, "reason": drop_map[aid]})
            continue
        if fwp_flags.get(aid):
            entry = fwp_map.get(str(aid))
            if entry is None:
                rejects.append({"announcement_id": aid, "reason": "fwp_not_adjudicated"})
                continue
            if not entry.get("pass"):
                rejects.append({"announcement_id": aid,
                                "reason": f"fwp_rejected_{entry.get('reason', 'fail_closed')}"})
                continue
            ratio_override[aid] = entry["new_plan_ratio_pct"]
        kept.append(r)
    return kept, ratio_override


def _midkey_diagnostics(firsts, window_days):
    """A5:中键(票,股东,比例)≤window 日扫描,仅产诊断清单,不改变事件集合(人裁 2026-07-16)。"""
    def _order_key(r):
        return (r.get("valid_time") or "", str(r.get("announcement_id")))
    last_seen: dict = {}
    pairs: list[dict] = []
    for r in sorted(firsts, key=_order_key):
        h, ratio = r.get("holder_name"), r.get("reduce_ratio_max_pct")
        if not h or ratio is None:
            continue
        k = (r.get("stock_code"), h, ratio)
        d = bj_event_date(r["valid_time"])
        prev = last_seen.get(k)
        if prev is not None and (d - prev[0]).days <= window_days:
            pairs.append({"stock_code": k[0], "holder_name": h, "ratio": ratio,
                          "prev_announcement_id": prev[1],
                          "announcement_id": r.get("announcement_id"),
                          "gap_days": (d - prev[0]).days})
        last_seen[k] = (d, r.get("announcement_id"))
    return pairs


def select_first_events(rows: list[dict], gate_ratio_pct: float = 1.0,
                        midkey_diag_window_days: int = 30,
                        listing: dict | None = None,
                        adjudication: dict | None = None) -> dict:
    """冻结语料行 → 首次计划事件集(规则 v2,人裁 2026-07-16;PAP 1%门)。

    步骤(顺序即口径,单一剔除理由留痕):
      1 去重+归属(A4): id 唯一;跨代码同 id 按 PIT 上市窗唯一命中,无/多命中 fail-closed;
      2 类判别(A1/A2/A3/A6): first_candidate 与 first_with_progress 进入,其余按类记剔除;
      3 冻结裁决表(A5/A6): 在册对剔后续(same_plan_adjudicated/ambiguous_possible_duplicate);
        fwp 逐行门,表外 fail-closed,过门者门槛比例=裁决表新计划比例;
      4 同计划强键关联: (票,股东,减持期起,止) 全解析同键 → 保最早(valid_time,id),余剔;
      5 比例门(PAP冻结): 解析(或 fwp 覆写)比例 ≥ gate;未解析=不可证≥1% → fail-closed 剔;
      6 事件发射: 唯一 (ts_code, 京时事件日);
      诊断(A5): 中键 30 日窗候选清单仅报告,不改变事件集合。
    返回 {events, rejects, conflicts, counters, diagnostics};零I/O、零随机,输入确定输出。
    """
    counters: dict = {"input": len(rows)}
    rejects: list[dict] = []
    conflicts: list[dict] = []
    uniq = _dedup_and_attribute(rows, listing, rejects, conflicts)
    counters["unique_id"] = len(uniq)
    counters["cross_stock_id_conflicts"] = len(conflicts)

    firsts: list[dict] = []
    fwp_flags: dict = {}
    cls_count: dict = {}
    for r in uniq:
        c = classify_event_title(r.get("title", ""))
        cls_count[c] = cls_count.get(c, 0) + 1
        if c in (CLS_FIRST, CLS_FWP):
            firsts.append(r)
            fwp_flags[r.get("announcement_id")] = (c == CLS_FWP)
        else:
            rejects.append({"announcement_id": r.get("announcement_id"), "reason": c})
    counters["class"] = cls_count

    firsts, ratio_override = _apply_adjudication(firsts, fwp_flags, adjudication, rejects)
    counters["after_adjudication"] = len(firsts)

    def _order_key(r):
        return (r.get("valid_time") or "", str(r.get("announcement_id")))

    strong_seen: set = set()
    drop_ids: set = set()
    for r in sorted(firsts, key=_order_key):
        k = (r.get("stock_code"), r.get("holder_name"),
             r.get("reduce_period_start"), r.get("reduce_period_end"))
        if all(v for v in k):
            if k in strong_seen:
                rejects.append({"announcement_id": r.get("announcement_id"),
                                "reason": "same_plan_strong_key"})
                drop_ids.add(r.get("announcement_id"))
            else:
                strong_seen.add(k)
    firsts = [r for r in firsts if r.get("announcement_id") not in drop_ids]
    counters["after_strong_key"] = len(firsts)

    qualified: list[dict] = []
    for r in firsts:
        aid = r.get("announcement_id")
        ratio = ratio_override.get(aid, r.get("reduce_ratio_max_pct"))
        if ratio is None:
            rejects.append({"announcement_id": aid, "reason": "ratio_unparsed_fail_closed"})
        elif ratio < gate_ratio_pct:
            rejects.append({"announcement_id": aid, "reason": "ratio_below_gate"})
        else:
            qualified.append(r)
    counters["after_ratio_gate"] = len(qualified)

    midkey_pairs = _midkey_diagnostics(firsts, midkey_diag_window_days)
    counters["midkey_diag_pairs"] = len(midkey_pairs)

    events: dict = {}
    for r in qualified:
        key = (r.get("ts_code"), bj_event_date(r["valid_time"]).isoformat())
        e = events.setdefault(key, {"ts_code": key[0], "event_date": key[1],
                                    "n_ann": 0, "announcement_ids": []})
        e["n_ann"] += 1
        e["announcement_ids"].append(r.get("announcement_id"))
    counters["events"] = len(events)
    return {"events": [events[k] for k in sorted(events)],
            "rejects": rejects, "conflicts": conflicts, "counters": counters,
            "diagnostics": {"midkey_candidates_30d": midkey_pairs}}
