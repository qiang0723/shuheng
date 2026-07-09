#!/usr/bin/env python3
"""淘沙 L2 · b1 池等权日收益 PIT 活基准预计算落库(切片3 #2b·步②;004 建表)。

读 qbase 归一视图 explore_reader_prices(∩calendar,继承 holdout+.BJ排除+后复权)+ taosha
pool_b1_current(当日池快照成员)→ 复用**冻结收益核** compute/returns.py 逐票算跨缺口对数收益,
**按当日池快照成员门控**等权聚合成 b1 池等权日收益序列,append-only 落 taosha
pool_b1_return_batch + pool_b1_return(004)。

口径(与 004 表注逐字对应,骗不了人):
  ret_pool_eqw[d] = 当日池快照成员(pool_b1_current 于 d)中【有 present bar 且有前序 present bar】的票
    log(close_d/close_前序present) 的等权平均。收益核=冻结 returns.py(multi_day/Close,跨缺口落恢复日)。
  n_pool_stocks[d] = 分母 = 上述票数(⊆当日池快照;停牌缺行不进;池空/无有效收益→该日无行)。
  轴=日历(约束②):源=explore_reader_prices JOIN explore_reader_calendar;宇宙限池全期并集(非池票零贡献)。

**基准成分逐日=当日池快照**(步②预置①):门控集合=pool_b1_current[到达日 d](PIT,d=收益实现日)。

双算闸(骗不了人):Python(冻结 returns.py,Path A)=落库权威;SQL 窗口 ln(close/lag)(Path B)独立复算;
  两路均按同一 membership 门控,逐日 |Δret|<1e-9 且 n_pool_stocks 整数全等,否则**中止不落库**。
硬闸(holdout 泄漏):max(trade_date) < 2024-07-01,否则中止。
验收硬项(--verify,步②预置①):落库后任抽 K 日,从 pool_b1_current[d] 独立重算 ret 与库值逐日 <1e-9,
  且门控成分集合==当日池快照(重算直接以 pool_b1_current[d] 成员为准 → ret 吻合即证库值用的就是当日快照)。

红线(taosha CLAUDE.md §2):不 import 兄弟目录;价源=qbase 视图(经 DSN,非 import)。
  读=QBASE_APP_DSN(价视图)+ TAOSHA_APP_DSN(池成员);写=TAOSHA_APP_DSN(只 INSERT,触发器焊 append-only)。
  秘钥纪律:DSN 只从 .env 读,不落日志、不回显、不进 git。
用法:
  python -m taosha.ingest.seed_pool_b1_return --selftest   # 纯核手算自检(不碰库)
  python -m taosha.ingest.seed_pool_b1_return --dry        # 连库+双算闸+硬闸,不落库
  python -m taosha.ingest.seed_pool_b1_return              # 全量预算+落库
  python -m taosha.ingest.seed_pool_b1_return --verify     # 落库后验收硬项(抽日成分==当日池快照)
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
CROSSCHECK_TOL = 1e-9
VERIFY_TOL = 1e-9
VERIFY_SAMPLE = 12          # 验收硬项抽样日数(确定性均匀抽 + 端点)


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


# ── 纯核:逐票冻结收益核 → **当日池快照门控**等权聚合(可脱库自检)────────────────
def compute_pool_eqw(rows: Iterable[tuple],
                     pool_by_date: dict) -> list[tuple[dt.date, float, int]]:
    """rows: (ts_code, trade_date, close) 迭代器,**须按 (ts_code, trade_date) 升序**。
    pool_by_date: {trade_date: set/frozenset(ts_code)} = 当日池快照(pool_b1_current)。
    返回 [(trade_date, ret_pool_eqw, n_pool_stocks), ...] 按 trade_date 升序。

    逐票 close 序列 → log_rates_from_prices(冻结核);rate[j] 到达日=dates[j+1](跨缺口落恢复日);
    **门控**:仅当 ts_code ∈ pool_by_date[到达日] 才计入该到达日等权(基准成分=当日池快照)。
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
        for j, r in enumerate(rates):
            if r is None:
                continue
            d = dates[j + 1]
            members = pool_by_date.get(d)
            if members is None or cur_code not in members:
                continue                       # 门控:到达日非当日池快照成员 → 不计入
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
        if prev_date_in_code is not None and trade_date <= prev_date_in_code:
            raise ValueError(f"输入未按 (ts_code,trade_date) 升序: {ts_code} {prev_date_in_code}->{trade_date}")
        prev_date_in_code = trade_date
        dates.append(trade_date)
        closes.append(None if close is None else float(close))
    flush()
    return [(d, acc[d] / cnt[d], cnt[d]) for d in sorted(acc)]


