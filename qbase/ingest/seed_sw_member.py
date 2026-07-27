#!/usr/bin/env python3
"""exp24 数据前置 · 申万半导体 L2(801081.SI)历史成分重采(阿里云执行;人令 2026-07-27 二,裁定 B1/C2)。

源=tushare `index_member_all`(C2:重采,不走老机;**接口不可用即停报,不自动改源**)。
语义=B1:申万现行(2021版)体系回溯+历史进出日期=半PIT,如实照落不包装。
范围红线:单指数 801081.SI(不扩电子链、不扩行业族)。
范式承 seed_marketdata.py:fact_batch(source='tushare:sw_member')+append-only COPY+整行去重+
双时戳(valid_time=in_date;observed_time=本批 pull_time)。原始返回 CSV+SHA 存内部证据包。

用法:python seed_sw_member.py --evidence /root/s24dataclose/tushare_raw [--dry]
"""
import argparse
import hashlib
import os
import sys
from datetime import datetime, timezone

import psycopg
import tushare as ts

INDEX_CODE = "801081.SI"
FIELDS = "l1_code,l1_name,l2_code,l2_name,l3_code,l3_name,ts_code,name,in_date,out_date,is_new"


def load_env(path="/opt/quant/.env"):
    env = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def ymd(s):
    if s is None:
        return None
    s = str(s).strip()
    if s in ("", "None", "nan", "NaT"):
        return None
    return datetime.strptime(s[:8], "%Y%m%d").date()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--evidence", required=True)
    a = ap.parse_args()
    os.makedirs(a.evidence, exist_ok=True)
    env = load_env()
    pull_time = datetime.now(timezone.utc)
    pro = ts.pro_api(env["TUSHARE_TOKEN"])

    frames = []
    for flag in ("Y", "N"):        # 现役 + 已剔除(index_member_all 默认只返现役;两态取全)
        try:
            df = pro.index_member_all(l2_code=INDEX_CODE, is_new=flag, fields=FIELDS)
        except Exception as e:     # C2:接口不可用即停报,不自动改走老机
            raise RuntimeError(f"tushare index_member_all(is_new={flag}) 不可用,停报(裁定C2): {e}")
        print(f"is_new={flag}: {len(df)} 行", flush=True)
        frames.append(df)
    import pandas as pd
    df = pd.concat(frames, ignore_index=True)
    assert len(df) > 0, "零行返回,停报"
    assert (df["l2_code"] == INDEX_CODE).all(), "混入非 801081.SI 行,停报"

    raw_csv = os.path.join(a.evidence, f"tushare_index_member_all_{INDEX_CODE}.csv")
    df.to_csv(raw_csv, index=False)
    sha = hashlib.sha256(open(raw_csv, "rb").read()).hexdigest()
    print(f"原始返回 CSV: {raw_csv} sha256={sha}", flush=True)

    rows, seen = [], set()
    for r in df.itertuples(index=False):
        rec = (INDEX_CODE, str(r.ts_code), None if pd.isna(r.name) else str(r.name),
               None if pd.isna(r.l1_code) else str(r.l1_code),
               None if pd.isna(r.l1_name) else str(r.l1_name),
               None if pd.isna(r.l3_code) else str(r.l3_code),
               None if pd.isna(r.l3_name) else str(r.l3_name),
               ymd(getattr(r, "in_date")), ymd(getattr(r, "out_date")),
               None if pd.isna(r.is_new) else str(r.is_new))
        if rec in seen:            # 整行去重(源双投递兜底)
            continue
        seen.add(rec)
        rows.append(rec)
    n_in = sum(1 for r in rows if r[7] is not None)
    n_out = sum(1 for r in rows if r[8] is not None)
    print(f"去重后 {len(rows)} 行;in_date 非空 {n_in};out_date 非空(已剔除){n_out}", flush=True)
    assert all(r[7] is not None for r in rows), "存在空 in_date,停报(区间语义不成立)"

    if a.dry:
        print("--dry: 不落库")
        return 0

    note = (f"exp24 数据前置(人令2026-07-27二,裁定B1/C2):tushare index_member_all 重采 "
            f"{INDEX_CODE} 申万半导体L2 历史成分(现役+已剔除两态取全);半PIT=现行2021版体系回溯+"
            f"历史进出日期,如实披露;原始CSV+SHA 存内部证据包;单指数不扩。sha256={sha[:16]}…")
    with psycopg.connect(env["QBASE_APP_DSN"]) as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO public.fact_batch(source,asof_date,pull_time,note) "
                    "VALUES (%s,%s,%s,%s) RETURNING batch_id",
                    ("tushare:sw_member", pull_time.date(), pull_time, note))
        bid = cur.fetchone()[0]
        cols = ("batch_id,index_code,ts_code,name,l1_code,l1_name,l3_code,l3_name,"
                "in_date,out_date,is_new,valid_time,observed_time")
        with cur.copy(f"COPY public.sw_member_snap ({cols}) FROM STDIN") as cp:
            for rec in rows:
                vt = datetime.combine(rec[7], datetime.min.time(), tzinfo=timezone.utc)
                cp.write_row((bid,) + rec[:8] + (rec[8], rec[9], vt, pull_time))
        conn.commit()
        cur.execute("SELECT count(*) FROM public.sw_member_snap WHERE batch_id=%s", (bid,))
        n = cur.fetchone()[0]
        print(f"落库: batch_id={bid} rows={n}", flush=True)
        assert n == len(rows), "落库行数≠去重行数,停报"
    return 0


if __name__ == "__main__":
    sys.exit(main())
