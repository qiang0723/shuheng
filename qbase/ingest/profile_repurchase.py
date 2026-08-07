#!/usr/bin/env python3
"""exp23 repurchase 全量质量画像；只读事实，不读取行情或收益。"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from qbase.ingest.repurchase_common import FIELD_NAMES, HOLDOUT, SOURCE, required_env


def load_rows(dsn: str) -> tuple[int, list[dict]]:
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on",
                         row_factory=dict_row) as conn:
        row = conn.execute(
            "SELECT max(batch_id) AS batch_id FROM fact_batch WHERE source=%s", (SOURCE,)
        ).fetchone()
        batch_id = row["batch_id"]
        if batch_id is None:
            raise RuntimeError("无tushare:repurchase正式批次")
        columns = ",".join(FIELD_NAMES)
        rows = conn.execute(
            f"SELECT {columns} FROM repurchase_snap WHERE batch_id=%s "
            "ORDER BY ann_date,ts_code,proc,end_date,exp_date,vol,amount,high_limit,low_limit",
            (batch_id,),
        ).fetchall()
    return int(batch_id), [dict(item) for item in rows]


def in_scope(row: dict) -> bool:
    return bool(row["ann_date"] and row["ann_date"] < HOLDOUT
                and row["ts_code"] and row["ts_code"].endswith((".SH", ".SZ")))


def suffix_bucket(ts_code: str | None) -> str:
    if ts_code and ts_code.endswith(".SH"):
        return "SH"
    if ts_code and ts_code.endswith(".SZ"):
        return "SZ"
    if ts_code and ts_code.endswith(".BJ"):
        return "BJ"
    return "OTHER"


def group_by_event(rows: list[dict]) -> dict[tuple[str, date], list[dict]]:
    groups = defaultdict(list)
    for row in rows:
        if row["ts_code"] and row["ann_date"]:
            groups[(row["ts_code"], row["ann_date"])].append(row)
    return dict(groups)


def row_signature(row: dict) -> tuple:
    return tuple(row[field] for field in FIELD_NAMES)


def proposal_profile(groups: dict) -> tuple[Counter, dict[int, Counter], dict[str, list[date]]]:
    totals = Counter()
    yearly = defaultdict(Counter)
    by_security = defaultdict(list)
    for (ts_code, ann_date), members in sorted(groups.items()):
        proposals = [row for row in members if row["proc"] == "预案"]
        if not proposals:
            continue
        totals["proposal_keys"] += 1
        totals["proposal_rows"] += len(proposals)
        yearly[ann_date.year]["proposal_keys"] += 1
        yearly[ann_date.year]["proposal_rows"] += len(proposals)
        bucket = "single_row_keys" if len(members) == 1 else "c1_multirow_keys"
        totals[bucket] += 1
        yearly[ann_date.year][bucket] += 1
        if len(members) == 1:
            by_security[ts_code].append(ann_date)
        if len({row_signature(row) for row in members}) < len(members):
            totals["keys_with_exact_duplicates"] += 1
            yearly[ann_date.year]["keys_with_exact_duplicates"] += 1
        if len({row["proc"] for row in members}) > 1:
            totals["keys_with_mixed_proc"] += 1
            yearly[ann_date.year]["keys_with_mixed_proc"] += 1
    return totals, yearly, by_security


def null_counts(rows: list[dict]) -> dict[str, int]:
    return {field: sum(row[field] is None for row in rows) for field in FIELD_NAMES}


def build_profile(batch_id: int, rows: list[dict]) -> dict:
    scope = [row for row in rows if in_scope(row)]
    groups = group_by_event(scope)
    proposals, proposal_yearly, by_security = proposal_profile(groups)
    stage = Counter(row["proc"] if row["proc"] is not None else "NULL" for row in scope)
    all_yearly = defaultdict(Counter)
    for row in scope:
        all_yearly[row["ann_date"].year]["rows"] += 1
        all_yearly[row["ann_date"].year][f"proc:{row['proc'] or 'NULL'}"] += 1
    for year, values in proposal_yearly.items():
        all_yearly[year].update(values)
    ambiguous = {code: dates for code, dates in by_security.items() if len(dates) > 1}
    exact_duplicate_rows = len(rows) - len({row_signature(row) for row in rows})
    suffix_rows = Counter(suffix_bucket(row["ts_code"]) for row in rows)
    suffix_securities = {bucket: len({row["ts_code"] for row in rows
                                      if suffix_bucket(row["ts_code"]) == bucket})
                         for bucket in suffix_rows}
    proposal_rows = stage.get("预案", 0)
    if proposals["proposal_rows"] != proposal_rows:
        raise RuntimeError("预案行未完整进入事件键分组（存在缺ts_code/ann_date），须停报")
    if proposals["single_row_keys"] + proposals["c1_multirow_keys"] != proposals["proposal_keys"]:
        raise RuntimeError("C1事件键分类不守恒")
    return {
        "source": SOURCE, "batch_id": batch_id, "all_rows": len(rows),
        "all_securities": len({row["ts_code"] for row in rows if row["ts_code"]}),
        "ann_date_min": min((row["ann_date"] for row in rows if row["ann_date"]), default=None),
        "ann_date_max": max((row["ann_date"] for row in rows if row["ann_date"]), default=None),
        "l1_exact_duplicate_rows": exact_duplicate_rows,
        "source_suffix_rows": dict(sorted(suffix_rows.items())),
        "source_suffix_securities": dict(sorted(suffix_securities.items())),
        "scope_rows": len(scope), "scope_securities": len({row["ts_code"] for row in scope}),
        "scope_event_keys": len(groups), "scope_null_rows": null_counts(scope),
        "stage_rows": dict(sorted(stage.items())),
        "proposal_c1": dict(sorted(proposals.items())),
        "single_proposal_securities_with_multiple_dates": len(ambiguous),
        "single_proposal_dates_in_ambiguous_securities": sum(map(len, ambiguous.values())),
        "by_event_year": {str(year): dict(sorted(values.items()))
                          for year, values in sorted(all_yearly.items())},
        "rules": {
            "candidate": "proc exact equals 预案",
            "C1": "any multirow event key is fail-closed; no choosing or folding",
            "scheme_identity": "multiple proposal dates per security require official evidence",
            "purpose": "official original-body evidence only; all purpose counts NFV",
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
    batch_id, rows = load_rows(required_env("QBASE_APP_DSN")["QBASE_APP_DSN"])
    payload = build_profile(batch_id, rows)
    Path(args.output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True,
                   default=json_default) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: payload[key] for key in (
        "batch_id", "all_rows", "scope_rows", "scope_event_keys",
        "single_proposal_securities_with_multiple_dates")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