# 源=prices ∩ calendar(约束②)、限池全期并集(universe,非池票零贡献故不拉)
def _src(universe_param: str) -> str:
    return (f"SELECT p.ts_code, p.trade_date, p.close FROM {VIEW} p "
            "JOIN explore_reader_calendar c USING (trade_date) "
            f"WHERE p.ts_code = ANY({universe_param})")


def load_pool_snapshots(conn, pool_batch: Optional[int] = None,
                        view: str = "pool_b1_membership") -> dict:
    """当日池快照 {trade_date: frozenset(ts_code)}。
    落库侧(taosha_app):读 pool_b1_membership WHERE batch_id=pool_batch(=pool_b1_current 同集,
      taosha_app 有 SELECT、不读 view 免扩权);验收侧(taosha_engine):view='pool_b1_current'(引擎视角)。"""
    by_date: dict = {}
    if view == "pool_b1_current":
        sql, params = "SELECT trade_date, ts_code FROM pool_b1_current", ()
    else:
        sql = "SELECT trade_date, ts_code FROM pool_b1_membership WHERE batch_id=%s"
        params = (pool_batch,)
    with conn.cursor(name="pool_snap_stream") as cur:
        cur.itersize = 200_000
        cur.execute(sql, params)
        for d, ts in cur:
            by_date.setdefault(d, set()).add(ts)
    return {d: frozenset(s) for d, s in by_date.items()}


def stream_prices(qconn, universe: list) -> Iterator[tuple]:
    with qconn.cursor(name="pool_prices_stream") as cur:
        cur.itersize = 100_000
        cur.execute(f"SELECT ts_code, trade_date, close FROM ({_src('%s')}) f "
                    "ORDER BY ts_code, trade_date", (universe,))
        for row in cur:
            yield row


def view_scan_stats(qconn, universe: list) -> tuple[int, dt.date, dt.date]:
    with qconn.cursor() as cur:
        cur.execute(f"SELECT count(*), min(trade_date), max(trade_date) FROM ({_src('%s')}) f",
                    (universe,))
        n, mn, mx = cur.fetchone()
    return int(n), mn, mx


def sql_crosscheck_pool(qconn, universe: list, pool_by_date: dict) -> dict:
    """Path B(独立):SQL 窗口 ln(close/lag) 逐票收益,流式**按当日池快照门控**等权聚合(Python)。
    返回 {trade_date: (ret, n)}。与 Path A 同 membership 门控 → 双算校验的是收益核(非门控)。"""
    acc: dict = {}
    cnt: dict = {}
    with qconn.cursor(name="pool_sql_stream") as cur:
        cur.itersize = 100_000
        cur.execute(
            "SELECT ts_code, trade_date, "
            "  ln(close / lag(close) OVER (PARTITION BY ts_code ORDER BY trade_date)) AS ret "
            f"FROM ({_src('%s')}) f ORDER BY ts_code, trade_date", (universe,))
        for ts, d, ret in cur:
            if ret is None:
                continue
            members = pool_by_date.get(d)
            if members is None or ts not in members:
                continue
            acc[d] = acc.get(d, 0.0) + float(ret)
            cnt[d] = cnt.get(d, 0) + 1
    return {d: (acc[d] / cnt[d], cnt[d]) for d in acc}


def compare(py_rows, sql_map) -> tuple[float, int]:
    py_map = {d: (r, n) for d, r, n in py_rows}
    if set(py_map) != set(sql_map):
        only_py = sorted(set(py_map) - set(sql_map))[:5]
        only_sql = sorted(set(sql_map) - set(py_map))[:5]
        raise AssertionError(f"双算日期集合不一致 py-only={only_py} sql-only={only_sql}")
    max_dret, n_mismatch = 0.0, 0
    for d, (r_py, n_py) in py_map.items():
        r_sql, n_sql = sql_map[d]
        max_dret = max(max_dret, abs(r_py - r_sql))
        if n_py != n_sql:
            n_mismatch += 1
    return max_dret, n_mismatch


