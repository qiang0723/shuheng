#!/usr/bin/env python3
"""exp19 数据闭合：逐证券采集 Tushare dividend，单批 append-only 落 qbase。"""
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

from qbase.ingest.dividend_common import (
    FIELDS,
    FIELD_NAMES,
    SOURCE,
    normalize_source_row,
    required_env,
)

API_ROW_CEILING = 1000
MAX_ATTEMPTS = 3


def universe(dsn: str) -> list[str]:
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on") as conn:
        rows = conn.execute(
            "SELECT ts_code FROM public.entity_master "
            "WHERE batch_id=(SELECT max(batch_id) FROM public.entity_batch "
            "WHERE source='tushare:stock_basic') ORDER BY ts_code"
        ).fetchall()
    codes = [row[0] for row in rows]
    if not codes or len(codes) != len(set(codes)):
        raise RuntimeError("证券全集为空或含重复，拒绝采集")
    return codes


def validate_frame(frame: pd.DataFrame, ts_code: str) -> None:
    got = set(frame.columns)
    expected = set(FIELD_NAMES)
    if got != expected:
        raise RuntimeError(
            f"{ts_code}字段漂移 missing={sorted(expected-got)} extra={sorted(got-expected)}"
        )
    if len(frame) >= API_ROW_CEILING:
        raise RuntimeError(f"{ts_code}返回{len(frame)}行，疑似接口触顶，停报")
    mixed = sorted(set(frame["ts_code"].dropna().astype(str)) - {ts_code})
    if mixed:
        raise RuntimeError(f"{ts_code}响应混入其他证券 {mixed[:3]}，停报")


def fetch_one(pro, ts_code: str) -> dict:
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            frame = pro.dividend(ts_code=ts_code, fields=FIELDS)
            validate_frame(frame, ts_code)
            ordered = frame.loc[:, list(FIELD_NAMES)]
            records = ordered.where(pd.notna(ordered), None).to_dict("records")
            return {"ts_code": ts_code, "columns": FIELD_NAMES, "records": records}
        except Exception as exc:  # 单票瞬时失败重试；最终失败仍整批停止
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"{ts_code}连续{MAX_ATTEMPTS}次失败：{type(last_error).__name__}") from last_error


def load_responses(path: Path, expected_codes: set[str]) -> dict[str, list[dict]]:
    responses: dict[str, list[dict]] = {}
    if not path.exists():
        return responses
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        record = json.loads(raw)
        code = record.get("ts_code")
        if code not in expected_codes or code in responses:
            raise RuntimeError(f"断点文件第{line_no}行证券越界或重复：{code}")
        if tuple(record.get("columns", ())) != FIELD_NAMES:
            raise RuntimeError(f"断点文件第{line_no}行字段漂移")
        responses[code] = record.get("records", [])
    return responses


def append_response(path: Path, payload: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def collect(pro, codes: list[str], path: Path, sleep_seconds: float) -> dict[str, list[dict]]:
    responses = load_responses(path, set(codes))
    for position, code in enumerate(codes, start=1):
        if code in responses:
            continue
        payload = fetch_one(pro, code)
        append_response(path, payload)
        responses[code] = payload["records"]
        if position % 100 == 0 or position == len(codes):
            print(f"collected={position}/{len(codes)} rows={sum(map(len, responses.values()))}", flush=True)
        time.sleep(sleep_seconds)
    if set(responses) != set(codes):
        raise RuntimeError("响应证券集合与请求全集不等，拒绝落库")
    return responses


def normalized_rows(responses: dict[str, list[dict]], pull_time: datetime) -> tuple[list[tuple], int]:
    raw = [normalize_source_row(row, pull_time) for code in sorted(responses) for row in responses[code]]
    return list(dict.fromkeys(raw)), len(raw)


def preflight_database(dsn: str) -> None:
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on") as conn:
        if conn.execute("SELECT to_regclass('public.dividend_snap')").fetchone()[0] is None:
            raise RuntimeError("dividend_snap不存在，须先apply DDL")
        count = conn.execute("SELECT count(*) FROM fact_batch WHERE source=%s", (SOURCE,)).fetchone()[0]
        if count:
            raise RuntimeError("tushare:dividend正式批次已存在，拒绝重复执行")


def write_batch(dsn: str, rows: list[tuple], pull_time: datetime, note: str) -> tuple[int, int]:
    columns = "batch_id," + ",".join(FIELD_NAMES) + ",valid_time,observed_time"
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT batch_id FROM fact_batch WHERE source=%s FOR UPDATE", (SOURCE,))
        if cur.fetchone() is not None:
            raise RuntimeError("事务内发现tushare:dividend批次，拒绝重复执行")
        cur.execute(
            "INSERT INTO fact_batch(source,asof_date,pull_time,note) VALUES (%s,%s,%s,%s) "
            "RETURNING batch_id", (SOURCE, pull_time.date(), pull_time, note),
        )
        batch_id = cur.fetchone()[0]
        with cur.copy(f"COPY dividend_snap ({columns}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row((batch_id, *row, pull_time))
        cur.execute("SELECT count(*) FROM dividend_snap WHERE batch_id=%s", (batch_id,))
        inserted = cur.fetchone()[0]
        if inserted != len(rows):
            raise RuntimeError(f"落库行数不等：{inserted}!={len(rows)}")
        conn.commit()
    return batch_id, inserted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--sleep", type=float, default=0.31)
    parser.add_argument("--dry-code")
    args = parser.parse_args()
    env = required_env("TUSHARE_TOKEN", "QBASE_APP_DSN")
    evidence = Path(args.evidence)
    evidence.mkdir(parents=True, exist_ok=True)
    pro = ts.pro_api(env["TUSHARE_TOKEN"])
    if args.dry_code:
        payload = fetch_one(pro, args.dry_code)
        print(json.dumps({"ts_code": args.dry_code, "rows": len(payload["records"]),
                          "columns": payload["columns"]}, ensure_ascii=False))
        return 0
    codes = universe(env["QBASE_APP_DSN"])
    preflight_database(env["QBASE_APP_DSN"])
    raw_path = evidence / "dividend_raw_responses.jsonl"
    responses = collect(pro, codes, raw_path, args.sleep)
    pull_time = datetime.now(timezone.utc)
    rows, raw_count = normalized_rows(responses, pull_time)
    note = f"exp19数据闭合(John 2026-08-06):逐证券全历史; raw={raw_count}; dedup={len(rows)}"
    batch_id, inserted = write_batch(env["QBASE_APP_DSN"], rows, pull_time, note)
    manifest = {
        "source": SOURCE, "batch_id": batch_id, "requested_securities": len(codes),
        "raw_rows": raw_count, "deduplicated_rows": len(rows), "inserted_rows": inserted,
        "field_names": FIELD_NAMES, "pull_time": pull_time.isoformat(),
        "raw_response_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    }
    (evidence / "dividend_fetch_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
