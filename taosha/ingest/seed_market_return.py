#!/usr/bin/env python3
"""淘沙 L2 · 全市场等权日收益预计算落库(切片3 步3;002 建表)。

读 qbase 归一视图 explore_reader_prices(经视图=继承 holdout<2024-07-01 + 北交所.BJ排除 + 后复权),
按 ts_code 流式,复用**冻结收益核** compute/returns.py 逐票算跨缺口对数收益,等权聚合成
全市场等权日收益序列,append-only 落 taosha market_batch + market_eqw_return(002)。

口径(与 002 表注逐字对应,骗不了人):
  ret_eqw[d] = 当日【有 present bar 且有前序 present bar】的票 log(close_d/close_前序present) 的等权平均。
  n_stocks[d] = 分母 = 上述票数(停牌缺行不进分母;IPO 首个 bar 无前序价不进;早年薄截面照算)。
  视图无 null 价行(停牌=缺行),故 per 票"相邻 present 行比值"恒等于 returns.multi_day 跨缺口收益。
  轴=日历(约束②):源 = explore_reader_prices JOIN explore_reader_calendar,基准定义在 SSE 交易日轴
    (=引擎消费轴);早年 tushare 非交易日 bar(周日,官方 trade_cal is_open=0)结构性排除,
    收益自然跨到前一日历交易日(returns.py 跨缺口)。

双算闸(骗不了人):Python(冻结 returns.py)=落库权威;SQL 窗口 avg(ln(close/lag)) 独立复算;
  逐日 |Δret|<1e-9 且 n_stocks 整数全等,否则**中止不落库**。
硬闸(holdout 泄漏):max(trade_date) < 2024-07-01 且 out_rows 远小于全日历 8797(≈8187),否则中止。

红线(taosha CLAUDE.md §2):不 import 兄弟目录(qbase/radar);数据入口=qbase 视图(经 DSN,非 import)。
  读取身份=QBASE_APP_DSN(可 SELECT 视图;holdout/.BJ/后复权 由视图定义结构性保证,与账号无关);
  写入身份=TAOSHA_APP_DSN(只 INSERT,触发器焊 append-only);引擎最小权 taosha_engine 属步4。
秘钥纪律:DSN 只从 .env 读,不落日志、不回显、不进 git。

用法:
  python -m taosha.ingest.seed_market_return --selftest   # 纯核手算自检(不碰库)
  python -m taosha.ingest.seed_market_return --dry        # 连库+双算闸+硬闸,不落库
  python -m taosha.ingest.seed_market_return              # 全量预算+落库
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import os
import sys
from typing import Iterable, Iterator, Optional

from taosha.compute.frozen_config import COMPOUNDING, audit_digest
from taosha.compute.returns import log_rates_from_prices
from taosha.reader.contract import HOLDOUT_START

VIEW = "explore_reader_prices"
FULL_CALENDAR_TRADING_DAYS = 8797   # 全日历(1990→2026)交易日数;落库行数落此值=holdout 泄漏事故
CROSSCHECK_TOL = 1e-9               # 逐日 |Δret| 容差(两独立实现 float 序噪声上界)


# ── .env 读取(只取需要键,绝不回显值)────────────────────────────────────────
def load_env(path: str) -> dict:
    env = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


# ── 纯核:逐票冻结收益核 → 全市场等权聚合(可脱库自检)────────────────────────
def compute_market_eqw(rows: Iterable[tuple]) -> list[tuple[dt.date, float, int]]:
    """rows: (ts_code, trade_date, close) 迭代器,**须按 (ts_code, trade_date) 升序**。
    返回 [(trade_date, ret_eqw, n_stocks), ...] 按 trade_date 升序。

    逐票:close 序列 → log_rates_from_prices(Close, multi_day)(冻结核);
    rate[j] 到达日 = dates[j+1](跨缺口收益落恢复日,对齐约定 rates[i]↔dates[i+1]);
    等权聚合:acc[到达日] += rate;cnt[到达日] += 1。ret_eqw = acc/cnt,n_stocks = cnt。
    """
    acc: dict[dt.date, float] = {}
    cnt: dict[dt.date, int] = {}

    cur_code: Optional[str] = None
    dates: list[dt.date] = []
    closes: list[Optional[float]] = []

    def flush():
        if cur_code is None or len(closes) < 2:
            return
        rates = log_rates_from_prices(closes, quote="Close", multi_day=True)
        # rate[j] ↔ dates[j+1](恢复日/到达日)
        for j, r in enumerate(rates):
            if r is None:
                continue
            d = dates[j + 1]
            acc[d] = acc.get(d, 0.0) + r
            cnt[d] = cnt.get(d, 0) + 1

    prev_date_in_code: Optional[dt.date] = None
    for ts_code, trade_date, close in rows:
        if ts_code != cur_code:
            flush()
            cur_code = ts_code
            dates = []
            closes = []
            prev_date_in_code = None
        # 单调性护栏:同票日期须严格递增(输入排序前提;违反即输入未排序,炸而非默默错算)
        if prev_date_in_code is not None and trade_date <= prev_date_in_code:
            raise ValueError(f"输入未按 (ts_code,trade_date) 升序: {ts_code} {prev_date_in_code}->{trade_date}")
        prev_date_in_code = trade_date
        dates.append(trade_date)
        closes.append(None if close is None else float(close))
    flush()

    return [(d, acc[d] / cnt[d], cnt[d]) for d in sorted(acc)]


# 源=prices ∩ calendar 交易日轴(约束②):剔除早年非交易日 bar,基准落 SSE 交易日轴。
SRC = (f"SELECT p.ts_code, p.trade_date, p.close FROM {VIEW} p "
       "JOIN explore_reader_calendar c USING (trade_date)")


# ── qbase 视图流式(server-side cursor,按 ts_code,trade_date 升序;日历轴限制)──
def stream_prices(qconn) -> Iterator[tuple]:
    with qconn.cursor(name="mkt_prices_stream") as cur:
        cur.itersize = 100_000
        cur.execute(f"SELECT ts_code, trade_date, close FROM ({SRC}) f "
                    "ORDER BY ts_code, trade_date")
        for row in cur:
            yield row


def view_scan_stats(qconn) -> tuple[int, int, dt.date, dt.date]:
    """返回 (raw_view_rows, input_rows[日历轴限制后], min_date, max_date[input])。"""
    with qconn.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {VIEW}")
        raw = int(cur.fetchone()[0])
        cur.execute(f"SELECT count(*), min(trade_date), max(trade_date) FROM ({SRC}) f")
        inp, mn, mx = cur.fetchone()
    return raw, int(inp), mn, mx


def sql_crosscheck(qconn) -> dict[dt.date, tuple[float, int]]:
    """SQL 独立复算(镜像同一日历轴限制):窗口 lag(日历轴 present 行)=跨缺口起点,
    ln(close/lag)=跨缺口对数收益;等权 avg + count 每交易日。返回 {trade_date: (ret, n)}。"""
    with qconn.cursor() as cur:
        cur.execute(
            "SELECT trade_date, avg(ret), count(ret) FROM ("
            "  SELECT trade_date, ln(close / lag(close) OVER "
            "         (PARTITION BY ts_code ORDER BY trade_date)) AS ret "
            f"  FROM ({SRC}) f) s "
            "WHERE ret IS NOT NULL GROUP BY trade_date ORDER BY trade_date")
        return {d: (float(r), int(n)) for d, r, n in cur.fetchall()}


def compare(py_rows, sql_map) -> tuple[float, int]:
    """逐日比对 Python vs SQL:返回 (max_abs_dret, n_mismatch)。日期集合须一致。"""
    py_map = {d: (r, n) for d, r, n in py_rows}
    if set(py_map) != set(sql_map):
        only_py = sorted(set(py_map) - set(sql_map))[:5]
        only_sql = sorted(set(sql_map) - set(py_map))[:5]
        raise AssertionError(f"双算日期集合不一致 py-only={only_py} sql-only={only_sql}")
    max_dret = 0.0
    n_mismatch = 0
    for d, (r_py, n_py) in py_map.items():
        r_sql, n_sql = sql_map[d]
        max_dret = max(max_dret, abs(r_py - r_sql))
        if n_py != n_sql:
            n_mismatch += 1
    return max_dret, n_mismatch


# ── 落库(append-only:一条 market_batch + COPY market_eqw_return,单事务)──────
def land(tconn, rows, *, source, hypothesis, frozen_digest, holdout, view_rows,
         min_date, max_date, pull_time, note) -> tuple[int, int]:
    with tconn.cursor() as cur:
        cur.execute(
            "INSERT INTO public.market_batch"
            "(source,hypothesis,compounding,frozen_digest,holdout_start,view_rows,"
            " out_rows,min_date,max_date,pull_time,note) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING batch_id",
            (source, hypothesis, COMPOUNDING, frozen_digest, holdout, view_rows,
             len(rows), min_date, max_date, pull_time, note))
        bid = cur.fetchone()[0]
        with cur.copy("COPY public.market_eqw_return(batch_id,trade_date,ret_eqw,n_stocks) "
                      "FROM STDIN") as cp:
            for d, r, n in rows:
                cp.write_row((bid, d, r, n))
    tconn.commit()
    with tconn.cursor() as cur:
        cur.execute("SELECT count(*) FROM public.market_eqw_return WHERE batch_id=%s", (bid,))
        landed = cur.fetchone()[0]
    return bid, int(landed)


def run(dry: bool):
    import psycopg

    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env = load_env(os.path.join(root, ".env"))
    qdsn = env.get("QBASE_APP_DSN")
    tdsn = env.get("TAOSHA_APP_DSN")
    if not qdsn or not tdsn:
        sys.exit("缺 QBASE_APP_DSN / TAOSHA_APP_DSN(.env)")

    pull_time = dt.datetime.now(dt.timezone.utc)
    digest = audit_digest()
    holdout = HOLDOUT_START            # date(2024,7,1)

    with psycopg.connect(qdsn) as qconn:
        raw_rows, input_rows, v_min, v_max = view_scan_stats(qconn)
        off_cal = raw_rows - input_rows
        print(f"视图 {VIEW}: raw={raw_rows} 日历轴input={input_rows}"
              f"(off-calendar剔除={off_cal}) range={v_min}..{v_max}", flush=True)
        print("Python(冻结 returns.py)逐票聚合中…", flush=True)
        py_rows = compute_market_eqw(stream_prices(qconn))
        print(f"  → 收益日 {len(py_rows)} 天", flush=True)
        print("SQL 窗口独立复算中…", flush=True)
        sql_map = sql_crosscheck(qconn)

    # ── 双算闸 ──
    max_dret, n_mismatch = compare(py_rows, sql_map)
    print(f"双算闸: max|Δret|={max_dret:.3e}  n_stocks 不一致日数={n_mismatch}", flush=True)
    if max_dret >= CROSSCHECK_TOL or n_mismatch != 0:
        sys.exit(f"✗ 双算闸不过(tol={CROSSCHECK_TOL:.0e}):中止不落库")

    # ── 硬闸(holdout 泄漏)──
    out_rows = len(py_rows)
    min_date = py_rows[0][0]
    max_date = py_rows[-1][0]
    n_stocks_min = min(n for _, _, n in py_rows)
    n_stocks_max = max(n for _, _, n in py_rows)
    print(f"落库口径: out_rows={out_rows}  日期 {min_date}..{max_date}  "
          f"n_stocks∈[{n_stocks_min},{n_stocks_max}]", flush=True)
    if max_date >= holdout:
        sys.exit(f"✗ holdout 泄漏: max_date={max_date} >= {holdout}:中止")
    if out_rows >= FULL_CALENDAR_TRADING_DAYS:
        sys.exit(f"✗ holdout 泄漏疑似: out_rows={out_rows} 触及全日历 {FULL_CALENDAR_TRADING_DAYS}:中止")

    note = (f"全市场等权对数日收益;收益核=冻结 returns.py(multi_day/Close);轴=日历(约束②:"
            f"prices∩calendar,off-calendar剔除={off_cal}行=早年非交易日周日bar);"
            f"分母=当日有present bar且有前序present bar的票(停牌缺行不进);"
            f"双算闸 max|Δret|={max_dret:.2e}/n_stocks全等;"
            f"raw_view={raw_rows}/日历轴input={input_rows};n_stocks∈[{n_stocks_min},{n_stocks_max}]")

    if dry:
        print("--dry:双算闸+硬闸均过,不落库。", flush=True)
        return

    with psycopg.connect(tdsn) as tconn:
        bid, landed = land(
            tconn, py_rows, source=f"qbase:{VIEW}∩explore_reader_calendar", hypothesis="market",
            frozen_digest=digest, holdout=holdout, view_rows=raw_rows,
            min_date=min_date, max_date=max_date, pull_time=pull_time, note=note)
    if landed != out_rows:
        sys.exit(f"✗ 回读行数 {landed} ≠ 预算 {out_rows}")
    print(f"✓ 落库 batch={bid} 行数={landed}(frozen_digest={digest[:12]}…)", flush=True)


# ── 纯核脱库自检(手算对照)────────────────────────────────────────────────────
def selftest():
    D = dt.date
    # 两票、含停牌缺行(A 在 d3 停牌=无 d3 行);d1=各自首 bar 无前序→不进。
    #  A: d1=10, d2=11, (d3 缺), d4=13, d5=14
    #  B: d1=20, d2=22, d3=21, d4=24  (d5 无行)
    rows = [
        ("A", D(2020, 1, 1), 10.0), ("A", D(2020, 1, 2), 11.0),
        ("A", D(2020, 1, 4), 13.0), ("A", D(2020, 1, 5), 14.0),
        ("B", D(2020, 1, 1), 20.0), ("B", D(2020, 1, 2), 22.0),
        ("B", D(2020, 1, 3), 21.0), ("B", D(2020, 1, 4), 24.0),
    ]
    got = {d: (r, n) for d, r, n in compute_market_eqw(rows)}
    ln = math.log
    # 手算到达日聚合:
    #  d2: A=ln(11/10), B=ln(22/20)          → n=2
    #  d3: B=ln(21/22)                        → n=1 (A 停牌缺行不进)
    #  d4: A=ln(13/11)跨缺口落恢复日, B=ln(24/21) → n=2
    #  d5: A=ln(14/13)                        → n=1
    #  d1: 无(各自首 bar)
    exp = {
        D(2020, 1, 2): ((ln(11 / 10) + ln(22 / 20)) / 2, 2),
        D(2020, 1, 3): (ln(21 / 22), 1),
        D(2020, 1, 4): ((ln(13 / 11) + ln(24 / 21)) / 2, 2),
        D(2020, 1, 5): (ln(14 / 13), 1),
    }
    assert set(got) == set(exp), (sorted(got), sorted(exp))
    for d in exp:
        assert got[d][1] == exp[d][1], (d, "n", got[d], exp[d])
        assert abs(got[d][0] - exp[d][0]) < 1e-15, (d, "ret", got[d], exp[d])
    assert D(2020, 1, 1) not in got, "首 bar 日不应有收益(无前序价)"
    # 乱序输入护栏
    try:
        compute_market_eqw([("A", D(2020, 1, 2), 11.0), ("A", D(2020, 1, 1), 10.0)])
        raise SystemExit("护栏未触发(应拒未排序输入)")
    except ValueError:
        pass
    print("seed_market_return 纯核自检 OK:跨缺口落恢复日 / 停牌缺行不进分母 / 首bar无收益 / 排序护栏")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="纯核手算自检(不碰库)")
    ap.add_argument("--dry", action="store_true", help="连库双算闸+硬闸,不落库")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    run(dry=args.dry)


if __name__ == "__main__":
    main()