def land(tconn, rows, *, source, pool_batch_id, frozen_digest, holdout, view_rows,
         min_date, max_date, avg_n, pull_time, note) -> tuple[int, int]:
    with tconn.cursor() as cur:
        cur.execute(
            "INSERT INTO public.pool_b1_return_batch"
            "(source,pool_batch_id,compounding,frozen_digest,holdout_start,view_rows,"
            " out_rows,min_date,max_date,avg_n_stocks,pull_time,note) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING batch_id",
            (source, pool_batch_id, COMPOUNDING, frozen_digest, holdout, view_rows,
             len(rows), min_date, max_date, avg_n, pull_time, note))
        bid = cur.fetchone()[0]
        with cur.copy("COPY public.pool_b1_return(batch_id,trade_date,ret_pool_eqw,n_pool_stocks) "
                      "FROM STDIN") as cp:
            for d, r, n in rows:
                cp.write_row((bid, d, r, n))
    tconn.commit()
    with tconn.cursor() as cur:
        cur.execute("SELECT count(*) FROM public.pool_b1_return WHERE batch_id=%s", (bid,))
        landed = cur.fetchone()[0]
    return bid, int(landed)


def _pool_batch_id(tconn) -> int:
    with tconn.cursor() as cur:
        cur.execute("SELECT max(batch_id) FROM public.pool_b1_batch")
        r = cur.fetchone()[0]
    if r is None:
        sys.exit("✗ pool_b1_batch 空:先跑 seed_pool_b1(003)")
    return int(r)


def run(dry: bool):
    import psycopg
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env = load_env(os.path.join(root, ".env"))
    qdsn, tdsn = env.get("QBASE_APP_DSN"), env.get("TAOSHA_APP_DSN")
    if not qdsn or not tdsn:
        sys.exit("缺 QBASE_APP_DSN / TAOSHA_APP_DSN(.env)")

    pull_time = dt.datetime.now(dt.timezone.utc)
    digest = audit_digest()
    holdout = HOLDOUT_START

    with psycopg.connect(tdsn) as tconn:
        pool_batch = _pool_batch_id(tconn)
        print(f"当日池快照:pool_b1_membership(batch={pool_batch}=pool_b1_current 同集)加载中…", flush=True)
        pool_by_date = load_pool_snapshots(tconn, pool_batch=pool_batch)
    universe = sorted({ts for s in pool_by_date.values() for ts in s})
    print(f"  评估日 {len(pool_by_date)} 天,池宇宙(全期并集)={len(universe)} 票", flush=True)

    with psycopg.connect(qdsn) as qconn:
        view_rows, v_min, v_max = view_scan_stats(qconn, universe)
        print(f"价视图(池宇宙∩calendar): rows={view_rows} range={v_min}..{v_max}", flush=True)
        print("Path A(冻结 returns.py)逐票门控聚合中…", flush=True)
        py_rows = compute_pool_eqw(stream_prices(qconn, universe), pool_by_date)
        print(f"  → 池等权收益日 {len(py_rows)} 天", flush=True)
        print("Path B(SQL 窗口)独立复算中…", flush=True)
        sql_map = sql_crosscheck_pool(qconn, universe, pool_by_date)

    # 双算闸
    max_dret, n_mismatch = compare(py_rows, sql_map)
    print(f"双算闸: max|Δret|={max_dret:.3e}  n_pool_stocks 不一致日数={n_mismatch}", flush=True)
    if max_dret >= CROSSCHECK_TOL or n_mismatch != 0:
        sys.exit(f"✗ 双算闸不过(tol={CROSSCHECK_TOL:.0e}):中止不落库")

    # 硬闸
    out_rows = len(py_rows)
    min_date, max_date = py_rows[0][0], py_rows[-1][0]
    n_min = min(n for _, _, n in py_rows)
    n_max = max(n for _, _, n in py_rows)
    avg_n = sum(n for _, _, n in py_rows) / out_rows
    print(f"落库口径: out_rows={out_rows} 日期 {min_date}..{max_date} "
          f"n_pool_stocks∈[{n_min},{n_max}] 均{avg_n:.1f}", flush=True)
    if max_date >= holdout:
        sys.exit(f"✗ holdout 泄漏: max_date={max_date} >= {holdout}:中止")

    note = (f"b1 池等权对数日收益 PIT 活基准;基准成分逐日=当日池快照(pool_b1_batch={pool_batch});"
            f"收益核=冻结 returns.py(multi_day/Close 跨缺口);轴=日历(约束② prices∩calendar);"
            f"双算闸 max|Δret|={max_dret:.2e}/n全等;view_rows={view_rows};"
            f"n_pool_stocks∈[{n_min},{n_max}]均{avg_n:.1f}")

    if dry:
        print("--dry:双算闸+硬闸均过,不落库。", flush=True)
        return

    with psycopg.connect(tdsn) as tconn:
        bid, landed = land(
            tconn, py_rows, source=f"qbase:{VIEW}∩calendar × taosha:pool_b1_current",
            pool_batch_id=pool_batch, frozen_digest=digest, holdout=holdout, view_rows=view_rows,
            min_date=min_date, max_date=max_date, avg_n=avg_n, pull_time=pull_time, note=note)
    if landed != out_rows:
        sys.exit(f"✗ 回读行数 {landed} ≠ 预算 {out_rows}")
    print(f"✓ 落库 batch={bid} 行数={landed}(frozen_digest={digest[:12]}…,pool_batch={pool_batch})",
          flush=True)


