#!/usr/bin/env python3
"""exp17 数据前置：按季度采集 Tushare express_vip 并落 qbase append-only 批次。

范围固定为 2010-12-31..2024-03-31 的季度报告期。原始 CSV 与 SHA 只进 --evidence
内部证据目录，不进 Git。L1 只做字段解析与整行去重，不裁初始/修订或事件方向。
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

import psycopg
import tushare as ts

SOURCE = "tushare:express"
FIRST_PERIOD = date(2010, 12, 31)
LAST_PERIOD = date(2024, 3, 31)
API_ROW_CEILING = 5000
FIELDS = (
    "ts_code,ann_date,end_date,revenue,operate_profit,total_profit,n_income,total_assets,"
    "total_hldr_eqy_exc_min_int,diluted_eps,diluted_roe,yoy_net_profit,bps,yoy_sales,"
    "yoy_op,yoy_tp,yoy_dedu_np,yoy_eps,yoy_roe,growth_assets,yoy_equity,growth_bps,"
    "or_last_year,op_last_year,tp_last_year,np_last_year,eps_last_year,open_net_assets,"
    "open_bps,perf_summary,is_audit,remark,update_flag"
)
FIELD_NAMES = tuple(FIELDS.split(","))
NUMERIC_FIELDS = FIELD_NAMES[3:29]


def load_env(path: str) -> dict[str, str]:
    env: dict[str, str] = {}
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def quarter_periods(start: date = FIRST_PERIOD, end: date = LAST_PERIOD) -> list[str]:
    periods: list[str] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        day = 31 if month in (3, 12) else 30
        periods.append(f"{year:04d}{month:02d}{day:02d}")
        month += 3
        if month > 12:
            year, month = year + 1, month - 12
    return periods


def ymd(value):
    if value is None or str(value).strip() in ("", "None", "nan", "NaT"):
        return None
    return datetime.strptime(str(value).strip()[:8], "%Y%m%d").date()


def num(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    return None if text in ("", "None", "nan", "NaT") else text


def txt(value):
    if value is None:
        return None
    text = str(value).strip()
    return None if text in ("", "None", "nan", "NaT") else text


def integer(value):
    text = num(value)
    return None if text is None else int(float(text))


def fetch_period(pro, period: str, evidence: Path):
    frame = pro.express_vip(period=period, fields=FIELDS)
    if set(frame.columns) != set(FIELD_NAMES):
        missing = sorted(set(FIELD_NAMES) - set(frame.columns))
        extra = sorted(set(frame.columns) - set(FIELD_NAMES))
        raise RuntimeError(f"{period}字段漂移 missing={missing} extra={extra}")
    if frame.empty or len(frame) >= API_ROW_CEILING:
        raise RuntimeError(f"{period}返回{len(frame)}行，空分片或疑似触顶，停报")
    if set(frame["end_date"].dropna().astype(str)) != {period}:
        raise RuntimeError(f"{period}混入其他报告期，停报")
    frame = frame.loc[:, FIELD_NAMES]
    path = evidence / f"express_vip_{period}.csv"
    frame.to_csv(path, index=False, lineterminator="\n")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return frame, sha, path.name


def normalize_row(record, pull_time: datetime) -> tuple:
    ann = ymd(record.ann_date)
    end = ymd(record.end_date)
    valid = datetime.combine(ann, datetime.min.time(), tzinfo=timezone.utc) if ann else pull_time
    values = [str(record.ts_code), ann, end]
    values.extend(num(getattr(record, field)) for field in NUMERIC_FIELDS)
    values.extend((txt(record.perf_summary), integer(record.is_audit),
                   txt(record.remark), txt(record.update_flag)))
    return tuple(values) + (valid,)


def dedupe_rows(frames, pull_time: datetime) -> tuple[list[tuple], int]:
    raw_rows = [normalize_row(row, pull_time) for frame in frames
                for row in frame.itertuples(index=False)]
    return list(dict.fromkeys(raw_rows)), len(raw_rows)


def ensure_no_existing_batch(cur) -> None:
    cur.execute("SELECT count(*) FROM public.fact_batch WHERE source=%s", (SOURCE,))
    if cur.fetchone()[0] != 0:
        raise RuntimeError("tushare:express批次已存在；本单元只允许首次落地，拒绝重复执行")


def preflight_database(dsn: str) -> None:
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SET TRANSACTION READ ONLY")
        cur.execute("SELECT to_regclass('public.express_snap')")
        if cur.fetchone()[0] is None:
            raise RuntimeError("express_snap不存在；须先apply 023 DDL")
        ensure_no_existing_batch(cur)


def write_batch(conn, rows: list[tuple], pull_time: datetime, note: str) -> tuple[int, int]:
    columns = "batch_id," + ",".join(FIELD_NAMES) + ",valid_time,observed_time"
    with conn.cursor() as cur:
        ensure_no_existing_batch(cur)
        cur.execute(
            "INSERT INTO public.fact_batch(source,asof_date,pull_time,note) "
            "VALUES (%s,%s,%s,%s) RETURNING batch_id",
            (SOURCE, pull_time.date(), pull_time, note),
        )
        batch_id = cur.fetchone()[0]
        with cur.copy(f"COPY public.express_snap ({columns}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row((batch_id, *row, pull_time))
    conn.commit()
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM public.express_snap WHERE batch_id=%s", (batch_id,))
        count = cur.fetchone()[0]
    return batch_id, count


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true")
    parser.add_argument("--dry-period", default="20231231")
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--env", default="/opt/quant/.env")
    parser.add_argument("--sleep", type=float, default=0.2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence = Path(args.evidence)
    evidence.mkdir(parents=True, exist_ok=True)
    env = load_env(args.env)
    if not env.get("TUSHARE_TOKEN") or not env.get("QBASE_APP_DSN"):
        raise RuntimeError("缺TUSHARE_TOKEN或QBASE_APP_DSN（仅报变量名，不回显值）")
    pro = ts.pro_api(env["TUSHARE_TOKEN"])
    pull_time = datetime.now(timezone.utc)
    periods = [args.dry_period] if args.dry else quarter_periods()
    if not args.dry:
        preflight_database(env["QBASE_APP_DSN"])
    frames, evidence_rows = [], []
    for period in periods:
        frame, sha, filename = fetch_period(pro, period, evidence)
        frames.append(frame)
        evidence_rows.append({"period": period, "rows": len(frame), "sha256": sha,
                              "file": filename})
        print(f"{period}: rows={len(frame)} sha256={sha[:16]}…", flush=True)
        time.sleep(args.sleep)
    rows, raw_count = dedupe_rows(frames, pull_time)
    manifest = {"source": SOURCE, "pull_time": pull_time.isoformat(), "fields": FIELD_NAMES,
                "periods": evidence_rows, "raw_rows": raw_count,
                "dedup_rows": len(rows), "pure_duplicates": raw_count - len(rows)}
    manifest_path = evidence / "express_fetch_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n",
                             encoding="utf-8")
    if args.dry:
        print(f"--dry PASS: periods={periods} raw={raw_count} dedup={len(rows)}，零落库")
        return 0
    note = (f"exp17数据前置(人令2026-07-30):express_vip季度分片{periods[0]}..{periods[-1]};"
            f"显式update_flag;源拉{raw_count}→整行去重{len(rows)};原始CSV+SHA仅内部证据包;"
            "L1忠实存全，不裁初始/修订或事件方向。")
    with psycopg.connect(env["QBASE_APP_DSN"]) as conn:
        batch_id, stored = write_batch(conn, rows, pull_time, note)
    if stored != len(rows):
        raise RuntimeError(f"落库核行数不符 {stored}!={len(rows)}")
    print(f"落库 PASS: batch_id={batch_id} rows={stored}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
