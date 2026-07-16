"""#3 loader:减持预披露 JSONL staging → qbase `holder_sell_predisclose_snap`(单事务批入)。

承 seed_holder_predisclose.py 的 hits.jsonl:建一个 fact_batch(lineage)+ 一次性 COMMIT 全量插入。
append-only 触发器焊死(011);去重 scope = (announcement_id, stock_code)=同一原始记录重复才去,keep first。
⚠口径修订(2026-07-16 人令,§3 窄闸):跨代码同 announcement_id(实体代码变更,如 600087→601975)两行
**均为原始事实,全部保留**;事件日归属判断=L2 适配器 PIT 规则,L1 零判断不得依输入顺序取舍。
旧 scope "announcement_id keep first" 就此作废。
双时戳:valid_time=公告时点(采集侧已转 UTC)、observed_time=DB now()(=采集批时刻由 batch 记)。

秘钥:DSN 只从 .env 读(QBASE_APP_DSN),不回显。用法(aliyun):
  set -a; . /opt/quant/.env; set +a
  /opt/venvs/qbase-ingest/bin/python -m qbase.ingest.load_holder_predisclose --hits /tmp/s3prod/hits.jsonl
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os

import psycopg
from psycopg.types.json import Json  # noqa: F401  (未用,保留以示 jsonb 可扩)

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _dsn() -> str:
    dsn = os.environ.get("QBASE_APP_DSN")
    if not dsn:
        env = {}
        for line in open(os.path.join(_ROOT, ".env")):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
        dsn = env.get("QBASE_APP_DSN")
    if not dsn:
        raise RuntimeError("缺 QBASE_APP_DSN(.env)")
    return dsn


_invalid_dates: list = []


def _date(s):
    """ISO 串→date;非法日历日期(公告原文笔误如 2017-09-31,L3 如实抄录)→ NULL+留痕不静默,
    原文串仍在 reduce_period_text 列保真(L1 忠实:date 列只装真日期,不猜不改)。"""
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        _invalid_dates.append(s)
        return None


def load(hits_path: str, note: str = "") -> None:
    # 读 + 去重((announcement_id, stock_code) keep first;跨代码同 id 两行均保留=原始事实,归属属 L2)
    recs, seen = [], set()
    with open(hits_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            key = (r.get("announcement_id"), r.get("stock_code"))
            if key in seen:
                continue
            seen.add(key)
            recs.append(r)
    print(f"staging 命中 {len(recs)} 条((announcement_id,stock_code) 去重后)")

    conn = psycopg.connect(_dsn())
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO fact_batch (source, asof_date, pull_time, note) "
                "VALUES (%s, CURRENT_DATE, now(), %s) RETURNING batch_id",
                ("cninfo:holder_sell_predisclose", note or f"减持预披露生产采集 {len(recs)} 条"))
            batch_id = cur.fetchone()[0]
            rows = [(
                batch_id, r["ts_code"], r["stock_code"], r.get("announcement_id"),
                r["title"], r.get("announcement_type"), r.get("source_url"),
                r.get("holder_name"), r.get("reduce_ratio_max_pct"),
                _date(r.get("reduce_period_start")), _date(r.get("reduce_period_end")),
                r.get("reduce_period_text"), r.get("reduce_period_kind"),
                r.get("parse_fail") or [], r.get("title_reason"),
                r.get("valid_time"),
            ) for r in recs]
            cur.executemany(
                "INSERT INTO holder_sell_predisclose_snap "
                "(batch_id, ts_code, stock_code, announcement_id, title, announcement_type, source_url, "
                " holder_name, reduce_ratio_max_pct, reduce_period_start, reduce_period_end, "
                " reduce_period_text, reduce_period_kind, parse_fail, title_reason, valid_time) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", rows)
        conn.commit()   # 单事务一次性 COMMIT
        print(f"✅ batch_id={batch_id} 入库 {len(rows)} 条(单事务 COMMIT;append-only 焊死)")
        if _invalid_dates:
            print(f"⚠ 非法日历日期置 NULL {len(_invalid_dates)} 项(原文在 reduce_period_text 保真): {_invalid_dates}")
    finally:
        conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hits", required=True)
    ap.add_argument("--note", default="")
    a = ap.parse_args()
    load(a.hits, a.note)
