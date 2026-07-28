"""exp24 SOX→A股半导体同向溢出事件规则（纯函数、Decimal、零 I/O）。"""
from __future__ import annotations

import datetime as dt
from bisect import bisect_left
from collections import Counter, defaultdict
from decimal import Decimal

THRESHOLD = Decimal("0.03")
INDEX_CODE = "801081.SI"
PERIOD_START = dt.date(2011, 1, 1)
PERIOD_END = dt.date(2024, 7, 1)


def _decimal(value) -> Decimal | None:
    if value is None:
        return None
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _unique_sox_rows(rows: list[dict]) -> list[dict]:
    ordered = sorted(rows, key=lambda r: r["trade_date"])
    dates = [r["trade_date"] for r in ordered]
    if len(dates) != len(set(dates)):
        dup = sorted(d for d, n in Counter(dates).items() if n > 1)
        raise ValueError(f"SOX trade_date 重复 → fail-closed:{dup[:10]}")
    return ordered


def detect_triggers(rows: list[dict]) -> tuple[list[dict], dict]:
    """相邻 SOX 数据行算 close return；|r|>=3% 闭区间触发。"""
    ordered = _unique_sox_rows(rows)
    triggers = []
    missing_close = 0
    empty_currency = 0
    for i, row in enumerate(ordered):
        if row.get("currency") == "":
            empty_currency += 1
        close = _decimal(row.get("close"))
        if close is None:
            missing_close += 1
        if i == 0:
            continue
        prev = _decimal(ordered[i - 1].get("close"))
        if close is None or prev in (None, Decimal("0")):
            continue
        ret = close / prev - Decimal("1")
        if abs(ret) < THRESHOLD:
            continue
        direction = "up" if ret > 0 else "down"
        triggers.append({"trigger_date": row["trade_date"], "return": ret,
                         "direction": direction, "direction_sign": 1 if ret > 0 else -1})
    by_dir = Counter(t["direction"] for t in triggers)
    return triggers, {
        "input_sox_rows": len(ordered),
        "missing_close_rows": missing_close,
        "empty_currency_rows": empty_currency,
        "triggers": len(triggers),
        "trigger_up": by_dir["up"],
        "trigger_down": by_dir["down"],
        "exact_boundary": sum(abs(t["return"]) == THRESHOLD for t in triggers),
    }


def map_and_drop_collisions(triggers: list[dict], a_share_dates: list[dt.date]) -> tuple[list[dict], dict]:
    """T→北京历日T+1起首个A股交易日；D4 同映射日多触发整组剔除。"""
    dates = sorted(a_share_dates)
    if len(dates) != len(set(dates)):
        raise ValueError("A股交易日轴含重复日期 → fail-closed")
    mapped = []
    unmapped = 0
    for trigger in triggers:
        start = trigger["trigger_date"] + dt.timedelta(days=1)
        idx = bisect_left(dates, start)
        if idx >= len(dates):
            unmapped += 1
            continue
        mapped.append({**trigger, "event_date": dates[idx]})
    groups: dict[dt.date, list[dict]] = defaultdict(list)
    for row in mapped:
        groups[row["event_date"]].append(row)
    collision_dates = {d: rs for d, rs in groups.items() if len(rs) > 1}
    kept = [rs[0] for d, rs in sorted(groups.items()) if len(rs) == 1]
    return kept, {
        "mapped_triggers": len(mapped),
        "mapped_dates": len(groups),
        "unmapped_triggers": unmapped,
        "collision_dates": len(collision_dates),
        "collision_triggers_dropped": sum(len(v) for v in collision_dates.values()),
        "collision_items": [
            {"event_date": d, "trigger_dates": [r["trigger_date"] for r in rs],
             "directions": [r["direction"] for r in rs]}
            for d, rs in sorted(collision_dates.items())],
    }