def verify():
    """验收硬项(步②预置①):落库后任抽 K 日,从 pool_b1_current[d] 独立重算 ret 与库值逐日 <1e-9;
    重算直接以当日池快照成员为门控 → ret 吻合即证库值基准成分==当日池快照(骗不了人)。"""
    import psycopg
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env = load_env(os.path.join(root, ".env"))
    # 引擎视角(taosha_engine):读引擎自己看到的 pool_b1_current(池快照)+ pool_b1_return_current(基准)
    #   + qbase explore_reader 价视图 → 验的是"引擎读到的基准==引擎读到的当日池快照等权",最铁。
    qdsn = env.get("TAOSHA_ENGINE_QBASE_DSN")
    tdsn = env.get("TAOSHA_ENGINE_TAOSHA_DSN")
    if not qdsn or not tdsn:
        sys.exit("缺 TAOSHA_ENGINE_QBASE_DSN / TAOSHA_ENGINE_TAOSHA_DSN(.env);验收硬项走引擎只读身份")

    with psycopg.connect(tdsn) as tconn:
        pool_by_date = load_pool_snapshots(tconn, view="pool_b1_current")   # 引擎视角池快照
        with tconn.cursor() as cur:
            cur.execute("SELECT trade_date, ret_pool_eqw, n_pool_stocks FROM pool_b1_return_current "
                        "ORDER BY trade_date")
            landed = cur.fetchall()
    if not landed:
        sys.exit("✗ pool_b1_return_current 空:先落库")
    dates = [r[0] for r in landed]
    lib = {d: (float(r), int(n)) for d, r, n in landed}
    # 确定性均匀抽样 + 端点(不用随机,可复现)
    k = min(VERIFY_SAMPLE, len(dates))
    idxs = sorted(set([0, len(dates) - 1] + [round(i * (len(dates) - 1) / (k - 1)) for i in range(k)]))
    sample_dates = [dates[i] for i in idxs]

    print(f"验收硬项:抽 {len(sample_dates)} 日,从 pool_b1_current 独立重算(成分==当日池快照)…", flush=True)
    max_dret, n_mismatch, n_setmiss = 0.0, 0, 0
    with psycopg.connect(qdsn) as qconn:
        for d in sample_dates:
            members = sorted(pool_by_date.get(d, frozenset()))
            # 独立重算:该日池快照成员在 <= d 的 close 序列 → 各自 d 当日收益(跨缺口对前一 present)
            with qconn.cursor() as cur:
                cur.execute(
                    f"SELECT ts_code, trade_date, close FROM ({_src('%s')}) f "
                    "WHERE trade_date <= %s ORDER BY ts_code, trade_date", (members, d))
                by_ts: dict = {}
                for ts, td, close in cur.fetchall():
                    by_ts.setdefault(ts, []).append((td, close))
            rets, used = [], set()
            for ts, seq in by_ts.items():
                # seq 升序;取 d 当日 close 与前一 present close
                if seq[-1][0] != d or seq[-1][1] is None:
                    continue                   # d 当日无 present bar → 不进(停牌)
                prev = None
                for td, c in seq[:-1][::-1]:
                    if c is not None:
                        prev = c
                        break
                if prev is None or prev <= 0:
                    continue                   # 无前序 present(IPO/长停)→ 不进
                rets.append(math.log(seq[-1][1] / prev))
                used.add(ts)
            ret_chk = (sum(rets) / len(rets)) if rets else None
            ret_lib, n_lib = lib[d]
            # 成分核对:重算门控用的就是 pool_by_date[d](当日池快照)→ used ⊆ members;n 应等库值
            if not set(used).issubset(set(members)):
                n_setmiss += 1
            if ret_chk is None or len(rets) != n_lib:
                n_mismatch += 1
                print(f"  ✗ {d}: 重算 n={len(rets)} vs 库 n={n_lib} 池快照={len(members)}", flush=True)
                continue
            dd = abs(ret_chk - ret_lib)
            max_dret = max(max_dret, dd)
            flag = "✓" if dd < VERIFY_TOL else "✗"
            print(f"  {flag} {d}: 池快照={len(members)} 有效分母={n_lib} "
                  f"ret 重算={ret_chk:.9f} 库={ret_lib:.9f} Δ={dd:.2e}", flush=True)
            if dd >= VERIFY_TOL:
                n_mismatch += 1
    if n_mismatch or n_setmiss or max_dret >= VERIFY_TOL:
        sys.exit(f"✗ 验收硬项不过:max|Δ|={max_dret:.2e} n_mismatch={n_mismatch} 成分越界={n_setmiss}")
    print(f"✅ 验收硬项通过:{len(sample_dates)} 日 max|Δ|={max_dret:.2e}<{VERIFY_TOL:.0e}、"
          f"成分逐日==当日池快照(pool_b1_current)、有效分母全等", flush=True)


