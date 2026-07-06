#!/usr/bin/env python3
"""Q1 · Entity Master 种子采集(阿里云执行)。

从 tushare 拉 stock_basic(全宇宙含退市)+ namechange(历史名),落 qbase append-only 快照。
- 每源一个 entity_batch;master/alias 只 INSERT(触发器焊死 UPDATE/DELETE)。
- 双时戳:observed_time=本批 pull_time;valid_time=事件时(master=as-of,alias=启用日)。
- namechange #1858 静默缺失:分 ts_code 分片全量拉,并与整表单拉计数对照,delta 记入 batch.note。

秘钥纪律:TUSHARE_TOKEN / QBASE_APP_DSN 只从 .env 读,不落日志、不进 git。
用法:python seed_entity.py            # 跑种子
      python seed_entity.py --dry     # 只连通+计数,不落库
"""
import os
import sys
import time
import argparse
from datetime import datetime, timezone

# ── .env 读取(不引 dotenv 依赖;只取需要的键,绝不回显值)──────────────────────
def load_env(path):
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
    """tushare YYYYMMDD 字符串 → date;空/None → None。"""
    if not s or str(s).strip() in ("", "None", "nan"):
        return None
    s = str(s).strip()
    return datetime.strptime(s, "%Y%m%d").date()


def fetch_stock_basic(pro):
    """L/D/P 三态分别拉取并合并 —— 默认只返 L,退市/暂停必须显式 status 才回。"""
    frames = []
    for status in ("L", "D", "P"):
        df = pro.stock_basic(
            list_status=status,
            fields="ts_code,symbol,name,area,industry,market,exchange,"
                   "list_status,list_date,delist_date",
        )
        print(f"  stock_basic status={status}: {len(df)} 行", flush=True)
        frames.append(df)
    import pandas as pd
    return pd.concat(frames, ignore_index=True)


