#!/usr/bin/env python3
"""exp18 数据前置：逐证券采集 Tushare fina_audit，落 qbase append-only 单批次。

范围固定为公告日 2011-01-01..2024-06-30。原始逐请求响应以 JSONL 和 SHA 存在
--evidence 内部目录，不进 Git。L1 仅做字段解析与整行去重，不判意见或版本。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import psycopg
import tushare as ts

SOURCE = "tushare:fina_audit"
START_DATE = date(2011, 1, 1)
END_DATE = date(2024, 6, 30)
FIELDS = "ts_code,ann_date,end_date,audit_result,audit_fees,audit_agency,audit_sign"
FIELD_NAMES = tuple(FIELDS.split(","))
MAX_ROWS_PER_SECURITY = 1000


def load_env(path: str) -> dict[str, str]:
    keys = ("TUSHARE_TOKEN", "QBASE_APP_DSN")
    env = {key: os.environ[key] for key in keys if os.environ.get(key)}
    if len(env) == len(keys):
        return env
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    return env


def is_missing(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) \
        or str(value).strip() in ("", "None", "nan", "NaT")


def ymd(value):
    if is_missing(value):
        return None
    return datetime.strptime(str(value).strip()[:8], "%Y%m%d").date()


def text(value):
    return None if is_missing(value) else str(value).strip()


def number(value):
    return None if is_missing(value) else str(value).strip()


def validate_frame(frame: pd.DataFrame, requested_code: str) -> None:
    missing = sorted(set(FIELD_NAMES) - set(frame.columns))
    extra = sorted(set(frame.columns) - set(FIELD_NAMES))
    if missing or extra:
        raise RuntimeError(f"{requested_code}字段漂移 missing={missing} extra={extra}")
    if len(frame) >= MAX_ROWS_PER_SECURITY:
        raise RuntimeError(f"{requested_code}返回{len(frame)}行，疑似触顶，停报")
    codes = set(frame["ts_code"].dropna().astype(str))
    if codes and codes != {requested_code}:
        raise RuntimeError(f"{requested_code}响应混入其他证券 {sorted(codes)}")
    dates = [ymd(value) for value in frame["ann_date"] if not is_missing(value)]
    if any(value < START_DATE or value > END_DATE for value in dates):
        raise RuntimeError(f"{requested_code}响应公告日越过授权范围")


def frame_record(frame: pd.DataFrame, requested_code: str) -> dict:
    clean = frame.loc[:, FIELD_NAMES].where(pd.notna(frame), None)
    return {"ts_code": requested_code, "columns": list(FIELD_NAMES),
            "records": clean.to_dict(orient="records")}


def fetch_one(pro, code: str, retries: int, retry_wait: float) -> pd.DataFrame:
    for attempt in range(1, retries + 1):
        try:
            frame = pro.fina_audit(
                ts_code=code,
                start_date=START_DATE.strftime("%Y%m%d"),
                end_date=END_DATE.strftime("%Y%m%d"),
                fields=FIELDS,
            )
            validate_frame(frame, code)
            return frame
        except Exception:
            if attempt == retries:
                raise
            time.sleep(retry_wait * attempt)
    raise AssertionError("unreachable")


def append_response(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_responses(path: Path) -> dict[str, list[dict]]:
    responses: dict[str, list[dict]] = {}
    if not path.exists():
        return responses
    with path.open(encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            record = json.loads(raw)
            code = record["ts_code"]
            if code in responses:
                raise RuntimeError(f"响应JSONL第{line_no}行重复证券 {code}")
            if tuple(record["columns"]) != FIELD_NAMES:
                raise RuntimeError(f"响应JSONL第{line_no}行字段漂移")
            responses[code] = record["records"]
    return responses


def fetch_all(pro, codes: list[str], response_path: Path, sleep_s: float,
              retries: int, retry_wait: float) -> dict[str, list[dict]]:
    responses = load_responses(response_path)
    unknown = sorted(set(responses) - set(codes))
    if unknown:
        raise RuntimeError(f"断点文件含非本批证券 {unknown[:5]}")
    for position, code in enumerate(codes, start=1):
        if code in responses:
            continue
        frame = fetch_one(pro, code, retries, retry_wait)
        record = frame_record(frame, code)
        append_response(response_path, record)
        responses[code] = record["records"]
        if position % 100 == 0 or position == len(codes):
            print(f"fetch {position}/{len(codes)} rows={sum(map(len, responses.values()))}", flush=True)
        time.sleep(sleep_s)
    if set(responses) != set(codes):
        raise RuntimeError("响应证券集合与请求全集不相等")
    return responses


def normalize_record(record: dict, pull_time: datetime) -> tuple:
    ann = ymd(record.get("ann_date"))
    end = ymd(record.get("end_date"))
    valid = datetime.combine(ann, datetime.min.time(), tzinfo=timezone.utc) if ann else pull_time
    return (text(record.get("ts_code")), ann, end, text(record.get("audit_result")),
            number(record.get("audit_fees")), text(record.get("audit_agency")),
            text(record.get("audit_sign")), valid)


def normalized_rows(responses: dict[str, list[dict]], pull_time: datetime) -> tuple[list[tuple], int]:
    raw = [normalize_record(record, pull_time) for code in sorted(responses)
           for record in responses[code]]
    return list(dict.fromkeys(raw)), len(raw)


def database_codes_and_preflight(dsn: str, require_table: bool) -> list[str]:
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SET TRANSACTION READ ONLY")
        cur.execute("SELECT count(*) FROM public.fact_batch WHERE source=%s", (SOURCE,))
        if cur.fetchone()[0] != 0:
            raise RuntimeError("tushare:fina_audit批次已存在；拒绝重复执行")
        if require_table:
            cur.execute("SELECT to_regclass('public.fina_audit_snap')")
            if cur.fetchone()[0] is None:
                raise RuntimeError("fina_audit_snap不存在；须先apply 025 DDL")
        cur.execute(
            "SELECT DISTINCT ts_code FROM public.entity_master "
            "WHERE batch_id=(SELECT max(batch_id) FROM public.entity_batch "
            "WHERE source='tushare:stock_basic') ORDER BY ts_code"
        )
        codes = [row[0] for row in cur.fetchall()]
    if not codes:
        raise RuntimeError("证券全集为空，停报")
    return codes


def write_batch(dsn: str, rows: list[tuple], pull_time: datetime, note: str) -> tuple[int, int]:
    columns = "batch_id," + ",".join(FIELD_NAMES) + ",valid_time,observed_time"
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM public.fact_batch WHERE source=%s", (SOURCE,))
        if cur.fetchone()[0] != 0:
            raise RuntimeError("tushare:fina_audit批次已存在；拒绝重复执行")
        cur.execute(
            "INSERT INTO public.fact_batch(source,asof_date,pull_time,note) "
            "VALUES (%s,%s,%s,%s) RETURNING batch_id",
            (SOURCE, pull_time.date(), pull_time, note),
        )
        batch_id = cur.fetchone()[0]
        with cur.copy(f"COPY public.fina_audit_snap ({columns}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row((batch_id, *row, pull_time))
        cur.execute("SELECT count(*) FROM public.fina_audit_snap WHERE batch_id=%s", (batch_id,))
        stored = cur.fetchone()[0]
        if stored != len(rows):
            raise RuntimeError(f"落库核行数不符 {stored}!={len(rows)}")
        conn.commit()
    return batch_id, stored


def write_manifest(path: Path, *, pull_time: datetime, codes: list[str],
                   raw_rows: int, dedup_rows: int, response_sha: str) -> None:
    payload = {
        "source": SOURCE, "pull_time": pull_time.isoformat(), "fields": FIELD_NAMES,
        "start_date": START_DATE.isoformat(), "end_date": END_DATE.isoformat(),
        "requested_securities": len(codes), "raw_rows": raw_rows,
        "dedup_rows": dedup_rows, "pure_duplicates": raw_rows - dedup_rows,
        "response_jsonl_sha256": response_sha,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--env", default="/opt/quant/.env")
    parser.add_argument("--dry-limit", type=int, default=0)
    parser.add_argument("--sleep", type=float, default=0.31)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--retry-wait", type=float, default=2.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence = Path(args.evidence)
    evidence.mkdir(parents=True, exist_ok=True)
    env = load_env(args.env)
    if not env.get("TUSHARE_TOKEN") or not env.get("QBASE_APP_DSN"):
        raise RuntimeError("缺TUSHARE_TOKEN或QBASE_APP_DSN（仅报变量名，不回显值）")
    codes = database_codes_and_preflight(env["QBASE_APP_DSN"], require_table=not args.dry_limit)
    if args.dry_limit:
        codes = codes[:args.dry_limit]
    pull_time = datetime.now(timezone.utc)
    response_path = evidence / "fina_audit_responses.jsonl"
    responses = fetch_all(ts.pro_api(env["TUSHARE_TOKEN"]), codes, response_path,
                          args.sleep, args.retries, args.retry_wait)
    rows, raw_count = normalized_rows(responses, pull_time)
    response_sha = hashlib.sha256(response_path.read_bytes()).hexdigest()
    write_manifest(evidence / "fina_audit_fetch_manifest.json", pull_time=pull_time,
                   codes=codes, raw_rows=raw_count, dedup_rows=len(rows),
                   response_sha=response_sha)
    if args.dry_limit:
        print(f"--dry-limit PASS: securities={len(codes)} raw={raw_count} "
              f"dedup={len(rows)} sha256={response_sha}")
        return 0
    note = (f"exp18数据前置(人令2026-07-31):fina_audit逐证券全量 "
            f"ann_date={START_DATE}..{END_DATE};请求{len(codes)}票;"
            f"源拉{raw_count}→整行去重{len(rows)};原始JSONL+SHA仅内部证据包;"
            "L1忠实存全，不裁意见、首次披露、修订或事件资格。")
    batch_id, stored = write_batch(env["QBASE_APP_DSN"], rows, pull_time, note)
    print(f"落库 PASS: batch_id={batch_id} rows={stored} response_sha256={response_sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
