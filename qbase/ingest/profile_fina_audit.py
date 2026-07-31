#!/usr/bin/env python3
"""exp18 fina_audit 批次只读质量画像，输出可复算 JSON。"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from qbase.ingest.seed_fina_audit import SOURCE, load_env

TARGET = ("保留意见", "无法表示意见", "否定意见")
EXCLUDED = ("标准无保留意见", "带强调事项段的无保留意见")


def fetch_one(cur, sql: str, params=()) -> dict:
    cur.execute(sql, params)
    row = cur.fetchone()
    return dict(row) if row else {}


def fetch_all(cur, sql: str, params=()) -> list[dict]:
    cur.execute(sql, params)
    return [dict(row) for row in cur.fetchall()]


def summary(cur, batch_id: int) -> dict:
    return fetch_one(cur, """
        SELECT count(*) AS rows,
               count(DISTINCT ts_code) AS securities,
               count(DISTINCT (ts_code,end_date)) AS period_groups,
               min(ann_date) AS min_ann_date, max(ann_date) AS max_ann_date,
               min(end_date) AS min_end_date, max(end_date) AS max_end_date,
               count(*) FILTER (WHERE ann_date IS NULL) AS ann_date_null_rows,
               count(*) FILTER (WHERE end_date IS NULL) AS end_date_null_rows,
               count(*) FILTER (WHERE audit_result IS NULL OR btrim(audit_result)='')
                   AS audit_result_null_rows,
               count(*) FILTER (WHERE audit_fees IS NULL) AS audit_fees_null_rows,
               count(*) FILTER (WHERE audit_agency IS NULL OR btrim(audit_agency)='')
                   AS audit_agency_null_rows,
               count(*) FILTER (WHERE audit_sign IS NULL OR btrim(audit_sign)='')
                   AS audit_sign_null_rows,
               count(*) FILTER (WHERE to_char(end_date,'MMDD')='1231') AS annual_rows
        FROM public.fina_audit_snap WHERE batch_id=%s
    """, (batch_id,))


def duplicate_profile(cur, batch_id: int) -> dict:
    return fetch_one(cur, """
        WITH exact_dup AS (
          SELECT count(*) AS n FROM (
            SELECT ts_code,ann_date,end_date,audit_result,audit_fees,audit_agency,audit_sign
            FROM public.fina_audit_snap WHERE batch_id=%s
            GROUP BY 1,2,3,4,5,6,7 HAVING count(*)>1
          ) d
        ), groups AS (
          SELECT ts_code,end_date,count(*) AS n,
                 count(DISTINCT ann_date) AS ann_n,
                 count(DISTINCT audit_result) AS result_n
          FROM public.fina_audit_snap
          WHERE batch_id=%s AND to_char(end_date,'MMDD')='1231'
          GROUP BY 1,2 HAVING count(*)>1
        )
        SELECT (SELECT n FROM exact_dup) AS exact_duplicate_keys,
               count(*) AS multirow_groups,
               coalesce(sum(n),0) AS multirow_rows,
               count(*) FILTER (WHERE ann_n>1) AS ann_date_conflict_groups,
               count(*) FILTER (WHERE result_n>1) AS opinion_conflict_groups
        FROM groups
    """, (batch_id, batch_id))


def orphan_profile(cur, batch_id: int) -> dict:
    return fetch_one(cur, """
        WITH em AS (
          SELECT DISTINCT ts_code FROM public.entity_master
          WHERE batch_id=(SELECT max(batch_id) FROM public.entity_batch
                          WHERE source='tushare:stock_basic')
        )
        SELECT count(*) AS orphan_rows, count(DISTINCT a.ts_code) AS orphan_securities
        FROM public.fina_audit_snap a LEFT JOIN em USING(ts_code)
        WHERE a.batch_id=%s AND em.ts_code IS NULL
    """, (batch_id,))


def classification_profile(cur, batch_id: int) -> dict:
    return fetch_one(cur, """
        WITH annual AS (
          SELECT * FROM public.fina_audit_snap
          WHERE batch_id=%s AND to_char(end_date,'MMDD')='1231'
            AND ann_date>=DATE '2011-01-01' AND ann_date<DATE '2024-07-01'
            AND ts_code !~ '\\.BJ$'
        ), grouped AS (
          SELECT ts_code,end_date,count(*) AS n,
                 count(*) FILTER (WHERE ann_date IS NULL OR audit_result IS NULL
                                  OR btrim(audit_result)='') AS missing_n,
                 min(ann_date) AS ann_date,min(audit_result) AS audit_result
          FROM annual GROUP BY 1,2
        )
        SELECT count(*) AS research_groups,
               count(*) FILTER (WHERE missing_n>0) AS required_missing_groups,
               count(*) FILTER (WHERE missing_n=0 AND n>1) AS multirow_groups,
               count(*) FILTER (WHERE missing_n=0 AND n=1
                    AND audit_result=ANY(%s)) AS target_groups,
               count(*) FILTER (WHERE missing_n=0 AND n=1
                    AND audit_result=ANY(%s)) AS excluded_groups,
               count(*) FILTER (WHERE missing_n=0 AND n=1
                    AND NOT audit_result=ANY(%s) AND NOT audit_result=ANY(%s)) AS unknown_groups
        FROM grouped
    """, (batch_id, list(TARGET), list(EXCLUDED), list(TARGET), list(EXCLUDED)))


def opinion_distribution(cur, batch_id: int) -> list[dict]:
    return fetch_all(cur, """
        SELECT audit_result,count(*) AS rows,count(DISTINCT (ts_code,end_date)) AS groups
        FROM public.fina_audit_snap
        WHERE batch_id=%s AND to_char(end_date,'MMDD')='1231'
          AND ann_date>=DATE '2011-01-01' AND ann_date<DATE '2024-07-01'
          AND ts_code !~ '\\.BJ$'
        GROUP BY audit_result ORDER BY rows DESC,audit_result NULLS LAST
    """, (batch_id,))


def candidate_years(cur, batch_id: int) -> list[dict]:
    return fetch_all(cur, """
        WITH grouped AS (
          SELECT ts_code,end_date,count(*) AS n,
                 count(*) FILTER (WHERE ann_date IS NULL OR audit_result IS NULL
                                  OR btrim(audit_result)='') AS missing_n,
                 min(ann_date) AS ann_date,min(audit_result) AS audit_result
          FROM public.fina_audit_snap
          WHERE batch_id=%s AND to_char(end_date,'MMDD')='1231'
            AND ann_date>=DATE '2011-01-01' AND ann_date<DATE '2024-07-01'
            AND ts_code !~ '\\.BJ$'
          GROUP BY 1,2
        )
        SELECT extract(year FROM ann_date)::int AS year,audit_result,count(*) AS groups
        FROM grouped WHERE n=1 AND missing_n=0 AND audit_result=ANY(%s)
        GROUP BY 1,2 ORDER BY 1,2
    """, (batch_id, list(TARGET)))


def event_key_profile(cur, batch_id: int) -> dict:
    return fetch_one(cur, """
        WITH grouped AS (
          SELECT ts_code,end_date,count(*) AS n,
                 count(*) FILTER (WHERE ann_date IS NULL OR audit_result IS NULL
                                  OR btrim(audit_result)='') AS missing_n,
                 min(ann_date) AS ann_date,min(audit_result) AS audit_result
          FROM public.fina_audit_snap
          WHERE batch_id=%s AND to_char(end_date,'MMDD')='1231'
            AND ann_date>=DATE '2011-01-01' AND ann_date<DATE '2024-07-01'
            AND ts_code !~ '\\.BJ$'
          GROUP BY 1,2
        ), events AS (
          SELECT ts_code,ann_date,count(*) AS n FROM grouped
          WHERE n=1 AND missing_n=0 AND audit_result=ANY(%s)
          GROUP BY 1,2
        )
        SELECT count(*) AS event_keys,
               count(*) FILTER (WHERE n>1) AS duplicate_event_keys,
               coalesce(sum(n) FILTER (WHERE n>1),0) AS duplicate_event_rows
        FROM events
    """, (batch_id, list(TARGET)))


def build_profile(dsn: str) -> dict:
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on",
                         row_factory=dict_row) as conn, conn.cursor() as cur:
        batch = fetch_one(cur, """
            SELECT batch_id,source,asof_date,pull_time,note FROM public.fact_batch
            WHERE source=%s ORDER BY batch_id DESC LIMIT 1
        """, (SOURCE,))
        if not batch:
            raise RuntimeError("无 tushare:fina_audit 批次")
        batch_id = batch["batch_id"]
        return {
            "transaction_read_only": fetch_one(cur, "SHOW transaction_read_only")["transaction_read_only"],
            "batch": batch,
            "summary": summary(cur, batch_id),
            "duplicates": duplicate_profile(cur, batch_id),
            "orphans": orphan_profile(cur, batch_id),
            "classification": classification_profile(cur, batch_id),
            "opinion_distribution": opinion_distribution(cur, batch_id),
            "candidate_years": candidate_years(cur, batch_id),
            "event_keys": event_key_profile(cur, batch_id),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--env", default="/opt/quant/.env")
    args = parser.parse_args()
    env = load_env(args.env)
    if not env.get("QBASE_APP_DSN"):
        raise RuntimeError("缺QBASE_APP_DSN（不回显值）")
    payload = build_profile(env["QBASE_APP_DSN"])
    Path(args.output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
