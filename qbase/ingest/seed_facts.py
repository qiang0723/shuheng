#!/usr/bin/env python3
"""Q2 · 公共事实回填采集(阿里云执行):forecast(业绩预告)+ stk_holdertrade(股东增减持)。

全市场史(含退市)落 qbase append-only 快照(006 建表)。每源一个 fact_batch;
snap 表只 INSERT(触发器焊死 UPDATE/DELETE),修数=新 batch。

设计承 Q1(seed_entity)的两条经验:
- **锚在 entity_master**:宇宙(含退市 ts_code)取自 Q1 落库的 entity_master 最新 batch,
  不重拉 stock_basic —— Q2 用 Q1 的实体口径,保 L1 自洽。
- **分片抗截断(#1858)**:tushare 单次调用硬顶 10000 且静默截断。按 ts_code 逐票分片全量拉,
  每票行数远小于万级,永不触顶;另做一次 period 整拉对照,delta 记入 batch.note 作截断证据。

双时戳:observed_time=本批 pull_time(回填批次时刻,不冒充实时,铁律2);
        valid_time=事件时(forecast: ann_date→first_ann_date→as-of;holdertrade: ann_date→as-of)。
忠实存全:落库前只做**整行去重**(去 tushare 逐字节双投递,保序),同键 distinct 行全照落。

秘钥纪律:TUSHARE_TOKEN / QBASE_APP_DSN 只从 .env 读,不落日志、不进 git。
用法:python seed_facts.py                    # 全量回填
      python seed_facts.py --dry             # 只连通+抽样验字段/计数,不落库
      python seed_facts.py --only forecast   # 只跑一源(forecast|holdertrade)
"""
import os
import sys
import time
import math
import argparse
from datetime import datetime, timezone


# ── .env 读取(不引 dotenv;只取需要的键,绝不回显值)──────────────────────────
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
    """tushare YYYYMMDD 字符串 → date;空/None/nan → None。"""
    if s is None:
        return None
    s = str(s).strip()
    if s in ("", "None", "nan", "NaT"):
        return None
    return datetime.strptime(s[:8], "%Y%m%d").date()


