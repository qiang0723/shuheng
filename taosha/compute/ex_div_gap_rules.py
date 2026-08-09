"""exp14 A1/B1/C1/D1 冻结前事件侧对账规则；纯函数、Decimal、零 I/O。"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from collections import Counter
from decimal import Decimal, InvalidOperation


RESEARCH_START = dt.date(2011, 1, 1)
RESEARCH_END = dt.date(2024, 7, 1)
THRESHOLD = Decimal("0.5")
COMPARE_FIELDS = (
    "ex_date", "stk_div", "stk_bo_rate", "stk_co_rate", "imp_ann_date", "record_date",
)
GROUP_REASONS = (
    "required_invalid", "timing_invalid", "component_invalid",
    "multi_null", "multi_conflict", "qualified",
)
FACTOR_REASONS = (
    "calendar_missing", "current_missing", "previous_missing",
    "factor_invalid", "factor_static", "factor_changed",
)


def _decimal(value):
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _member(row: dict) -> tuple[str, dict | None]:
    required = ("end_date", "ex_date", "imp_ann_date", "stk_div")
    if any(row.get(key) is None for key in required):
        return "required_invalid", None
    if row["imp_ann_date"] >= row["ex_date"]:
        return "timing_invalid", None
    total = _decimal(row.get("stk_div"))
    bonus, capital = _decimal(row.get("stk_bo_rate")), _decimal(row.get("stk_co_rate"))
    raw_bonus, raw_capital = row.get("stk_bo_rate"), row.get("stk_co_rate")
    invalid_number = total is None or (raw_bonus is not None and bonus is None)
    invalid_number |= raw_capital is not None and capital is None
    if invalid_number or (raw_bonus is None and raw_capital is None):
        return "component_invalid", None
    if total != (bonus or Decimal(0)) + (capital or Decimal(0)):
        return "component_invalid", None
    return "ok", {**row, "_total": total, "_bonus": bonus, "_capital": capital}


def _signature(row: dict) -> tuple:
    return (
        row["ex_date"], row["_total"], row["_bonus"], row["_capital"],
        row["imp_ann_date"], row["record_date"],
    )


def _fold_group(members: list[dict]) -> tuple[str, dict | None]:
    normalized = []
    for row in members:
        reason, clean = _member(row)
        if reason != "ok":
            return reason, None
        normalized.append(clean)
    if len(normalized) == 1:
        return "qualified", normalized[0]
    if any(row.get(field) is None for row in members for field in COMPARE_FIELDS):
        return "multi_null", None
    if len({_signature(row) for row in normalized}) != 1:
        return "multi_conflict", None
    normalized.sort(key=lambda row: tuple(str(row.get(key)) for key in sorted(row)))
    return "qualified", normalized[0]


def _implementation_rows(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row.get("div_proc") == "实施"
            and row.get("ex_date") is not None
            and RESEARCH_START <= row["ex_date"] < RESEARCH_END
            and str(row.get("ts_code", "")).endswith((".SH", ".SZ"))]


def _unique_event_keys(events: list[dict]) -> tuple[list[dict], dict]:
    groups = {}
    for row in events:
        groups.setdefault((row["ts_code"], row["ex_date"]), []).append(row)
    final, duplicate_groups = [], 0
    duplicate_rows = 0
    for _, members in sorted(groups.items()):
        if len(members) != 1:
            duplicate_groups += 1
            duplicate_rows += len(members)
        else:
            final.append(members[0])
    return final, {"event_key_duplicate_groups": duplicate_groups,
                   "event_key_duplicate_rows_dropped": duplicate_rows}


def prepare_events(rows: list[dict]) -> dict:
    """dividend忠实行 → B1/Decimal/事件键存活候选；尚未应用A1因子门。"""
    scoped = _implementation_rows(rows)
    groups = {}
    for row in scoped:
        groups.setdefault((row["ts_code"], row.get("end_date")), []).append(row)
    reasons = Counter({key: 0 for key in GROUP_REASONS})
    accepted = []
    multi_groups = 0
    for _, members in sorted(groups.items()):
        multi_groups += int(len(members) > 1)
        reason, row = _fold_group(members)
        reasons[reason] += 1
        if row is not None:
            accepted.append(row)
    threshold = [row for row in accepted if row["_total"] >= THRESHOLD]
    candidates, duplicates = _unique_event_keys(threshold)
    counters = {
        "input_rows": len(rows), "implementation_rows": len(scoped),
        "implementation_groups": len(groups), "multirow_groups": multi_groups,
        **{f"group_{key}": reasons[key] for key in GROUP_REASONS},
        "below_threshold_groups": len(accepted) - len(threshold),
        "threshold_groups": len(threshold),
        "threshold_exact_boundary_groups": sum(row["_total"] == THRESHOLD for row in threshold),
        **duplicates, "pre_factor_candidates": len(candidates),
    }
    identities = {
        "group": len(groups) == sum(reasons.values()),
        "threshold": len(accepted) == counters["below_threshold_groups"] + len(threshold),
        "event_key": len(threshold) == len(candidates) + duplicates[
            "event_key_duplicate_rows_dropped"],
    }
    if not all(identities.values()):
        raise ValueError(f"exp14基础漏斗恒等式不成立:{identities}")
    return {"candidates": candidates, "counters": counters, "identities": identities}


def _calendar_context(open_dates: list[dt.date]) -> tuple[list[dt.date], dict]:
    ordered = sorted(set(open_dates))
    previous = {day: ordered[index - 1] for index, day in enumerate(ordered) if index}
    return ordered, previous


def required_factor_keys(prepared: dict, open_dates: list[dt.date]) -> list[tuple]:
    """返回A1所需的最小因子键，供reader限量取数。"""
    _, previous = _calendar_context(open_dates)
    factor_keys = set()
    for event in prepared["candidates"]:
        day, code = event["ex_date"], event["ts_code"]
        if day in previous:
            factor_keys.update(((code, previous[day]), (code, day)))
    return sorted(factor_keys)


def _factor_index(rows: list[dict]) -> tuple[dict, dict]:
    groups = {}
    for row in rows:
        groups.setdefault((row["ts_code"], row["trade_date"]), []).append(row)
    values, duplicate_identical = {}, 0
    duplicate_conflict = 0
    for key, members in groups.items():
        parsed = {_decimal(row.get("adj_factor")) for row in members}
        if None in parsed or any(value <= 0 for value in parsed if value is not None):
            values[key] = None
        elif len(parsed) != 1:
            values[key] = None
            duplicate_conflict += 1
        else:
            values[key] = next(iter(parsed))
            duplicate_identical += int(len(members) > 1)
    return values, {"factor_input_rows": len(rows),
                    "factor_duplicate_identical_keys": duplicate_identical,
                    "factor_duplicate_conflict_keys": duplicate_conflict}


def _factor_reason(event: dict, factors: dict, previous: dict) -> str:
    day, code = event["ex_date"], event["ts_code"]
    if day not in previous:
        return "calendar_missing"
    current_key, prior_key = (code, day), (code, previous[day])
    if current_key not in factors:
        return "current_missing"
    if prior_key not in factors:
        return "previous_missing"
    if factors[current_key] is None or factors[prior_key] is None:
        return "factor_invalid"
    return "factor_static" if factors[current_key] == factors[prior_key] else "factor_changed"


def _selection_sha(events: list[dict]) -> str:
    payload = [{"ts_code": row["ts_code"], "event_date": row["ex_date"].isoformat(),
                "end_date": row["end_date"].isoformat(), "stk_div": str(row["_total"])}
               for row in events]
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _regime(day: dt.date) -> str:
    if day < dt.date(2017, 1, 1):
        return "pre_2017"
    if day < dt.date(2018, 11, 23):
        return "enforcement_transition"
    return "exchange_rule_period"


def _factor_ratio_audit(events: list[dict], factors: dict, previous: dict) -> dict:
    ratios = [factors[(event["ts_code"], event["ex_date"])] /
              factors[(event["ts_code"], previous[event["ex_date"]])]
              for event in events]
    return {
        "not_for_verdict": True,
        "events": len(ratios),
        "ratio_min": str(min(ratios)) if ratios else None,
        "ratio_mean": str(sum(ratios, Decimal(0)) / len(ratios)) if ratios else None,
        "ratio_max": str(max(ratios)) if ratios else None,
        "note": "除权日前一SSE开市日至除权日adj_factor比；仅机械审计，不进CAR或判决。",
    }


def finalize_events(prepared: dict, factor_rows: list[dict], open_dates: list[dt.date]) -> dict:
    """应用A1因子门；本单元不读取bar或收益。"""
    _, previous = _calendar_context(open_dates)
    factors, factor_stats = _factor_index(factor_rows)
    factor_reasons = Counter({key: 0 for key in FACTOR_REASONS})
    final = []
    for event in prepared["candidates"]:
        reason = _factor_reason(event, factors, previous)
        factor_reasons[reason] += 1
        if reason == "factor_changed":
            final.append(event)
    final.sort(key=lambda row: (row["ts_code"], row["ex_date"], row["end_date"]))
    yearly, regimes = Counter(), Counter()
    for event in final:
        yearly[str(event["ex_date"].year)] += 1
        regimes[_regime(event["ex_date"])] += 1
    counters = {**prepared["counters"], **factor_stats,
                **{f"factor_{key}": factor_reasons[key] for key in FACTOR_REASONS},
                "final_events": len(final),
                "final_exact_boundary": sum(row["_total"] == THRESHOLD for row in final)}
    identities = {**prepared["identities"],
                  "factor": prepared["counters"]["pre_factor_candidates"] == sum(
                      factor_reasons.values()),
                  "yearly": len(final) == sum(yearly.values()),
                  "regime": len(final) == sum(regimes.values())}
    if not all(identities.values()):
        raise ValueError(f"exp14最终漏斗恒等式不成立:{identities}")
    return {"events": final, "counters": counters, "identities": identities,
            "events_yearly": dict(yearly), "regulatory_composition": dict(regimes),
            "factor_mechanism_audit": _factor_ratio_audit(final, factors, previous),
            "selection_sha256": _selection_sha(final)}


def select_events(dividend_rows: list[dict], factor_rows: list[dict],
                  open_dates: list[dt.date]) -> dict:
    """fixture/小样本便利入口；生产recon分两段限量读取因子。"""
    return finalize_events(prepare_events(dividend_rows), factor_rows, open_dates)
