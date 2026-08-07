#!/usr/bin/env python3
"""exp23：按无重叠月窗采集 Tushare repurchase，单批 append-only 落 qbase。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import psycopg
import tushare as ts

from qbase.ingest.repurchase_common import (
    DEFAULT_START, FIELDS, FIELD_NAMES, HOLDOUT, SOURCE, month_windows,
    normalize_source_row, required_env, window_key,
)

API_ROW_CEILING = 2000
MAX_ATTEMPTS = 3


def validate_frame(frame: pd.DataFrame, window: tuple[date, date]) -> None:
    got, expected = set(frame.columns), set(FIELD_NAMES)
    if got != expected:
        raise RuntimeError(
            f"{window_key(window)}字段漂移 missing={sorted(expected-got)} "
            f"extra={sorted(got-expected)}"
        )
    if len(frame) >= API_ROW_CEILING:
        raise RuntimeError(f"{window_key(window)}返回{len(frame)}行，疑似接口触顶，停报")
    dates = pd.to_datetime(frame["ann_date"], errors="coerce").dropna().dt.date
    outside = [value for value in dates if not window[0] <= value <= window[1]]
    if outside:
        raise RuntimeError(f"{window_key(window)}响应混入窗外ann_date，停报")


def fetch_window(pro, window: tuple[date, date]) -> dict:
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            frame = pro.repurchase(start_date=f"{window[0]:%Y%m%d}",
                                   end_date=f"{window[1]:%Y%m%d}", fields=FIELDS)
            validate_frame(frame, window)
            ordered = frame.loc[:, list(FIELD_NAMES)]
            records = ordered.where(pd.notna(ordered), None).to_dict("records")
            return {"window": window_key(window), "columns": FIELD_NAMES, "records": records}
        except Exception as exc:
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(1.5 * attempt)
    raise RuntimeError(
        f"{window_key(window)}连续{MAX_ATTEMPTS}次失败：{type(last_error).__name__}"
    ) from last_error


def load_responses(path: Path, expected: set[str]) -> dict[str, list[dict]]:
    responses = {}
    if not path.exists():
        return responses
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        record = json.loads(raw)
        key = record.get("window")
        if key not in expected or key in responses:
            raise RuntimeError(f"断点文件第{line_no}行窗口越界或重复：{key}")
        if tuple(record.get("columns", ())) != FIELD_NAMES:
            raise RuntimeError(f"断点文件第{line_no}行字段漂移")
        responses[key] = record.get("records", [])
    return responses


def append_response(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def collect(pro, windows: list[tuple[date, date]], path: Path,
            sleep_seconds: float) -> dict[str, list[dict]]:
    expected = {window_key(window) for window in windows}
    responses = load_responses(path, expected)
    for position, window in enumerate(windows, start=1):
        key = window_key(window)
        if key not in responses:
            payload = fetch_window(pro, window)
            append_response(path, payload)
            responses[key] = payload["records"]
            time.sleep(sleep_seconds)
        if position % 24 == 0 or position == len(windows):
            print(f"collected={position}/{len(windows)} rows={sum(map(len,responses.values()))}",
                  flush=True)
    if set(responses) != expected:
        raise RuntimeError("响应窗口集合与请求全集不等，拒绝落库")
    return responses


def normalized_rows(responses: dict[str, list[dict]], pull_time: datetime) -> tuple[list[tuple], int]:
    raw = [normalize_source_row(row, pull_time) for key in sorted(responses)
           for row in responses[key]]
    return list(dict.fromkeys(raw)), len(raw)


def preflight_database(dsn: str) -> None:
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on") as conn:
        if conn.execute("SELECT to_regclass('public.repurchase_snap')").fetchone()[0] is None:
            raise RuntimeError("repurchase_snap不存在，须先apply 027 DDL")
        count = conn.execute("SELECT count(*) FROM fact_batch WHERE source=%s", (SOURCE,)).fetchone()[0]
        if count:
            raise RuntimeError("tushare:repurchase正式批次已存在，拒绝重复执行")


def write_batch(dsn: str, rows: list[tuple], pull_time: datetime, note: str) -> tuple[int, int]:
    columns = "batch_id," + ",".join(FIELD_NAMES) + ",valid_time,observed_time"
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT batch_id FROM fact_batch WHERE source=%s FOR UPDATE", (SOURCE,))
        if cur.fetchone() is not None:
            raise RuntimeError("事务内发现tushare:repurchase批次，拒绝重复执行")
        cur.execute(
            "INSERT INTO fact_batch(source,asof_date,pull_time,note) VALUES (%s,%s,%s,%s) "
            "RETURNING batch_id", (SOURCE, pull_time.date(), pull_time, note),
        )
        batch_id = cur.fetchone()[0]
        with cur.copy(f"COPY repurchase_snap ({columns}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row((batch_id, *row, pull_time))
        cur.execute("SELECT count(*) FROM repurchase_snap WHERE batch_id=%s", (batch_id,))
        inserted = cur.fetchone()[0]
        if inserted != len(rows):
            raise RuntimeError(f"落库行数不等：{inserted}!={len(rows)}")
        conn.commit()
    return batch_id, inserted


def write_manifest(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--start", default=DEFAULT_START.isoformat())
    parser.add_argument("--end", default=(HOLDOUT - timedelta(days=1)).isoformat())
    parser.add_argument("--sleep", type=float, default=0.31)
    parser.add_argument("--dry-start")
    parser.add_argument("--dry-end")
    args = parser.parse_args()
    env = required_env("TUSHARE_TOKEN", "QBASE_APP_DSN")
    evidence = Path(args.evidence)
    evidence.mkdir(parents=True, exist_ok=True)
    pro = ts.pro_api(env["TUSHARE_TOKEN"])
    if args.dry_start and args.dry_end:
        window = (date.fromisoformat(args.dry_start), date.fromisoformat(args.dry_end))
        payload = fetch_window(pro, window)
        print(json.dumps({"window": payload["window"], "rows": len(payload["records"]),
                          "columns": payload["columns"]}, ensure_ascii=False))
        return 0
    windows = month_windows(date.fromisoformat(args.start), date.fromisoformat(args.end))
    preflight_database(env["QBASE_APP_DSN"])
    raw_path = evidence / "repurchase_raw_responses.jsonl"
    responses = collect(pro, windows, raw_path, args.sleep)
    pull_time = datetime.now(timezone.utc)
    rows, raw_count = normalized_rows(responses, pull_time)
    note = f"exp23数据闭合(John 2026-08-07):月窗全历史;raw={raw_count};dedup={len(rows)}"
    batch_id, inserted = write_batch(env["QBASE_APP_DSN"], rows, pull_time, note)
    manifest = {"source": SOURCE, "batch_id": batch_id, "window_count": len(windows),
                "start": args.start, "end": args.end, "raw_rows": raw_count,
                "deduplicated_rows": len(rows), "inserted_rows": inserted,
                "field_names": FIELD_NAMES, "pull_time": pull_time.isoformat(),
                "raw_response_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest()}
    write_manifest(evidence / "repurchase_fetch_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
