#!/usr/bin/env python3
"""exp21：按报告期分页采集 balancesheet_vip，单批 append-only 落 qbase。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import psycopg
import tushare as ts

from qbase.ingest.balancesheet_common import (
    FIELDS, FIELD_NAMES, SOURCE, normalize_source_row, quarter_periods, required_env,
)

PAGE_SIZE = 4000
MAX_PAGES = 8
MAX_ATTEMPTS = 3


def validate_page(frame: pd.DataFrame, period: str, offset: int) -> None:
    got, expected = set(frame.columns), set(FIELD_NAMES)
    if got != expected:
        raise RuntimeError(
            f"{period}@{offset}字段漂移 missing={sorted(expected-got)} extra={sorted(got-expected)}"
        )
    periods = set(frame["end_date"].dropna().astype(str).str[:8])
    if periods - {period}:
        raise RuntimeError(f"{period}@{offset}响应混入其他报告期 {sorted(periods)[:3]}")


def query_page(pro, period: str, offset: int) -> pd.DataFrame:
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            frame = pro.query("balancesheet_vip", period=period, limit=PAGE_SIZE,
                              offset=offset, fields=FIELDS)
            validate_page(frame, period, offset)
            return frame.loc[:, list(FIELD_NAMES)]
        except Exception as exc:
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"{period}@{offset}连续{MAX_ATTEMPTS}次失败") from last_error


def fetch_period(pro, period: str) -> dict:
    pages, page_keys = [], set()
    for page in range(MAX_PAGES):
        offset = page * PAGE_SIZE
        frame = query_page(pro, period, offset)
        records = frame.where(pd.notna(frame), None).to_dict("records")
        keys = {json.dumps(row, ensure_ascii=False, sort_keys=True) for row in records}
        if page and keys & page_keys:
            raise RuntimeError(f"{period}分页重叠，拒绝采集")
        page_keys.update(keys)
        pages.extend(records)
        if len(frame) < PAGE_SIZE:
            return {"period": period, "columns": FIELD_NAMES, "pages": page + 1,
                    "records": pages}
    raise RuntimeError(f"{period}达到{MAX_PAGES}页仍未终止，疑似截断")


def load_responses(path: Path, expected: set[str]) -> dict[str, dict]:
    responses = {}
    if not path.exists():
        return responses
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        item = json.loads(raw)
        period = item.get("period")
        if period not in expected or period in responses:
            raise RuntimeError(f"断点第{line_no}行报告期越界或重复：{period}")
        if tuple(item.get("columns", ())) != FIELD_NAMES:
            raise RuntimeError(f"断点第{line_no}行字段漂移")
        responses[period] = item
    return responses


def append_response(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def collect(pro, periods: list[str], path: Path, sleep_seconds: float) -> dict[str, dict]:
    expected = set(periods)
    responses = load_responses(path, expected)
    for position, period in enumerate(periods, start=1):
        if period not in responses:
            payload = fetch_period(pro, period)
            append_response(path, payload)
            responses[period] = payload
            time.sleep(sleep_seconds)
        if position % 20 == 0 or position == len(periods):
            total = sum(len(item["records"]) for item in responses.values())
            print(f"collected={position}/{len(periods)} rows={total}", flush=True)
    if set(responses) != expected:
        raise RuntimeError("响应报告期集合与请求全集不等")
    return responses


def normalized_rows(responses: dict[str, dict], pull_time: datetime) -> tuple[list[tuple], int]:
    raw = [normalize_source_row(row, pull_time) for period in sorted(responses)
           for row in responses[period]["records"]]
    return list(dict.fromkeys(raw)), len(raw)


def preflight_database(dsn: str) -> None:
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on") as conn:
        if conn.execute("SELECT to_regclass('public.balancesheet_pit_snap')").fetchone()[0] is None:
            raise RuntimeError("balancesheet_pit_snap不存在，须先apply DDL")
        if conn.execute("SELECT count(*) FROM fact_batch WHERE source=%s", (SOURCE,)).fetchone()[0]:
            raise RuntimeError("tushare:balancesheet正式批次已存在")


def write_batch(dsn: str, rows: list[tuple], pull_time: datetime, note: str) -> tuple[int, int]:
    columns = "batch_id," + ",".join(FIELD_NAMES) + ",valid_time,observed_time"
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT batch_id FROM fact_batch WHERE source=%s FOR UPDATE", (SOURCE,))
        if cur.fetchone() is not None:
            raise RuntimeError("事务内发现balancesheet批次，拒绝重复执行")
        cur.execute(
            "INSERT INTO fact_batch(source,asof_date,pull_time,note) VALUES (%s,%s,%s,%s) "
            "RETURNING batch_id", (SOURCE, pull_time.date(), pull_time, note),
        )
        batch_id = cur.fetchone()[0]
        with cur.copy(f"COPY balancesheet_pit_snap ({columns}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row((batch_id, *row, pull_time))
        inserted = cur.execute(
            "SELECT count(*) FROM balancesheet_pit_snap WHERE batch_id=%s", (batch_id,)
        ).fetchone()[0]
        if inserted != len(rows):
            raise RuntimeError(f"落库行数不等：{inserted}!={len(rows)}")
        conn.commit()
    return batch_id, inserted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--sleep", type=float, default=0.31)
    parser.add_argument("--dry-period")
    args = parser.parse_args()
    env = required_env("TUSHARE_TOKEN", "QBASE_APP_DSN")
    evidence = Path(args.evidence)
    evidence.mkdir(parents=True, exist_ok=True)
    pro = ts.pro_api(env["TUSHARE_TOKEN"])
    if args.dry_period:
        payload = fetch_period(pro, args.dry_period)
        print(json.dumps({"period": args.dry_period, "rows": len(payload["records"]),
                          "pages": payload["pages"], "columns": payload["columns"]},
                         ensure_ascii=False))
        return 0
    periods = quarter_periods()
    preflight_database(env["QBASE_APP_DSN"])
    raw_path = evidence / "balancesheet_raw_responses.jsonl"
    responses = collect(pro, periods, raw_path, args.sleep)
    pull_time = datetime.now(timezone.utc)
    rows, raw_count = normalized_rows(responses, pull_time)
    note = f"exp21数据闭合(John 2026-08-09):季度VIP全历史;raw={raw_count};dedup={len(rows)}"
    batch_id, inserted = write_batch(env["QBASE_APP_DSN"], rows, pull_time, note)
    manifest = {"source": SOURCE, "batch_id": batch_id, "period_count": len(periods),
                "raw_rows": raw_count, "deduplicated_rows": len(rows),
                "inserted_rows": inserted, "field_names": FIELD_NAMES,
                "pull_time": pull_time.isoformat(),
                "raw_response_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest()}
    (evidence / "balancesheet_fetch_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