def selftest():
    D = dt.date
    # 池快照(当日成员):d2 池={A,B}、d3 池={B}、d4 池={A}(测门控:非成员当日收益不计入)
    pool_by_date = {
        D(2020, 1, 2): frozenset({"A", "B"}),
        D(2020, 1, 3): frozenset({"B"}),
        D(2020, 1, 4): frozenset({"A"}),           # d4 只 A 在池(B 的 d4 收益不计入)
        D(2020, 1, 5): frozenset({"A", "B"}),
    }
    rows = [
        ("A", D(2020, 1, 1), 10.0), ("A", D(2020, 1, 2), 11.0),
        ("A", D(2020, 1, 4), 13.0), ("A", D(2020, 1, 5), 14.0),   # A 缺 d3(停牌)→ d4 跨缺口
        ("B", D(2020, 1, 1), 20.0), ("B", D(2020, 1, 2), 22.0),
        ("B", D(2020, 1, 3), 21.0), ("B", D(2020, 1, 4), 24.0),   # B 无 d5 行
    ]
    got = {d: (r, n) for d, r, n in compute_pool_eqw(rows, pool_by_date)}
    ln = math.log
    # 手算门控聚合:
    #  d2: 池{A,B}: A=ln(11/10),B=ln(22/20) → n=2
    #  d3: 池{B}:   B=ln(21/22)             → n=1(A 停牌缺行本就无 d3 收益)
    #  d4: 池{A}:   A=ln(13/11)跨缺口落 d4   → n=1(B 的 d4=ln(24/21) 因 B 不在 d4 池 → 不计入)
    #  d5: 池{A,B}: A=ln(14/13);B 无 d5 行  → n=1
    exp = {
        D(2020, 1, 2): ((ln(11 / 10) + ln(22 / 20)) / 2, 2),
        D(2020, 1, 3): (ln(21 / 22), 1),
        D(2020, 1, 4): (ln(13 / 11), 1),
        D(2020, 1, 5): (ln(14 / 13), 1),
    }
    assert set(got) == set(exp), (sorted(got), sorted(exp))
    for d in exp:
        assert got[d][1] == exp[d][1], (d, "n", got[d], exp[d])
        assert abs(got[d][0] - exp[d][0]) < 1e-15, (d, "ret", got[d], exp[d])
    assert D(2020, 1, 1) not in got, "首 bar 日无收益"
    # 门控核心:d4 若不门控会含 B → n=2;门控后 n=1、值=纯 A(证成分=当日池快照)
    assert got[D(2020, 1, 4)][1] == 1 and abs(got[D(2020, 1, 4)][0] - ln(13 / 11)) < 1e-15, "门控:非成员不计入"
    # 排序护栏
    try:
        compute_pool_eqw([("A", D(2020, 1, 2), 11.0), ("A", D(2020, 1, 1), 10.0)], pool_by_date)
        raise SystemExit("护栏未触发")
    except ValueError:
        pass
    print("seed_pool_b1_return 纯核自检 OK:当日池快照门控(非成员当日收益不计入)/ 跨缺口落恢复日 / "
          "停牌缺行不进 / 首bar无收益 / 排序护栏")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--verify", action="store_true", help="落库后验收硬项(抽日成分==当日池快照)")
    args = ap.parse_args()
    if args.selftest:
        selftest()
    elif args.verify:
        verify()
    else:
        run(dry=args.dry)


if __name__ == "__main__":
    main()