def fetch_namechange(pro, ts_codes, sleep_s):
    """分 ts_code 分片全量拉(抗 #1858);另做一次整表单拉测截断,返回 (rows, bulk_n, raw_n)。

    tushare namechange 源系统性脏:①整行重复交付(每条常出现两遍,全字段相同);
    ②同一段命名会并存 end 空/填、U/W 后缀、甚至错别字等多个 distinct 行(全宇宙 18% 的票有此碰撞)。
    L1 忠实底料(qbase 铁律7,人批 2026-07-06):落库前只做**整行去重**(去逐字节完全相同的双投递,保序),
    其余 distinct 行**全部照落,零判断**——"哪个 end 真 / 哪个名 canonical"留给 Q3 v_entity_alias 视图集中归一。
    唯一约束已放宽到全字段元组(005),故这些同自然键的 distinct 行不再撞约束。
    """
    # 整表单拉(受 #1858 截断,仅作对照证据)
    try:
        bulk_n = len(pro.namechange(fields="ts_code,name,start_date,end_date,ann_date"))
    except Exception as e:  # noqa: BLE001
        bulk_n = -1
        print(f"  namechange 整拉对照失败(仅证据用,不阻塞):{type(e).__name__}", flush=True)

    rows, done = [], 0
    for code in ts_codes:
        for attempt in range(4):
            try:
                df = pro.namechange(
                    ts_code=code,
                    fields="ts_code,name,start_date,end_date,ann_date",
                )
                for _, r in df.iterrows():
                    rows.append((
                        code, "name", r["name"],
                        ymd(r.get("start_date")), ymd(r.get("end_date")),
                        ymd(r.get("ann_date")),
                    ))
                break
            except Exception as e:  # noqa: BLE001  —— 多为限频,退避重试
                if attempt == 3:
                    raise
                time.sleep(1.5 * (attempt + 1))
        done += 1
        if done % 500 == 0:
            print(f"  namechange 分片 {done}/{len(ts_codes)} … 累计 {len(rows)} 名(含源双发)", flush=True)
        time.sleep(sleep_s)
    raw_n = len(rows)
    rows = list(dict.fromkeys(rows))  # 整行去重:只去逐字节相同的双投递,保序;同键 distinct 行照落(忠实,归一留 Q3 视图)
    return rows, bulk_n, raw_n


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--env", default=os.path.join(here, "..", "..", ".env"))
    ap.add_argument("--sleep", type=float, default=float(os.environ.get("TS_SLEEP", "0.12")),
                    help="namechange 分片调用间隔秒(抗限频)")
    ap.add_argument("--dry", action="store_true", help="只连通+计数,不落库")
    args = ap.parse_args()

    env = load_env(os.path.abspath(args.env))
    token = env.get("TUSHARE_TOKEN")
    dsn = env.get("QBASE_APP_DSN")
    if not token:
        sys.exit("缺 TUSHARE_TOKEN(.env)。请人写入 /opt/quant/.env 后重跑,勿在对话/git 出现。")
    if not dsn and not args.dry:
        sys.exit("缺 QBASE_APP_DSN(.env)。")

    import tushare as ts
    pro = ts.pro_api(token)
    pull_time = datetime.now(timezone.utc)
    asof = pull_time.date()
    print(f"[{pull_time.isoformat()}] 采集开始 as-of={asof}", flush=True)

    # ── 拉取 ────────────────────────────────────────────────────────────────
    basic = fetch_stock_basic(pro)
    universe = sorted(basic["ts_code"].unique().tolist())
    n_delist = int((basic["list_status"] == "D").sum())
    print(f"stock_basic 合计 {len(basic)} 行 / 唯一 ts_code {len(universe)}(退市 D={n_delist})", flush=True)

    alias_rows, bulk_n, raw_n = fetch_namechange(pro, universe, args.sleep)
    sharded_n = len(alias_rows)          # 去重后(落库数)
    dup_dropped = raw_n - sharded_n      # tushare 双发去掉的行数
    delta = sharded_n - bulk_n if bulk_n >= 0 else None
    print(f"namechange 分片:源拉 {raw_n} 行 → 整行去重后 {sharded_n} 名(去双发 {dup_dropped})"
          f" / 整拉对照 {bulk_n} / 去重后仍多出 {delta}(#1858 截断证据)", flush=True)

    if args.dry:
        print("--dry:不落库,结束。", flush=True)
        return

    # ── 落库(psycopg3,COPY;master/alias 只 INSERT)───────────────────────────
    import psycopg
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            # batch 1:stock_basic
            note_b = f"tushare stock_basic L/D/P 全宇宙;唯一 ts_code={len(universe)};退市 D={n_delist}"
            cur.execute(
                "INSERT INTO public.entity_batch(source,asof_date,pull_time,note) "
                "VALUES (%s,%s,%s,%s) RETURNING batch_id",
                ("tushare:stock_basic", asof, pull_time, note_b),
            )
            b_master = cur.fetchone()[0]
            with cur.copy(
                "COPY public.entity_master"
                "(batch_id,ts_code,symbol,name,area,industry,market,exchange,"
                "list_status,list_date,delist_date,valid_time,observed_time) FROM STDIN"
            ) as cp:
                for _, r in basic.iterrows():
                    cp.write_row((
                        b_master, r["ts_code"], r.get("symbol"), r.get("name"),
                        r.get("area"), r.get("industry"), r.get("market"), r.get("exchange"),
                        (r.get("list_status") or None), ymd(r.get("list_date")),
                        ymd(r.get("delist_date")), pull_time, pull_time,
                    ))

            # batch 2:namechange
            note_n = (f"tushare namechange 分 ts_code 分片全量;源拉={raw_n} 整行去重后={sharded_n}"
                      f"(去纯双投递{dup_dropped}) 整拉对照={bulk_n} 多出={delta}(#1858)"
                      f";忠实存全口径(人批 2026-07-06):同键 end空/填、U/W后缀、错别字等 distinct 行全照落,归一留 Q3 视图")
            cur.execute(
                "INSERT INTO public.entity_batch(source,asof_date,pull_time,note) "
                "VALUES (%s,%s,%s,%s) RETURNING batch_id",
                ("tushare:namechange", asof, pull_time, note_n),
            )
            b_alias = cur.fetchone()[0]
            with cur.copy(
                "COPY public.entity_alias"
                "(batch_id,ts_code,alias_type,alias,start_date,end_date,ann_date,"
                "valid_time,observed_time) FROM STDIN"
            ) as cp:
                for (code, atype, name, sd, ed, ad) in alias_rows:
                    vt = datetime.combine(sd, datetime.min.time(), tzinfo=timezone.utc) if sd else pull_time
                    cp.write_row((b_alias, code, atype, name, sd, ed, ad, vt, pull_time))
        conn.commit()

    # ── 核行数(落库后回读)────────────────────────────────────────────────────
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM entity_master WHERE batch_id=%s", (b_master,))
        m = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM entity_alias WHERE batch_id=%s", (b_alias,))
        a = cur.fetchone()[0]
    print(f"落库核行数:entity_master={m}(应={len(basic)}) "
          f"entity_alias={a}(应={sharded_n}) batch=({b_master},{b_alias})", flush=True)
    assert m == len(basic) and a == sharded_n, "核行数不符!"
    print("✅ 种子完成,核行数一致。", flush=True)


if __name__ == "__main__":
    main()