def _valid_members(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    valid, rejected = [], []
    for row in rows:
        reason = None
        if row.get("index_code") != INDEX_CODE:
            reason = "wrong_index"
        elif str(row.get("ts_code", "")).endswith(".BJ"):
            reason = "north_exchange"
        elif row.get("in_date") is None:
            reason = "missing_in_date"
        elif row.get("out_date") is not None and row["in_date"] >= row["out_date"]:
            reason = "invalid_interval"
        if reason:
            rejected.append({"reason": reason, **row})
        else:
            valid.append(row)
    return valid, rejected


def expand_members(mapped: list[dict], member_rows: list[dict]) -> tuple[list[dict], dict]:
    """按 event_date∈[in_date,out_date) 展开证券；重复事件键整组剔除。"""
    members, member_rejects = _valid_members(member_rows)
    candidates = []
    per_date = {}
    for trigger in mapped:
        event_date = trigger["event_date"]
        active = [m for m in members if m["in_date"] <= event_date
                  and (m.get("out_date") is None or event_date < m["out_date"])]
        per_date[event_date] = len({m["ts_code"] for m in active})
        for member in active:
            candidates.append({
                "ts_code": member["ts_code"], "event_date": event_date,
                "trigger_date": trigger["trigger_date"], "sox_return": trigger["return"],
                "direction": trigger["direction"], "direction_sign": trigger["direction_sign"],
            })
    by_key: dict[tuple, list[dict]] = defaultdict(list)
    for event in candidates:
        by_key[(event["ts_code"], event["event_date"])].append(event)
    dup_keys = {key: vals for key, vals in by_key.items() if len(vals) > 1}
    events = [vals[0] for key, vals in sorted(by_key.items()) if len(vals) == 1]
    return events, {
        "member_input_rows": len(member_rows),
        "member_valid_rows": len(members),
        "member_rejected_rows": len(member_rejects),
        "member_rejects": member_rejects,
        "expanded_candidates": len(candidates),
        "duplicate_event_keys": len(dup_keys),
        "duplicate_events_dropped": sum(len(v) for v in dup_keys.values()),
        "duplicate_items": [{"ts_code": k[0], "event_date": k[1], "n": len(v)}
                            for k, v in sorted(dup_keys.items())],
        "pool_members_by_event_date": dict(sorted(per_date.items())),
        "zero_member_event_dates": sum(n == 0 for n in per_date.values()),
    }


def select_events(sox_rows: list[dict], member_rows: list[dict],
                  a_share_dates: list[dt.date]) -> dict:
    """冻结规则总入口：触发→映射/D4→研究期→池展开。"""
    triggers, trigger_audit = detect_triggers(sox_rows)
    mapped, mapping_audit = map_and_drop_collisions(triggers, a_share_dates)
    in_period = [r for r in mapped if PERIOD_START <= r["event_date"] < PERIOD_END]
    events, member_audit = expand_members(in_period, member_rows)
    yearly = Counter(r["event_date"].year for r in in_period)
    directions = Counter(r["direction"] for r in in_period)
    counters = {
        **trigger_audit,
        **{k: v for k, v in mapping_audit.items() if k != "collision_items"},
        "out_of_period_mapped_dates": len(mapped) - len(in_period),
        "surviving_trigger_dates": len(in_period),
        "surviving_up": directions["up"],
        "surviving_down": directions["down"],
        **{k: v for k, v in member_audit.items()
           if k not in {"member_rejects", "duplicate_items", "pool_members_by_event_date"}},
        "final_events": len(events),
    }
    return {
        "events": events,
        "counters": counters,
        "trigger_yearly": dict(sorted(yearly.items())),
        "collision_items": mapping_audit["collision_items"],
        "member_rejects": member_audit["member_rejects"],
        "duplicate_items": member_audit["duplicate_items"],
        "pool_members_by_event_date": member_audit["pool_members_by_event_date"],
        "funnel_identity_ok": (
            counters["triggers"]
            == counters["mapped_triggers"] + counters["unmapped_triggers"]
            == counters["collision_triggers_dropped"] + counters["surviving_trigger_dates"]
               + counters["out_of_period_mapped_dates"]),
    }
