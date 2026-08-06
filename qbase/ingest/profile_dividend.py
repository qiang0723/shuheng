#!/usr/bin/env python3
"""exp19 dividend 全量质量画像；只读数据，不读取行情或收益。"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from qbase.ingest.dividend_common import HOLDOUT, SOURCE, required_env


def load_rows(dsn: str) -> tuple[int, list[dict]]:
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on",
                         row_factory=dict_row) as conn:
        batch_id = conn.execute(
            "SELECT max(batch_id) FROM fact_batch WHERE source=%s", (SOURCE,)
        ).fetchone()[0]
        if batch_id is None:
            raise RuntimeError("无tushare:dividend正式批次")
        rows = conn.execute(
            "SELECT ts_code,end_date,ann_date,div_proc,stk_div,stk_bo_rate,stk_co_rate,"
            "cash_div,cash_div_tax,record_date,ex_date,pay_date,div_listdate,imp_ann_date,"
            "base_date,base_share,update_flag FROM dividend_snap WHERE batch_id=%s "
            "ORDER BY ts_code,end_date,ann_date,div_proc,update_flag", (batch_id,)
        ).fetchall()
    return int(batch_id), [dict(row) for row in rows]


def annual_scope(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row["end_date"] and row["end_date"].month == 12
            and row["end_date"].day == 31 and row["ann_date"]
            and row["ann_date"] < HOLDOUT and not row["ts_code"].endswith(".BJ")]


def group_rows(rows: list[dict]) -> dict[tuple[str, date], list[dict]]:
    groups: dict[tuple[str, date], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["ts_code"], row["end_date"])].append(row)
    return dict(groups)


def classify_group(members: list[dict]) -> tuple[str, dict | None]:
    initial = [row for row in members
               if row["div_proc"] == "预案" and row["update_flag"] == "0"]
    if not initial:
        return "initial_missing", None
    if len(initial) > 1:
        signatures = {(row["ann_date"], row["cash_div_tax"], row["base_date"], row["base_share"])
                      for row in initial}
        return ("initial_multiple_conflict" if len(signatures) > 1
                else "initial_multiple_identical"), None
    row = initial[0]
    if row["ann_date"] is None or row["cash_div_tax"] is None:
        return "initial_required_null", None
    if row["cash_div_tax"] < 0:
        return "initial_negative_cash", None
    return "qualified", row


def yearly_increment(counter: dict[int, Counter], year: int, key: str) -> None:
    counter.setdefault(year, Counter())[key] += 1


def candidate_funnel(groups: dict, qualified: dict) -> tuple[Counter, dict[int, Counter]]:
    total = Counter()
    by_year: dict[int, Counter] = {}
    threshold = Decimal("0.50")
    for (ts_code, end_date), current in sorted(qualified.items()):
        ann_year = current["ann_date"].year
        prior_key = (ts_code, date(end_date.year - 1, 12, 31))
        if prior_key not in groups:
            outcome = "missing_prior_group"
        elif prior_key not in qualified:
            outcome = "unresolvable_prior"
        else:
            prior = qualified[prior_key]["cash_div_tax"]
            current_value = current["cash_div_tax"]
            if prior == 0:
                outcome = "zero_undefined"
            else:
                change = current_value / prior - Decimal(1)
                if change >= threshold:
                    outcome = "up"
                elif change <= -threshold:
                    outcome = "down"
                else:
                    outcome = "inside"
                if change in {threshold, -threshold}:
                    total["exact_boundary"] += 1
                    yearly_increment(by_year, ann_year, "exact_boundary")
        total[outcome] += 1
        yearly_increment(by_year, ann_year, outcome)
    return total, by_year


def build_profile(batch_id: int, rows: list[dict]) -> dict:
    scope = annual_scope(rows)
    groups = group_rows(scope)
    reasons = Counter()
    qualified = {}
    by_fiscal_year: dict[int, Counter] = {}
    implementation_only = 0
    for key, members in sorted(groups.items()):
        reason, initial = classify_group(members)
        reasons[reason] += 1
        yearly_increment(by_fiscal_year, key[1].year, "groups")
        yearly_increment(by_fiscal_year, key[1].year, reason)
        if initial is not None:
            qualified[key] = initial
        elif any(row["div_proc"] != "预案" and row["cash_div_tax"] is not None
                 for row in members):
            implementation_only += 1
            yearly_increment(by_fiscal_year, key[1].year, "later_value_without_initial")
    funnel, by_event_year = candidate_funnel(groups, qualified)
    stage = Counter(str(row["div_proc"]) if row["div_proc"] is not None else "NULL" for row in scope)
    flags = Counter(str(row["update_flag"]) if row["update_flag"] is not None else "NULL" for row in scope)
    exact_rows = len(rows) - len({tuple(row.values()) for row in rows})
    return {
        "source": SOURCE,
        "batch_id": batch_id,
        "all_rows": len(rows),
        "securities": len({row["ts_code"] for row in rows}),
        "source_ann_date_min": min((row["ann_date"] for row in rows if row["ann_date"]), default=None),
        "source_ann_date_max": max((row["ann_date"] for row in rows if row["ann_date"]), default=None),
        "exact_duplicate_rows_after_l1_dedup": exact_rows,
        "annual_scope_rows": len(scope),
        "annual_scope_groups": len(groups),
        "stage_rows": dict(sorted(stage.items())),
        "update_flag_rows": dict(sorted(flags.items())),
        "group_classification": dict(sorted(reasons.items())),
        "qualified_initial_groups": len(qualified),
        "later_value_without_initial_groups": implementation_only,
        "candidate_funnel_d1_c1": dict(sorted(funnel.items())),
        "by_fiscal_year": {str(year): dict(sorted(values.items()))
                           for year, values in sorted(by_fiscal_year.items())},
        "by_event_year": {str(year): dict(sorted(values.items()))
                          for year, values in sorted(by_event_year.items())},
        "rules": {
            "E1": "exactly one div_proc=预案 and update_flag=0 row",
            "A1": "cash_div_tax only",
            "C1": "prior=0/missing/unresolvable excluded; current=0 and prior>0 is -100%",
            "D1": "Decimal >=+50% / <=-50%",
            "implementation_backfill": "forbidden",
        },
    }


def json_default(value):
    if isinstance(value, (date, Decimal)):
        return str(value)
    raise TypeError(type(value).__name__)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    dsn = required_env("QBASE_APP_DSN")["QBASE_APP_DSN"]
    batch_id, rows = load_rows(dsn)
    profile = build_profile(batch_id, rows)
    Path(args.output).write_text(
        json.dumps(profile, ensure_ascii=False, indent=1, sort_keys=True,
                   default=json_default) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: profile[key] for key in (
        "batch_id", "all_rows", "annual_scope_groups", "qualified_initial_groups",
        "later_value_without_initial_groups")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
