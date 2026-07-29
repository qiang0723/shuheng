"""exp568 普通状态→ST/风险警示实施事件识别（纯函数，零 I/O）。

事件口径来自冻结 PAP ``st-imposition-pap-final-2026-07-29.json``：
按 ``(ts_code, start_date)`` 折叠名称段，只接受普通→ST；公告锚冲突、
状态不可判、公告晚于生效日和事件键重复均 fail-closed。带星/不带星只做
NOT_FOR_VERDICT 组成审计，不形成收益分层。

名称定级、段折叠与跨票聚合复用 exp12 同源实现，反向事件规则留在本模块，
不改动 exp12 的冻结行为。
"""
from __future__ import annotations

from taosha.compute.st_removal_rules import (
    ANN_DATE_END,
    ANN_DATE_START,
    fold_segments,
    has_star,
    merge_selections,
    name_state,
)

REASON_UNJUDGEABLE = "state_unjudgeable_fail_closed"
REASON_ANCHOR_MISSING = "anchor_missing"
REASON_ANCHOR_CONFLICT = "anchor_conflict_fail_closed"
REASON_ANN_AFTER_START = "ann_after_start_fail_closed"
REASON_OUT_OF_PERIOD = "out_of_period"
REASON_DUPLICATE_KEY = "event_key_duplicate_fail_closed"


def _transition_record(ts_code: str, prev: dict, cur: dict) -> dict:
    anchor = cur["anns"][0] if len(cur["anns"]) == 1 else None
    return {
        "ts_code": ts_code,
        "prev_start_date": prev["start_date"].isoformat(),
        "prev_names": prev["names"],
        "prev_state": prev["state"],
        "cur_start_date": cur["start_date"].isoformat(),
        "cur_names": cur["names"],
        "cur_state": cur["state"],
        "ann_date": anchor.isoformat() if anchor else None,
        "anns_distinct": [d.isoformat() for d in cur["anns"]],
        "gap_days": (cur["start_date"] - anchor).days if anchor else None,
        "st_variant": "starred" if cur["star_any"] else "plain_st",
    }


def run_funnel(ts_code: str, rows: list[dict]) -> dict:
    """识别单票普通→ST事件并返回事件、逐条剔除及互斥漏斗计数。"""
    segments, start_missing = fold_segments(rows)
    counters = {
        "input_rows": len(rows),
        "start_missing_rows": start_missing,
        "segments": len(segments),
        "transitions_with_prev": max(len(segments) - 1, 0),
        "imposition_candidates": 0,
        REASON_UNJUDGEABLE: 0,
        REASON_ANCHOR_MISSING: 0,
        REASON_ANCHOR_CONFLICT: 0,
        REASON_ANN_AFTER_START: 0,
        REASON_OUT_OF_PERIOD: 0,
        "duplicate_event_keys": 0,
        REASON_DUPLICATE_KEY: 0,
        "final_events": 0,
        "starred_events": 0,
        "plain_st_events": 0,
    }
    survivors: list[dict] = []
    rejects: list[dict] = []

    for index in range(1, len(segments)):
        prev, cur = segments[index - 1], segments[index]
        clean = prev["state"] == "normal" and cur["state"] == "st"
        unjudgeable = (
            "mixed" in (prev["state"], cur["state"])
            and any(name_state(name) == "normal" for name in prev["names"])
            and any(name_state(name) == "st" for name in cur["names"])
        )
        if not (clean or unjudgeable):
            continue

        counters["imposition_candidates"] += 1
        record = _transition_record(ts_code, prev, cur)
        if unjudgeable:
            counters[REASON_UNJUDGEABLE] += 1
            rejects.append(dict(record, reason=REASON_UNJUDGEABLE))
            continue
        if not cur["anns"]:
            counters[REASON_ANCHOR_MISSING] += 1
            rejects.append(dict(record, reason=REASON_ANCHOR_MISSING))
            continue
        if len(cur["anns"]) > 1:
            counters[REASON_ANCHOR_CONFLICT] += 1
            rejects.append(dict(record, reason=REASON_ANCHOR_CONFLICT))
            continue

        anchor = cur["anns"][0]
        if anchor > cur["start_date"]:
            counters[REASON_ANN_AFTER_START] += 1
            rejects.append(dict(record, reason=REASON_ANN_AFTER_START))
            continue
        if not (ANN_DATE_START <= anchor < ANN_DATE_END):
            counters[REASON_OUT_OF_PERIOD] += 1
            rejects.append(dict(record, reason=REASON_OUT_OF_PERIOD))
            continue
        survivors.append(record)

    events: list[dict] = []
    by_anchor: dict[str, list[dict]] = {}
    for record in survivors:
        by_anchor.setdefault(record["ann_date"], []).append(record)
    for anchor in sorted(by_anchor):
        group = by_anchor[anchor]
        if len(group) > 1:
            counters["duplicate_event_keys"] += 1
            counters[REASON_DUPLICATE_KEY] += len(group)
            rejects.extend(dict(record, reason=REASON_DUPLICATE_KEY,
                                n_colliding=len(group)) for record in group)
            continue
        event = group[0]
        counters["final_events"] += 1
        counters[f"{event['st_variant']}_events"] += 1
        events.append(event)

    return {"events": events, "rejects": rejects, "counters": counters}


def funnel_identity_ok(counters: dict) -> bool:
    rejected = sum(counters[key] for key in (
        REASON_UNJUDGEABLE,
        REASON_ANCHOR_MISSING,
        REASON_ANCHOR_CONFLICT,
        REASON_ANN_AFTER_START,
        REASON_OUT_OF_PERIOD,
        REASON_DUPLICATE_KEY,
    ))
    return counters["imposition_candidates"] - rejected == counters["final_events"]


def composition_identity_ok(counters: dict) -> bool:
    return (counters["starred_events"] + counters["plain_st_events"]
            == counters["final_events"])


def select_st_imposition_events(ts_code: str, rows: list[dict]) -> dict:
    return run_funnel(ts_code, rows)


__all__ = [
    "composition_identity_ok",
    "funnel_identity_ok",
    "merge_selections",
    "run_funnel",
    "select_st_imposition_events",
]
