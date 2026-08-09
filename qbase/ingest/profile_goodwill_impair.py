#!/usr/bin/env python3
"""exp21 财务 PIT 与 forecast召回定位器全量画像；不判事件、不读收益。"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from qbase.ingest.balancesheet_common import HOLDOUT, SOURCE, required_env


def load_rows(dsn: str) -> tuple[int, list[dict], list[dict]]:
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on",
                         row_factory=dict_row) as conn:
        row = conn.execute(
            "SELECT max(batch_id) AS batch_id FROM fact_batch WHERE source=%s", (SOURCE,)
        ).fetchone()
        batch_id = row["batch_id"]
        if batch_id is None:
            raise RuntimeError("无tushare:balancesheet正式批次")
        balances = conn.execute(
            "SELECT ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,update_flag,"
            "goodwill,total_hldr_eqy_exc_min_int,total_hldr_eqy_inc_min_int "
            "FROM balancesheet_pit_snap WHERE batch_id=%s "
            "ORDER BY ts_code,end_date,f_ann_date,ann_date,report_type,update_flag", (batch_id,)
        ).fetchall()
        forecasts = conn.execute(
            "SELECT ts_code,ann_date,first_ann_date,end_date,summary,change_reason "
            "FROM forecast_snap WHERE batch_id=(SELECT max(batch_id) FROM fact_batch "
            "WHERE source='tushare:forecast') AND ann_date<DATE '2024-07-01' "
            "AND ts_code ~ '\\.(SH|SZ)$' AND (COALESCE(summary,'') ILIKE '%商誉%' "
            "OR COALESCE(change_reason,'') ILIKE '%商誉%') "
            "ORDER BY ann_date,ts_code,end_date"
        ).fetchall()
    return int(batch_id), [dict(item) for item in balances], [dict(item) for item in forecasts]


def disclosure_date(row: dict) -> date | None:
    return row["f_ann_date"] or row["ann_date"]


def in_scope(row: dict) -> bool:
    disclosed = disclosure_date(row)
    return bool(disclosed and disclosed < HOLDOUT and row["ts_code"]
                and row["ts_code"].endswith((".SH", ".SZ")))


def row_signature(row: dict) -> tuple:
    return tuple(row[key] for key in (
        "ts_code", "ann_date", "f_ann_date", "end_date", "report_type", "comp_type",
        "update_flag", "goodwill", "total_hldr_eqy_exc_min_int",
        "total_hldr_eqy_inc_min_int",
    ))


def group_profile(rows: list[dict]) -> tuple[Counter, dict[int, Counter]]:
    groups = defaultdict(list)
    for row in rows:
        groups[(row["ts_code"], row["end_date"])].append(row)
    totals, yearly = Counter(), defaultdict(Counter)
    for (_, end_date), members in sorted(groups.items(), key=str):
        year = end_date.year if end_date else 0
        totals["groups"] += 1
        yearly[year]["groups"] += 1
        bucket = "single_row_groups" if len(members) == 1 else "multirow_groups"
        totals[bucket] += 1
        yearly[year][bucket] += 1
        if len({row_signature(item) for item in members}) < len(members):
            totals["groups_with_exact_duplicates"] += 1
            yearly[year]["groups_with_exact_duplicates"] += 1
        if len({item["f_ann_date"] for item in members}) > 1:
            totals["groups_with_multiple_actual_dates"] += 1
            yearly[year]["groups_with_multiple_actual_dates"] += 1
        if len({item["report_type"] for item in members}) > 1:
            totals["groups_with_multiple_report_types"] += 1
            yearly[year]["groups_with_multiple_report_types"] += 1
    return totals, yearly


def denominator_status(locator: dict, balances: list[dict]) -> str:
    event_date = locator["ann_date"]
    eligible = [row for row in balances if row["ts_code"] == locator["ts_code"]
                and disclosure_date(row) and disclosure_date(row) < event_date]
    if not eligible:
        return "missing_prior_report"
    latest = max(disclosure_date(row) for row in eligible)
    same_day = [row for row in eligible if disclosure_date(row) == latest]
    values = {row["total_hldr_eqy_exc_min_int"] for row in same_day}
    if len(values) != 1 or len({row["report_type"] for row in same_day}) != 1:
        return "version_unresolvable"
    value = next(iter(values))
    if value is None:
        return "denominator_missing"
    if value == 0:
        return "denominator_zero"
    if value < 0:
        return "denominator_negative"
    return "denominator_positive"


def build_profile(batch_id: int, rows: list[dict], forecasts: list[dict]) -> dict:
    scope = [row for row in rows if in_scope(row)]
    group_totals, group_yearly = group_profile(scope)
    field_nulls = {field: sum(row[field] is None for row in scope) for field in (
        "ann_date", "f_ann_date", "end_date", "report_type", "update_flag", "goodwill",
        "total_hldr_eqy_exc_min_int", "total_hldr_eqy_inc_min_int",
    )}
    by_disclosure_year = defaultdict(Counter)
    for row in scope:
        year = disclosure_date(row).year
        by_disclosure_year[year]["rows"] += 1
        by_disclosure_year[year][f"report_type:{row['report_type'] or 'NULL'}"] += 1
        by_disclosure_year[year][f"update_flag:{row['update_flag'] or 'NULL'}"] += 1
    statuses, status_yearly = Counter(), defaultdict(Counter)
    for locator in forecasts:
        status = denominator_status(locator, scope)
        statuses[status] += 1
        status_yearly[locator["ann_date"].year][status] += 1
    return {
        "source": SOURCE, "batch_id": batch_id, "all_rows": len(rows),
        "scope_rows": len(scope), "scope_securities": len({row["ts_code"] for row in scope}),
        "disclosure_date_min": min((disclosure_date(row) for row in scope), default=None),
        "disclosure_date_max": max((disclosure_date(row) for row in scope), default=None),
        "l1_exact_duplicate_rows": len(rows) - len({row_signature(row) for row in rows}),
        "scope_field_null_rows": field_nulls,
        "report_period_group_profile": dict(sorted(group_totals.items())),
        "forecast_goodwill_locator_rows": len(forecasts),
        "forecast_goodwill_locator_groups": len({(row["ts_code"], row["end_date"])
                                                   for row in forecasts}),
        "locator_prior_equity_shape_nfv": dict(sorted(statuses.items())),
        "by_report_period_year": {str(year): dict(sorted(values.items()))
                                  for year, values in sorted(group_yearly.items())},
        "by_disclosure_year": {str(year): dict(sorted(values.items()))
                               for year, values in sorted(by_disclosure_year.items())},
        "locator_prior_equity_by_year_nfv": {
            str(year): dict(sorted(values.items())) for year, values in sorted(status_yearly.items())
        },
        "rules": {
            "valid_time": "f_ann_date, fallback ann_date; both original fields retained",
            "L1": "no report-version folding and no event qualification",
            "A1": "only total_hldr_eqy_exc_min_int may become denominator",
            "locator": "forecast goodwill text is recall-only; never event or coverage evidence",
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
    batch_id, balances, forecasts = load_rows(required_env("QBASE_APP_DSN")["QBASE_APP_DSN"])
    payload = build_profile(batch_id, balances, forecasts)
    Path(args.output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True,
                   default=json_default) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: payload[key] for key in (
        "batch_id", "all_rows", "scope_rows", "forecast_goodwill_locator_rows",
        "forecast_goodwill_locator_groups")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
