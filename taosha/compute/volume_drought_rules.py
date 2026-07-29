"""exp10 成交额干涸后首次放量且收阳事件识别（纯函数，零 I/O）。

冻结 PAP：volume-drought-break-pap-final-2026-07-29.json
digest=18d7322c8b4e2e14871a2d037516271892422cb0fa054a8e68697d0f8830aff1。
本模块只实现事件几何；不读事件后收益、不作统计判决、不写台账。
"""
from __future__ import annotations

import datetime as dt
import hashlib
from collections import deque
from decimal import Decimal


MA_DAYS = 60
MIN_LOW_DAYS = 5
LOW_RATIO = Decimal("0.30")
EVENT_DATE_START = dt.date(2011, 1, 1)
EVENT_DATE_END = dt.date(2024, 7, 1)

REASON_PRE2011 = "out_of_period_pre2011"
REASON_POST = "out_of_period_post"
REASON_DUPLICATE = "event_key_duplicate_fail_closed"


def _dec(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _new_counters() -> dict[str, int]:
    return {
        "input_rows": 0,
        "eligible_real_rows": 0,
        "invalid_real_bar_rows": 0,
        "insufficient_ma_rows": 0,
        "calendar_gap_breaks": 0,
        "armed_segments": 0,
        "armed_gap_breaks": 0,
        "armed_invalid_breaks": 0,
        "right_censored_armed": 0,
        "first_breakout_terminals": 0,
        "events_all_periods": 0,
        "breakout_not_positive_all_periods": 0,
        "armed_neutral_rows": 0,
        "exact_low_boundary": 0,
        "exact_breakout_boundary": 0,
    }


def _reset_stage(state: dict) -> None:
    state["low_run"] = 0
    state["low_start"] = None
    state["armed"] = False
    state["wait"] = 0


def _event(ts_code: str, row: dict, state: dict, ma: Decimal) -> dict:
    return {
        "ts_code": ts_code,
        "event_date": row["trade_date"].isoformat(),
        "low_start": state["low_start"].isoformat(),
        "low_days": state["low_run"],
        "wait_rows": state["wait"],
        "amount_to_prior_ma": str(_dec(row["amount"]) / ma),
    }


def select_volume_drought_events(ts_code: str, rows: list[dict]) -> dict:
    """单票状态机；rows 按交易日升序，cal_rank 为交易所开市日序号。

    prior60 可跨停牌，gap/异常 bar 只清 low_run 与 armed；当前 bar 永不进入自己的均量。
    返回全期事件、非收阳拒绝几何与互斥终局计数。
    """
    counters = _new_counters()
    prior: deque[Decimal] = deque(maxlen=MA_DAYS)
    state = {"low_run": 0, "low_start": None, "armed": False, "wait": 0}
    events: list[dict] = []
    rejected: list[dict] = []
    last_rank = None
    last_date = None

    for row in rows:
        counters["input_rows"] += 1
        trade_date = row["trade_date"]
        rank = int(row["cal_rank"])
        if last_date is not None and trade_date <= last_date:
            raise ValueError(f"{ts_code}: trade_date 非严格递增——fail-closed")
        if last_rank is not None and rank <= last_rank:
            raise ValueError(f"{ts_code}: cal_rank 非严格递增——fail-closed")
        if last_rank is not None and rank != last_rank + 1:
            counters["calendar_gap_breaks"] += 1
            if state["armed"]:
                counters["armed_gap_breaks"] += 1
            _reset_stage(state)
        last_date, last_rank = trade_date, rank

        amount, open_px, close_px = row.get("amount"), row.get("open"), row.get("close")
        if amount is None or _dec(amount) <= 0 or open_px is None or close_px is None:
            counters["invalid_real_bar_rows"] += 1
            if state["armed"]:
                counters["armed_invalid_breaks"] += 1
            _reset_stage(state)
            continue

        amount = _dec(amount)
        open_px, close_px = _dec(open_px), _dec(close_px)
        counters["eligible_real_rows"] += 1
        if len(prior) < MA_DAYS:
            counters["insufficient_ma_rows"] += 1
            prior.append(amount)
            continue

        ma = sum(prior) / MA_DAYS
        is_low = amount < LOW_RATIO * ma
        if amount == LOW_RATIO * ma:
            counters["exact_low_boundary"] += 1
        if amount == ma:
            counters["exact_breakout_boundary"] += 1

        if not state["armed"]:
            if is_low:
                if state["low_run"] == 0:
                    state["low_start"] = trade_date
                state["low_run"] += 1
                if state["low_run"] == MIN_LOW_DAYS:
                    state["armed"] = True
                    state["wait"] = 0
                    counters["armed_segments"] += 1
            else:
                _reset_stage(state)
        else:
            state["wait"] += 1
            if is_low:
                state["low_run"] += 1
            elif amount > ma:
                counters["first_breakout_terminals"] += 1
                if close_px > open_px:
                    counters["events_all_periods"] += 1
                    events.append(_event(ts_code, row, state, ma))
                else:
                    counters["breakout_not_positive_all_periods"] += 1
                    rejected.append({"ts_code": ts_code,
                                     "trade_date": trade_date.isoformat(),
                                     "reason": "first_breakout_not_positive"})
                _reset_stage(state)
            else:
                counters["armed_neutral_rows"] += 1
        prior.append(amount)

    if state["armed"]:
        counters["right_censored_armed"] += 1
    return {"events": events, "terminal_rejects": rejected, "counters": counters}


def merge_selections(per_security: list[dict], base_counters: dict | None = None) -> dict:
    events: list[dict] = []
    rejects: list[dict] = []
    counters = dict(base_counters or {})
    for selection in per_security:
        events.extend(selection["events"])
        rejects.extend(selection["terminal_rejects"])
        for key, value in selection["counters"].items():
            counters[key] = counters.get(key, 0) + value
    return {"events": events, "terminal_rejects": rejects, "counters": counters}


def finalize_events(merged: dict) -> dict:
    """事件键唯一性 fail-closed + 研究期过滤；selection SHA 与封存脚本同式。"""
    by_key: dict[tuple[str, str], list[dict]] = {}
    for event in merged["events"]:
        by_key.setdefault((event["ts_code"], event["event_date"]), []).append(event)

    final, rejects = [], list(merged["terminal_rejects"])
    duplicate_keys = 0
    for event in merged["events"]:
        group = by_key[(event["ts_code"], event["event_date"])]
        if len(group) > 1:
            rejects.append(dict(event, reason=REASON_DUPLICATE, n_colliding=len(group)))
            continue
        day = dt.date.fromisoformat(event["event_date"])
        if day < EVENT_DATE_START:
            rejects.append(dict(event, reason=REASON_PRE2011))
        elif day >= EVENT_DATE_END:
            rejects.append(dict(event, reason=REASON_POST))
        else:
            final.append(event)
    duplicate_keys = sum(1 for group in by_key.values() if len(group) > 1)

    reasons: dict[str, int] = {}
    for row in rejects:
        reasons[row["reason"]] = reasons.get(row["reason"], 0) + 1
    counters = dict(merged["counters"])
    counters["event_key_uniqueness_violations"] = duplicate_keys
    counters["uniqueness_dropped_events"] = sum(
        len(group) for group in by_key.values() if len(group) > 1)
    counters["events_pre2011"] = reasons.get(REASON_PRE2011, 0)
    counters["events_post"] = reasons.get(REASON_POST, 0)
    counters["events_study"] = len(final)
    counters["breakout_not_positive_pre2011"] = sum(
        1 for row in merged["terminal_rejects"]
        if dt.date.fromisoformat(row["trade_date"]) < EVENT_DATE_START)
    counters["breakout_not_positive_study"] = sum(
        1 for row in merged["terminal_rejects"]
        if EVENT_DATE_START <= dt.date.fromisoformat(row["trade_date"]) < EVENT_DATE_END)
    digest = hashlib.sha256()
    for event in final:
        digest.update(f"{event['ts_code']}|{event['event_date']}\n".encode())
    return {"events": final, "rejects": rejects, "counters": counters,
            "reject_reasons": reasons, "selection_sha256": digest.hexdigest()}
