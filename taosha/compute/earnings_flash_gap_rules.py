"""exp17 冻结 A1/B1/C1 事件规则；纯函数、Decimal、零 I/O。"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from decimal import Decimal, InvalidOperation


RESEARCH_START = dt.date(2011, 1, 1)
RESEARCH_END = dt.date(2024, 7, 1)
DIRECTIONS = ("up", "down")
CLASS_KEYS = (
    "orphan", "no_strict_prior", "no_complete_prior", "forecast_conflict",
    "actual_null", "up", "down", "inside", "boundary",
)


def _decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _study_express_groups(rows: list[dict]) -> tuple[dict, dict]:
    eligible = [row for row in rows if row.get("ann_date") is not None
                and RESEARCH_START <= row["ann_date"] < RESEARCH_END]
    groups = {}
    for row in eligible:
        groups.setdefault((row["ts_code"], row.get("end_date")), []).append(row)
    accepted, rejects = {}, {"flag0_missing": 0, "flag0_multiple": 0}
    for key, members in sorted(groups.items()):
        initial = [row for row in members if str(row.get("update_flag")) == "0"]
        if not initial:
            rejects["flag0_missing"] += 1
        elif len(initial) != 1:
            rejects["flag0_multiple"] += 1
        else:
            accepted[key] = initial[0]
    return accepted, {"eligible_rows": len(eligible), "groups": len(groups), **rejects}


def _forecast_index(rows: list[dict]) -> dict:
    index = {}
    for row in rows:
        if row.get("ann_date") is not None:
            index.setdefault((row["ts_code"], row.get("end_date")), []).append(row)
    for members in index.values():
        members.sort(key=lambda row: (row["ann_date"],
                                     str(row.get("net_profit_min")),
                                     str(row.get("net_profit_max"))))
    return index


def _choose_interval(express: dict, forecasts: list[dict]) -> tuple[str, dict | None]:
    if not forecasts:
        return "orphan", None
    prior = [row for row in forecasts if row["ann_date"] < express["ann_date"]]
    if not prior:
        return "no_strict_prior", None
    complete = []
    for row in prior:
        lower, upper = _decimal(row.get("net_profit_min")), _decimal(row.get("net_profit_max"))
        if lower is not None and upper is not None and lower <= upper:
            complete.append((row, lower, upper))
    if not complete:
        return "no_complete_prior", None
    latest = max(item[0]["ann_date"] for item in complete)
    latest_rows = [(row, lower, upper) for row, lower, upper in complete
                   if row["ann_date"] == latest]
    intervals = {(lower, upper) for _, lower, upper in latest_rows}
    if len(intervals) != 1:
        return "forecast_conflict", None
    lower, upper = next(iter(intervals))
    return "ok", {"forecast_ann_date": latest, "lower": lower, "upper": upper}


def _classify(express: dict, interval: dict) -> tuple[str, Decimal | None]:
    income = _decimal(express.get("n_income"))
    if income is None:
        return "actual_null", None
    actual = income / Decimal("10000")
    if actual > interval["upper"]:
        return "up", actual
    if actual < interval["lower"]:
        return "down", actual
    if actual == interval["lower"] or actual == interval["upper"]:
        return "boundary", actual
    return "inside", actual


def _selection_sha(events: list[dict]) -> str:
    payload = [{"ts_code": row["ts_code"], "event_date": row["event_date"].isoformat(),
                "direction": row["direction"], "end_date": row["end_date"].isoformat()}
               for row in events]
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _finalize(directed: list[dict]) -> tuple[list[dict], dict]:
    by_key = {}
    for row in directed:
        by_key.setdefault((row["ts_code"], row["event_date"]), []).append(row)
    final, duplicate_groups = [], 0
    direction_conflicts = duplicate_rows = 0
    for _, members in sorted(by_key.items()):
        if len(members) != 1:
            duplicate_groups += 1
            duplicate_rows += len(members)
            direction_conflicts += int(len({row["direction"] for row in members}) > 1)
            continue
        final.append(members[0])
    return final, {"event_key_duplicate_groups": duplicate_groups,
                   "event_key_duplicate_rows_dropped": duplicate_rows,
                   "direction_conflict_groups": direction_conflicts}


def select_events(express_rows: list[dict], forecast_rows: list[dict]) -> dict:
    """两条事实腿 → 冻结事件集与互斥漏斗。"""
    accepted, group_stats = _study_express_groups(express_rows)
    forecasts = _forecast_index(forecast_rows)
    classes = {key: 0 for key in CLASS_KEYS}
    yearly, directed = {}, []
    same_day_forecast_groups = 0
    for key, express in accepted.items():
        members = forecasts.get(key, [])
        same_day_forecast_groups += int(any(
            row["ann_date"] == express["ann_date"] for row in members))
        classification, interval = _choose_interval(express, members)
        actual = None
        if classification == "ok":
            classification, actual = _classify(express, interval)
        classes[classification] += 1
        year = str(express["ann_date"].year)
        yearly.setdefault(year, {key: 0 for key in ("up", "down", "inside", "boundary")})
        if classification in yearly[year]:
            yearly[year][classification] += 1
        if classification in DIRECTIONS:
            directed.append({
                "ts_code": express["ts_code"], "end_date": express["end_date"],
                "event_date": express["ann_date"], "direction": classification,
                "forecast_ann_date": interval["forecast_ann_date"],
                "lower": interval["lower"], "upper": interval["upper"],
                "actual_wan": actual,
            })
    final, event_rejects = _finalize(directed)
    counters = {
        "input_express_rows": len(express_rows), "input_forecast_rows": len(forecast_rows),
        "study_express_rows": group_stats["eligible_rows"],
        "report_groups": group_stats["groups"],
        "flag0_missing_groups": group_stats["flag0_missing"],
        "flag0_multiple_groups": group_stats["flag0_multiple"],
        "b1_rejected_groups": group_stats["flag0_missing"] + group_stats["flag0_multiple"],
        "b1_surviving_groups": len(accepted), "same_day_forecast_groups": same_day_forecast_groups,
        **classes, "directed_group_rows": len(directed), **event_rejects,
        "final_events": len(final),
        "final_up": sum(row["direction"] == "up" for row in final),
        "final_down": sum(row["direction"] == "down" for row in final),
    }
    class_identity = len(accepted) == sum(classes.values())
    event_identity = len(directed) == len(final) + event_rejects["event_key_duplicate_rows_dropped"]
    yearly_identity = len(final) == sum(counters[f"final_{d}"] for d in DIRECTIONS)
    if not class_identity or not event_identity or not yearly_identity:
        raise ValueError("exp17 漏斗恒等式不成立")
    return {"events": final, "counters": counters, "classification_yearly": yearly,
            "classification_identity_ok": class_identity,
            "event_identity_ok": event_identity, "yearly_identity_ok": yearly_identity,
            "selection_sha256": _selection_sha(final)}
