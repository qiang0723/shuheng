"""holder_sell(exp4) 事件识别确定性规则 — 六类判别 + 首次计划识别/关联/去重(纯函数,零I/O)。
冻结于 §2B 盘面验收(2026-07-16 晨令验收点③):规则先冻结、后运行;未见任何事件研究结果。
口径出处:exp4 冻结 PAP(event_def=减持计划首次预披露公告,减持比例≥总股本1%;T+1日级;sample_gate=30=最小样本量门)。

六类(晨令口径):首次 / 修订 / 进展 / 时间过半 / 结果 / 终止。
判别策略 = 锚定正则 + 负语境掩码 + fail-closed 兜底:
  · 污染词须锚定"减持/计划"语境才判类(防"限售期满后减持…计划"真首次被误杀);
  · 含广义污染词但未命中任何锚定类 → suspect_unresolved,剔除并留痕(绝不静默进事件);
  · 混合标题(旧计划收尾暨后续新计划预披露)→ combo_ambiguous,剔除并留痕(单标签必错一半,诚实弃用)。
"""
from __future__ import annotations

import datetime as dt
import re

# ── 负语境掩码:非"减持计划"语境的期满/届满(限售期满后减持=真首次) ────────────
_RE_MASK = re.compile(r"(限售|锁定|解禁|禁售|持有)[^，。；]{0,8}?(期满|届满)")

# ── 六类锚定正则(优先序自上而下,首中即判) ─────────────────────────────────
_RE_REVISION = re.compile(
    r"更正|修订|补充"
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
    r"|减持(股份)?计划[^，。；]{0,8}(期满|届满)"
    r"|期满未减持"
    r"|减持(股份)?(计划)?[^，。；]{0,4}完毕"
    r"|减持完成")
# 混合标题指示:污染核心命中 且 出现"暨/及(后续|未来|新)…预披露"式新计划并披指示
_RE_NEWPLAN_IND = re.compile(
    r"(暨|及)[^，。；]{0,16}预披露|(后续|未来|新)[^，。；]{0,12}减持[^，。；]{0,10}预披露")
# 广义污染词(fail-closed 兜底面)
_RE_BROAD = re.compile(r"过半|进展|期满|届满|结果|完毕|完成|终止|结束|更正|修订|补充|变更|调整|延期|实施")

CLS_FIRST = "first_candidate"
CLS_REVISION = "revision"
CLS_TERMINATION = "termination"
CLS_HALFWAY = "halfway"
CLS_PROGRESS = "progress"
CLS_RESULT = "result"
CLS_COMBO = "combo_ambiguous"
CLS_SUSPECT = "suspect_unresolved"

#: 除首次外全部为污染/剔除类
POLLUTION_CLASSES = (CLS_REVISION, CLS_TERMINATION, CLS_HALFWAY,
                     CLS_PROGRESS, CLS_RESULT, CLS_COMBO, CLS_SUSPECT)


def classify_event_title(title: str) -> str:
    """标题 → 六类+两剔除类。确定性:纯文本、无外部状态。"""
    t = re.sub(r"\s+", "", title or "")
    t = _RE_MASK.sub("◇", t)
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
    if _RE_BROAD.search(t):
        return CLS_SUSPECT
    return CLS_FIRST


_BJT = dt.timezone(dt.timedelta(hours=8))


def bj_event_date(valid_time_iso: str) -> dt.date:
    """UTC ISO 时间戳 → 京时日历日(事件日)。PAP=T+1 日级无盘中分支:盘中/盘后/源侧日级零点同口径取京时日期。"""
    return dt.datetime.fromisoformat(valid_time_iso).astimezone(_BJT).date()


