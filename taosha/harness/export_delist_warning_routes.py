#!/usr/bin/env python3
"""exp22 公告索引路由导出：只读重建 batch7 普通→ST 广义事件全集。"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

from taosha.compute.st_imposition_rules import (
    composition_identity_ok,
    funnel_identity_ok,
    merge_selections,
    select_st_imposition_events,
)

REFERENCE = {
    "snapshot_batch": "batch7",
    "final_events": 765,
    "final_securities": 646,
    "starred_events": 560,
    "plain_st_events": 205,
}


def _show_read_only(row: dict) -> str:
    value = row.get("transaction_read_only")
    if value not in ("on", "off"):
        raise RuntimeError("SHOW transaction_read_only返回形态非法")
    return value


def _selection(rows: list[dict]) -> dict:
    per_security: list[dict] = []
    current: str | None = None
    buffer: list[dict] = []
    for row in sorted(rows, key=lambda item: (
            item["ts_code"], item["start_date"] or dt.date.min,
            str(item["alias"]), item["ann_date"] or dt.date.min)):
        if current is not None and row["ts_code"] != current:
            per_security.append(select_st_imposition_events(current, buffer))
            buffer = []
        current = row["ts_code"]
        buffer.append(row)
    if current is not None:
        per_security.append(select_st_imposition_events(current, buffer))
    return merge_selections(per_security)


def route_payload(rows: list[dict], transaction_read_only: str) -> dict:
    selection = _selection(rows)
    counters = selection["counters"]
    routes = sorted({event["ts_code"] for event in selection["events"]})
    batches = sorted({str(row["snapshot_batch"]) for row in rows})
    checks = {
        "transaction_read_only": transaction_read_only == "on",
        "snapshot_batch": batches == [REFERENCE["snapshot_batch"]],
        "funnel_identity": funnel_identity_ok(counters),
        "composition_identity": composition_identity_ok(counters),
        "event_count": counters["final_events"] == REFERENCE["final_events"],
        "security_count": len(routes) == REFERENCE["final_securities"],
        "starred_count": counters["starred_events"] == REFERENCE["starred_events"],
        "plain_st_count": counters["plain_st_events"] == REFERENCE["plain_st_events"],
    }
    if not all(checks.values()):
        raise RuntimeError(f"route export fail-closed: {checks}")
    events = sorted(selection["events"], key=lambda item: (
        item["ts_code"], item["ann_date"], item["cur_start_date"]))
    event_keys = [{key: event[key] for key in (
        "ts_code", "ann_date", "prev_start_date", "cur_start_date")}
        for event in events]
    key_bytes = json.dumps(event_keys, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), default=str).encode()
    return {
        "artifact_status": "ROUTING_ONLY_NOT_EXP22_CANDIDATES",
        "source_view": "explore_reader_namechange",
        "transaction_read_only": transaction_read_only,
        "snapshot_batches": batches,
        "reference": REFERENCE,
        "checks": checks,
        "counters": counters,
        "event_key_sha256": hashlib.sha256(key_bytes).hexdigest(),
        "events": events,
        "routes": routes,
    }


def _read_rows(dsn: str) -> tuple[list[dict], str]:
    import psycopg
    from psycopg.rows import dict_row

    sql = (
        "SELECT ts_code,alias,start_date,ann_date,snapshot_batch "
        "FROM explore_reader_namechange "
        "ORDER BY ts_code,start_date,alias,ann_date NULLS FIRST"
    )
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on",
                         row_factory=dict_row) as conn:
        read_only = _show_read_only(
            dict(conn.execute("SHOW transaction_read_only").fetchone()))
        rows = [dict(row) for row in conn.execute(sql).fetchall()]
    return rows, read_only


def _write(path: Path, payload: dict) -> str:
    data = (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), default=str) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--dsn-env", default="TAOSHA_ENGINE_QBASE_DSN")
    args = parser.parse_args()
    dsn = os.environ.get(args.dsn_env)
    if not dsn:
        raise SystemExit(f"缺环境变量 {args.dsn_env}（不回显值）")
    rows, read_only = _read_rows(dsn)
    payload = route_payload(rows, read_only)
    digest = _write(Path(args.output), payload)
    print(json.dumps({
        "output": args.output,
        "sha256": digest,
        "events": len(payload["events"]),
        "routes": len(payload["routes"]),
        "event_key_sha256": payload["event_key_sha256"],
        "transaction_read_only": read_only,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