def num(x):
    """tushare 数值 → float;NaN/空/None → None(忠实照落,不填默认)。"""
    if x is None:
        return None
    if isinstance(x, float) and math.isnan(x):
        return None
    s = str(x).strip()
    if s in ("", "None", "nan", "NaT"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def txt(x):
    """空/nan 文本 → None。"""
    if x is None:
        return None
    s = str(x).strip()
    return None if s in ("", "None", "nan", "NaT") else s


# ── 采集源定义:字段清单 + 取值映射 + 事件时口径 ─────────────────────────────
FORECAST_FIELDS = ("ts_code,ann_date,end_date,type,p_change_min,p_change_max,"
                   "net_profit_min,net_profit_max,last_parent_net,first_ann_date,"
                   "summary,change_reason")
HOLDER_FIELDS = ("ts_code,ann_date,holder_name,holder_type,in_de,change_vol,"
                 "change_ratio,after_share,after_ratio,avg_price,total_share,"
                 "begin_date,close_date")


def forecast_row(code, r, pull_time):
    ann = ymd(r.get("ann_date"))
    first_ann = ymd(r.get("first_ann_date"))
    vt = ann or first_ann
    vt = datetime.combine(vt, datetime.min.time(), tzinfo=timezone.utc) if vt else pull_time
    # 顺序须与 COPY 列一致(见 write_batch)
    return (
        code, ann, ymd(r.get("end_date")), txt(r.get("type")),
        num(r.get("p_change_min")), num(r.get("p_change_max")),
        num(r.get("net_profit_min")), num(r.get("net_profit_max")),
        num(r.get("last_parent_net")), first_ann,
        txt(r.get("summary")), txt(r.get("change_reason")), vt,
    )


def holder_row(code, r, pull_time):
    ann = ymd(r.get("ann_date"))
    vt = datetime.combine(ann, datetime.min.time(), tzinfo=timezone.utc) if ann else pull_time
    return (
        code, ann, txt(r.get("holder_name")), txt(r.get("holder_type")),
        txt(r.get("in_de")), num(r.get("change_vol")), num(r.get("change_ratio")),
        num(r.get("after_share")), num(r.get("after_ratio")), num(r.get("avg_price")),
        num(r.get("total_share")), ymd(r.get("begin_date")), ymd(r.get("close_date")), vt,
    )


SOURCES = {
    "forecast": {
        "source": "tushare:forecast",
        "api": "forecast",
        "fields": FORECAST_FIELDS,
        "row": forecast_row,
        "table": "public.forecast_snap",
        "cols": ("batch_id,ts_code,ann_date,end_date,type,p_change_min,p_change_max,"
                 "net_profit_min,net_profit_max,last_parent_net,first_ann_date,"
                 "summary,change_reason,valid_time,observed_time"),
    },
    "holdertrade": {
        "source": "tushare:stk_holdertrade",
        "api": "stk_holdertrade",
        "fields": HOLDER_FIELDS,
        "row": holder_row,
        "table": "public.holdertrade_snap",
        "cols": ("batch_id,ts_code,ann_date,holder_name,holder_type,in_de,change_vol,"
                 "change_ratio,after_share,after_ratio,avg_price,total_share,"
                 "begin_date,close_date,valid_time,observed_time"),
    },
}


# ── 分片拉取(逐 ts_code,抗 #1858 截断;退避重试抗限频)───────────────────────
def fetch_sharded(pro, spec, ts_codes, pull_time, sleep_s, log_every=500):
    rows, done = [], 0
    api = getattr(pro, spec["api"])
    for code in ts_codes:
        for attempt in range(4):
            try:
                df = api(ts_code=code, fields=spec["fields"])
                for _, r in df.iterrows():
                    rows.append(spec["row"](code, r, pull_time))
                break
            except Exception as e:  # noqa: BLE001 —— 多为限频,退避重试
                if attempt == 3:
                    raise
                time.sleep(1.5 * (attempt + 1))
        done += 1
        if done % log_every == 0:
            print(f"  {spec['api']} 分片 {done}/{len(ts_codes)} … 累计 {len(rows)} 行(含源双发)",
                  flush=True)
        time.sleep(sleep_s)
    raw_n = len(rows)
    rows = list(dict.fromkeys(rows))  # 整行去重:只去逐字节相同双投递,保序;同键 distinct 行照落
    return rows, raw_n


def load_universe(cur):
    """宇宙取自 entity_master 最新 batch(含退市 ts_code)。Q2 锚在 Q1 实体口径。"""
    cur.execute("SELECT max(batch_id) FROM public.entity_master "
                "WHERE batch_id IN (SELECT batch_id FROM public.entity_batch "
                "WHERE source='tushare:stock_basic')")
    b = cur.fetchone()[0]
    if b is None:
        sys.exit("entity_master 无 stock_basic batch —— 请先完成 Q1 种子。")
    cur.execute("SELECT DISTINCT ts_code FROM public.entity_master WHERE batch_id=%s ORDER BY ts_code",
                (b,))
    return [r[0] for r in cur.fetchall()], b


def write_batch(conn, spec, rows, asof, pull_time, note):
    """一个 fact_batch + COPY 落 snap 表;回读核行数。返回 (batch_id, 落库行数)。"""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO public.fact_batch(source,asof_date,pull_time,note) "
            "VALUES (%s,%s,%s,%s) RETURNING batch_id",
            (spec["source"], asof, pull_time, note),
        )
        bid = cur.fetchone()[0]
        with cur.copy(f"COPY {spec['table']}({spec['cols']}) FROM STDIN") as cp:
            for row in rows:
                cp.write_row((bid, *row, pull_time))  # +observed_time
    conn.commit()
    with conn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {spec['table']} WHERE batch_id=%s", (bid,))
        n = cur.fetchone()[0]
    return bid, n


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--env", default=os.path.join(here, "..", "..", ".env"))
    ap.add_argument("--sleep", type=float, default=float(os.environ.get("TS_SLEEP", "0.12")),
                    help="分片调用间隔秒(抗限频)")
    ap.add_argument("--only", choices=("forecast", "holdertrade"), help="只跑一源")
    ap.add_argument("--dry", action="store_true",
                    help="只连通+抽样(前若干票)验字段/计数,不落库")
    ap.add_argument("--dry-sample", type=int, default=8, help="--dry 抽样票数")
    args = ap.parse_args()

    env = load_env(os.path.abspath(args.env))
    token = env.get("TUSHARE_TOKEN")
    dsn = env.get("QBASE_APP_DSN")
    if not token:
        sys.exit("缺 TUSHARE_TOKEN(.env)。请人写入 /opt/quant/.env 后重跑,勿在对话/git 出现。")
    if not dsn:
        sys.exit("缺 QBASE_APP_DSN(.env)。宇宙取自 entity_master,需连库。")

    import tushare as ts
    import psycopg
    pro = ts.pro_api(token)
    pull_time = datetime.now(timezone.utc)
    asof = pull_time.date()
    which = [args.only] if args.only else ["forecast", "holdertrade"]
    print(f"[{pull_time.isoformat()}] Q2 采集开始 as-of={asof} 源={which} dry={args.dry}", flush=True)

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            universe, ubatch = load_universe(cur)
        print(f"宇宙(entity_master batch={ubatch}含退市):{len(universe)} 只 ts_code", flush=True)

        if args.dry:
            sample = universe[:args.dry_sample]
            print(f"--dry:抽样 {len(sample)} 票验字段/连通,不落库。", flush=True)
            for key in which:
                spec = SOURCES[key]
                rows, raw_n = fetch_sharded(pro, spec, sample, pull_time, args.sleep, log_every=9999)
                print(f"  [{key}] 抽样 {len(sample)}票 → 源拉 {raw_n} 行 / 整行去重后 {len(rows)}",
                      flush=True)
                if rows:
                    print(f"    首行样例(字段就位验证):{rows[0]}", flush=True)
            print("--dry 完成:字段/连通/去重逻辑通过。", flush=True)
            return

        for key in which:
            spec = SOURCES[key]
            print(f"── [{key}] 全量分片拉取(源={spec['source']})──", flush=True)
            rows, raw_n = fetch_sharded(pro, spec, universe, pull_time, args.sleep)
            dedup = len(rows)
            note = (f"{spec['source']} 分 ts_code 分片全量(锚 entity_master batch={ubatch},"
                    f"宇宙 {len(universe)}含退市);源拉 {raw_n} → 整行去重后 {dedup}"
                    f"(去纯双投递 {raw_n - dedup});忠实存全,同键 distinct 行照落。")
            bid, n = write_batch(conn, spec, rows, asof, pull_time, note)
            print(f"  [{key}] 落库 batch={bid} 行数={n}(应={dedup})", flush=True)
            assert n == dedup, f"[{key}] 核行数不符!{n}!={dedup}"

    print("✅ Q2 采集完成,核行数一致。", flush=True)


if __name__ == "__main__":
    main()
