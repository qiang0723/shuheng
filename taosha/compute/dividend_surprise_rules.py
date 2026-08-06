"""exp19 A1/B2-P1/C1/D1/E1 冻结事件规则；纯函数、Decimal、零 I/O。"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from collections import Counter
from decimal import Decimal, InvalidOperation


RESEARCH_START = dt.date(2021, 1, 1)
RESEARCH_END = dt.date(2024, 7, 1)
THRESHOLD = Decimal("0.50")
DIRECTIONS = ("up", "down")
CLASS_KEYS = ("missing_prior", "unresolvable_prior", "zero_undefined",
              "up", "down", "inside")


def _decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _annual_groups(rows: list[dict]) -> dict:
    groups = {}
    for row in rows:
        end, ann = row.get("end_date"), row.get("ann_date")
        if end is None or ann is None or end.month != 12 or end.day != 31:
            continue
        if ann >= RESEARCH_END or str(row.get("ts_code", "")).endswith(".BJ"):
            continue
        groups.setdefault((row["ts_code"], end), []).append(row)
    return groups


def _strict_initial_groups(groups: dict) -> tuple[dict, Counter]:
    accepted, reasons = {}, Counter()
    for key, members in sorted(groups.items()):
        initial = [row for row in members
                   if row.get("div_proc") == "预案" and str(row.get("update_flag")) == "0"]
        if not initial:
            reasons["initial_missing"] += 1
            reasons["later_value_without_initial"] += int(any(
                row.get("div_proc") != "预案" and _decimal(row.get("cash_div_tax")) is not None
                for row in members))
            continue
        if len(initial) != 1:
            signatures = {(row.get("ann_date"), str(row.get("cash_div_tax")),
                           row.get("base_date"), str(row.get("base_share")))
                          for row in initial}
            reason = ("initial_multiple_conflict" if len(signatures) > 1
                      else "initial_multiple_identical")
            reasons[reason] += 1
            continue
        row, value = initial[0], _decimal(initial[0].get("cash_div_tax"))
        if row.get("ann_date") is None or value is None or value < 0:
            reasons["initial_required_invalid"] += 1
            continue
        accepted[key] = dict(row, _cash_div_tax=value)
        reasons["qualified"] += 1
    return accepted, reasons


def _classify(key: tuple, current: dict, groups: dict, qualified: dict):
    ts_code, end_date = key
    prior_key = (ts_code, dt.date(end_date.year - 1, 12, 31))
    if prior_key not in groups:
        return "missing_prior", None
    if prior_key not in qualified:
        return "unresolvable_prior", None
    prior, value = qualified[prior_key]["_cash_div_tax"], current["_cash_div_tax"]
    if prior == 0:
        return "zero_undefined", None
    change = value / prior - Decimal(1)
    if change >= THRESHOLD:
        return "up", change
    if change <= -THRESHOLD:
        return "down", change
    return "inside", change


def _selection_sha(events: list[dict]) -> str:
    payload = [{"ts_code": row["ts_code"], "event_date": row["event_date"].isoformat(),
                "direction": row["direction"], "end_date": row["end_date"].isoformat()}
               for row in events]
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _finalize(events: list[dict]) -> tuple[list[dict], dict]:
    by_key = {}
    for row in events:
        by_key.setdefault((row["ts_code"], row["event_date"]), []).append(row)
    final, duplicate_groups = [], 0
    duplicate_rows = direction_conflicts = 0
    for _, members in sorted(by_key.items()):
        if len(members) != 1:
            duplicate_groups += 1
            duplicate_rows += len(members)
            direction_conflicts += int(len({row["direction"] for row in members}) > 1)
        else:
            final.append(members[0])
    return final, {"event_key_duplicate_groups": duplicate_groups,
                   "event_key_duplicate_rows_dropped": duplicate_rows,
                   "direction_conflict_groups": direction_conflicts}


def select_events(rows: list[dict]) -> dict:
    """L1 dividend 行 → 冻结事件集、全期/研究期互斥漏斗与确定性 SHA。"""
    groups = _annual_groups(rows)
    qualified, group_reasons = _strict_initial_groups(groups)
    full = Counter({key: 0 for key in CLASS_KEYS})
    research = Counter({key: 0 for key in CLASS_KEYS})
    full_boundary = research_boundary = 0
    yearly, directed = {}, []
    for key, current in sorted(qualified.items()):
        classification, change = _classify(key, current, groups, qualified)
        full[classification] += 1
        full_boundary += int(change in {THRESHOLD, -THRESHOLD})
        ann = current["ann_date"]
        if not RESEARCH_START <= ann < RESEARCH_END:
            continue
        research[classification] += 1
        research_boundary += int(change in {THRESHOLD, -THRESHOLD})
        year = str(ann.year)
        yearly.setdefault(year, {name: 0 for name in CLASS_KEYS})
        yearly[year][classification] += 1
        if classification in DIRECTIONS:
            directed.append({"ts_code": current["ts_code"], "end_date": current["end_date"],
                             "event_date": ann, "direction": classification,
                             "current_cash_div_tax": current["_cash_div_tax"],
                             "change": change})
    final, duplicate_rejects = _finalize(directed)
    annual_rows = sum(len(members) for members in groups.values())
    counters = {
        "input_rows": len(rows), "annual_scope_rows": annual_rows,
        "annual_scope_groups": len(groups), "qualified_initial_groups": len(qualified),
        "initial_missing_groups": group_reasons["initial_missing"],
        "initial_multiple_identical_groups": group_reasons["initial_multiple_identical"],
        "initial_multiple_conflict_groups": group_reasons["initial_multiple_conflict"],
        "initial_required_invalid_groups": group_reasons["initial_required_invalid"],
        "later_value_without_initial_groups": group_reasons["later_value_without_initial"],
        "implementation_backfill_hits": 0,
        "full_period_classification": dict(full), "full_period_exact_boundary": full_boundary,
        "research_classification": dict(research),
        "research_exact_boundary": research_boundary, "directed_group_rows": len(directed),
        **duplicate_rejects, "final_events": len(final),
        "final_up": sum(row["direction"] == "up" for row in final),
        "final_down": sum(row["direction"] == "down" for row in final),
    }
    identities = {
        "group": len(groups) == sum(group_reasons[name] for name in (
            "qualified", "initial_missing", "initial_multiple_identical",
            "initial_multiple_conflict", "initial_required_invalid")),
        "full_classification": len(qualified) == sum(full.values()),
        "research_classification": sum(research.values()) == sum(
            1 for row in qualified.values() if RESEARCH_START <= row["ann_date"] < RESEARCH_END),
        "event": len(directed) == len(final) + duplicate_rejects["event_key_duplicate_rows_dropped"],
        "direction": len(final) == counters["final_up"] + counters["final_down"],
    }
    if not all(identities.values()):
        raise ValueError(f"exp19 漏斗恒等式不成立:{identities}")
    return {"events": final, "counters": counters, "classification_yearly": yearly,
            "identities": identities, "selection_sha256": _selection_sha(final)}