def select_first_events(rows: list[dict], gate_ratio_pct: float = 1.0,
                        same_plan_window_days: int = 30) -> dict:
    """冻结语料行 → 首次计划事件集(确定性首次识别/关联/去重,PAP 1%门)。

    步骤(顺序即口径,单一剔除理由留痕):
      1 去重: announcement_id 唯一,保输入序首条(跨票同id=同一公告归属冲突,记 conflicts);
      2 类判别: 仅 first_candidate 进入,其余按类记剔除;
      3 同计划强键关联: (票,股东,减持期起,止) 全解析同键 → 保最早(valid_time,id),余剔;
      4 同计划中键关联: (票,股东,比例) 解析同键且距已保留条 ≤window 日 → 同计划再披,剔;
      5 比例门(PAP冻结): reduce_ratio_max_pct 解析且 ≥ gate_ratio_pct;未解析=不可证≥1% → fail-closed 剔;
      6 事件发射: 唯一 (ts_code, 京时事件日)(同日多股东多计划=同一市场事件日,n_ann 记数)。
    返回 {events, rejects, conflicts, counters};零I/O、零随机,输入确定输出。
    """
    counters: dict = {"input": len(rows)}
    rejects: list[dict] = []
    seen_ids: dict = {}
    conflicts: list[dict] = []
    uniq: list[dict] = []
    for r in rows:
        aid = r.get("announcement_id")
        if aid in seen_ids:
            prev = seen_ids[aid]
            if prev.get("stock_code") != r.get("stock_code"):
                conflicts.append({"announcement_id": aid,
                                  "kept": prev.get("stock_code"),
                                  "dropped": r.get("stock_code")})
            rejects.append({"announcement_id": aid, "reason": "dup_announcement_id"})
            continue
        seen_ids[aid] = r
        uniq.append(r)
    counters["unique_id"] = len(uniq)
    counters["cross_stock_id_conflicts"] = len(conflicts)

    firsts: list[dict] = []
    cls_count: dict = {}
    for r in uniq:
        c = classify_event_title(r.get("title", ""))
        cls_count[c] = cls_count.get(c, 0) + 1
        if c == CLS_FIRST:
            firsts.append(r)
        else:
            rejects.append({"announcement_id": r.get("announcement_id"), "reason": c})
    counters["class"] = cls_count

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

    mid_kept: dict = {}
    drop_ids = set()
    for r in sorted(firsts, key=_order_key):
        h, ratio = r.get("holder_name"), r.get("reduce_ratio_max_pct")
        if not h or ratio is None:
            continue
        k = (r.get("stock_code"), h, ratio)
        d = bj_event_date(r["valid_time"])
        last = mid_kept.get(k)
        if last is not None and (d - last).days <= same_plan_window_days:
            rejects.append({"announcement_id": r.get("announcement_id"),
                            "reason": "same_plan_midkey_window"})
            drop_ids.add(r.get("announcement_id"))
        else:
            mid_kept[k] = d
    firsts = [r for r in firsts if r.get("announcement_id") not in drop_ids]
    counters["after_mid_key"] = len(firsts)

    qualified: list[dict] = []
    for r in firsts:
        ratio = r.get("reduce_ratio_max_pct")
        if ratio is None:
            rejects.append({"announcement_id": r.get("announcement_id"),
                            "reason": "ratio_unparsed_fail_closed"})
        elif ratio < gate_ratio_pct:
            rejects.append({"announcement_id": r.get("announcement_id"),
                            "reason": "ratio_below_gate"})
        else:
            qualified.append(r)
    counters["after_ratio_gate"] = len(qualified)

    events: dict = {}
    for r in qualified:
        key = (r.get("ts_code"), bj_event_date(r["valid_time"]).isoformat())
        e = events.setdefault(key, {"ts_code": key[0], "event_date": key[1],
                                    "n_ann": 0, "announcement_ids": []})
        e["n_ann"] += 1
        e["announcement_ids"].append(r.get("announcement_id"))
    counters["events"] = len(events)
    return {"events": [events[k] for k in sorted(events)],
            "rejects": rejects, "conflicts": conflicts, "counters": counters}
