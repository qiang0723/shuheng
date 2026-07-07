#!/usr/bin/env python3
"""Q3-B · 行情回填采集(阿里云执行):日线 daily + 复权因子 adj_factor + 交易日历 trade_cal。

人拍 B(2026-07-07):marketdata=梯队4 公共事实,回填进 qbase 本地表(不走 FDW、不碰老平台),
源=tushare(与 Q2 同源)。全市场史(含退市)落 007 建的 append-only 快照;每源一 fact_batch;
snap 只 INSERT(触发器焊死 UPDATE/DELETE),修数/复权重述=新 batch。

承 seed_facts(Q2)两经验:
- **锚在 entity_master**:宇宙(含退市 ts_code)取 Q1 落库 entity_master 最新 stock_basic batch,不重拉。
- **分片抗截断(#1858)**:tushare 单次硬顶 10000 且静默截断。daily/adj_factor 按 ts_code 逐票分片
  (每票全史 <8000 行,永不触顶);trade_cal 按年分片(全历史 ~1.3万日 > 1万,逐年拉规避)。

双时戳:observed_time=本批 pull_time(回填时刻,不冒充实时,铁律2);valid_time=行情时(trade_date/cal_date)。
忠实存全:落库前只整行去重(去 tushare 逐字节双投递,保序),同键 distinct 行全照落;不归一不打分。
归一(后复权/停牌/涨跌停/板块/ST/行业)是 Q3 视图的活,此处只存原始 OHLCV/因子/日历。

秘钥纪律:TUSHARE_TOKEN / QBASE_APP_DSN 只从 .env 读,不落日志、不进 git。
用法:python seed_marketdata.py                 # 全量回填(daily+adj_factor+trade_cal)
      python seed_marketdata.py --dry          # 只连通+抽样验字段/计数,不落库
      python seed_marketdata.py --only daily    # 只跑一源(daily|adj_factor|trade_cal)
      python seed_marketdata.py --sleep 0.3     # 分片间隔(daily API 较重,限频时调大)
"""
import os
import sys
import time
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
    s = str(x).strip()
    if s in ("", "None", "nan", "NaT"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def txt(x):
    if x is None:
        return None
    s = str(x).strip()
    return s if s not in ("", "None", "nan", "NaT") else None


def _vt(d, pull_time):
    """行情日 date → 事件时 timestamptz(UTC 零点);缺则退 batch pull_time。"""
    return datetime.combine(d, datetime.min.time(), tzinfo=timezone.utc) if d else pull_time


DAILY_FIELDS = "ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount"
ADJ_FIELDS = "ts_code,trade_date,adj_factor"
CAL_FIELDS = "exchange,cal_date,is_open,pretrade_date"


def daily_row(code, r, pull_time):
    d = ymd(r.get("trade_date"))
    # 顺序须与 COPY 列一致(见 SOURCES.cols / write_batch)
    return (
        code, d, num(r.get("open")), num(r.get("high")), num(r.get("low")),
        num(r.get("close")), num(r.get("pre_close")), num(r.get("change")),
        num(r.get("pct_chg")), num(r.get("vol")), num(r.get("amount")), _vt(d, pull_time),
    )


def adj_row(code, r, pull_time):
    d = ymd(r.get("trade_date"))
    return (code, d, num(r.get("adj_factor")), _vt(d, pull_time))


def cal_row(_code, r, pull_time):
    d = ymd(r.get("cal_date"))
    iso = r.get("is_open")
    iso = int(iso) if iso is not None and str(iso).strip() not in ("", "None", "nan") else None
    return (txt(r.get("exchange")), d, iso, ymd(r.get("pretrade_date")), _vt(d, pull_time))


SOURCES = {
    "daily": {
        "source": "tushare:daily", "api": "daily", "fields": DAILY_FIELDS,
        "row": daily_row, "table": "public.bar_daily_snap", "sharded": "ts_code",
        "cols": ("batch_id,ts_code,trade_date,open,high,low,close,pre_close,change,"
                 "pct_chg,vol,amount,valid_time,observed_time"),
    },
    "adj_factor": {
        "source": "tushare:adj_factor", "api": "adj_factor", "fields": ADJ_FIELDS,
        "row": adj_row, "table": "public.adj_factor_snap", "sharded": "ts_code",
        "cols": "batch_id,ts_code,trade_date,adj_factor,valid_time,observed_time",
    },
    "trade_cal": {
        "source": "tushare:trade_cal", "api": "trade_cal", "fields": CAL_FIELDS,
        "row": cal_row, "table": "public.trade_cal_snap", "sharded": "year",
        "cols": "batch_id,exchange,cal_date,is_open,pretrade_date,valid_time,observed_time",
    },
}


def _call_retry(api, sleep_s, **kw):
    """退避重试抗限频(4 次)。"""
    for attempt in range(4):
        try:
            return api(**kw)
        except Exception:  # noqa: BLE001 —— 多为限频
            if attempt == 3:
                raise
            time.sleep(1.5 * (attempt + 1))
    return None


def fetch_sharded_code(pro, spec, ts_codes, pull_time, sleep_s, log_every=500):
    """daily/adj_factor:逐 ts_code 分片全史。"""
    rows, done = [], 0
    api = getattr(pro, spec["api"])
    for code in ts_codes:
        df = _call_retry(api, sleep_s, ts_code=code, fields=spec["fields"])
        for _, r in df.iterrows():
            rows.append(spec["row"](code, r, pull_time))
        done += 1
        if done % log_every == 0:
            print(f"  {spec['api']} 分片 {done}/{len(ts_codes)} … 累计 {len(rows)} 行(含源双发)",
                  flush=True)
        time.sleep(sleep_s)
    raw_n = len(rows)
    rows = list(dict.fromkeys(rows))  # 整行去重:只去逐字节相同双投递,保序
    return rows, raw_n


def fetch_sharded_year(pro, spec, y0, y1, pull_time, sleep_s):
    """trade_cal:按年分片(全历史 >1万日,逐年拉规避 10000 截断)。SSE 全市场同历。"""
    rows = []
    api = getattr(pro, spec["api"])
    for y in range(y0, y1 + 1):
        df = _call_retry(api, sleep_s, exchange="SSE",
                         start_date=f"{y}0101", end_date=f"{y}1231", fields=spec["fields"])
        for _, r in df.iterrows():
            rows.append(spec["row"](None, r, pull_time))
        time.sleep(sleep_s)
    raw_n = len(rows)
    rows = list(dict.fromkeys(rows))
    return rows, raw_n


def load_universe(cur):
    """宇宙取自 entity_master 最新 stock_basic batch(含退市 ts_code)。承 Q1/Q2 实体口径。"""
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


def run_source(pro, spec, universe, ubatch, pull_time, sleep_s):
    """按分片类型取数 → 返回 (rows, raw_n, note_prefix)。"""
    if spec["sharded"] == "ts_code":
        rows, raw_n = fetch_sharded_code(pro, spec, universe, pull_time, sleep_s)
        scope = f"分 ts_code 分片全史(锚 entity_master batch={ubatch},宇宙 {len(universe)}含退市)"
    else:  # year(trade_cal)
        y0, y1 = 1990, pull_time.year
        rows, raw_n = fetch_sharded_year(pro, spec, y0, y1, pull_time, sleep_s)
        scope = f"按年分片 {y0}..{y1}(SSE 全市场同历)"
    return rows, raw_n, scope


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--env", default=os.path.join(here, "..", "..", ".env"))
    ap.add_argument("--sleep", type=float, default=float(os.environ.get("TS_SLEEP", "0.3")),
                    help="分片调用间隔秒(daily API 较重,默认 0.3;限频时调大)")
    ap.add_argument("--only", choices=("daily", "adj_factor", "trade_cal"), help="只跑一源")
    ap.add_argument("--dry", action="store_true", help="只连通+抽样验字段/计数,不落库")
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
    which = [args.only] if args.only else ["daily", "adj_factor", "trade_cal"]
    print(f"[{pull_time.isoformat()}] Q3-B 行情采集开始 as-of={asof} 源={which} dry={args.dry}",
          flush=True)

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            universe, ubatch = load_universe(cur)
        print(f"宇宙(entity_master batch={ubatch}含退市):{len(universe)} 只 ts_code", flush=True)

        if args.dry:
            sample = universe[:args.dry_sample]
            print(f"--dry:抽样 {len(sample)} 票(trade_cal 只拉近 2 年)验字段/连通,不落库。", flush=True)
            for key in which:
                spec = SOURCES[key]
                if spec["sharded"] == "ts_code":
                    rows, raw_n = fetch_sharded_code(pro, spec, sample, pull_time, args.sleep,
                                                     log_every=9999)
                else:
                    rows, raw_n = fetch_sharded_year(pro, spec, pull_time.year - 1, pull_time.year,
                                                     pull_time, args.sleep)
                print(f"  [{key}] 源拉 {raw_n} 行 / 整行去重后 {len(rows)}", flush=True)
                if rows:
                    print(f"    首行样例(字段就位验证):{rows[0]}", flush=True)
            print("--dry 完成:字段/连通/去重逻辑通过。", flush=True)
            return

        for key in which:
            spec = SOURCES[key]
            print(f"── [{key}] 全量拉取(源={spec['source']})──", flush=True)
            rows, raw_n, scope = run_source(pro, spec, universe, ubatch, pull_time, args.sleep)
            dedup = len(rows)
            note = (f"{spec['source']} {scope};源拉 {raw_n} → 整行去重后 {dedup}"
                    f"(去纯双投递 {raw_n - dedup});忠实存全,同键 distinct 行照落。")
            bid, n = write_batch(conn, spec, rows, asof, pull_time, note)
            print(f"  [{key}] 落库 batch={bid} 行数={n}(应={dedup})", flush=True)
            assert n == dedup, f"[{key}] 核行数不符!{n}!={dedup}"

    print("✅ Q3-B 行情采集完成,核行数一致。", flush=True)


if __name__ == "__main__":
    main()
