"""淘沙 L2 · b1 全市场流动性池成员 PIT 预计算落库(切片3 #2b;003 承载表)。

读 qbase `bar_daily_snap.amount`(非 .BJ、holdout<2024-07-01)+ `entity_master.list_date`
+ `explore_reader_calendar_snap`(交易日轴)→ 按 compute.liquidity_pool 口径逐评估日算 b1 池成员
(trailing-20d 成交额均值 PIT 排名、上市满120交易日宇宙、前20%)→ 写 taosha `pool_b1_membership`
(单事务 COPY,append-only)。

修法#3 窄补(2026-07-13)——seed 绑定已发布快照: 底表批次经 study_snap_batch('daily'/'stock_basic')
钉死到 GUC 指定的已发布 manifest(权威镜像+attestation fail-closed),日历轴走 *_snap 视图;
source_anchor={所读快照 qbase 向量, source_manifest{snapshot_id,digest}}。
~~旧模式 max(batch_id) 现值路由~~ 作废(先记锚后读 current 的血缘窗口已消除)。

口径一致:滚动 trailing 均值(O(1)/日,内存友好)自检对齐 liquidity_pool.trailing_mean_amount。
秘钥:读 QBASE_APP_DSN、写 TAOSHA_APP_DSN,只从 .env,不回显。用法(aliyun,属主已建 003):
  set -a; . /opt/quant/.env; set +a
  /opt/venvs/qbase-ingest/bin/python -m taosha.ingest.seed_pool_b1 --source-snapshot-id N [--dry]
"""
from __future__ import annotations

import argparse
import bisect
import datetime as dt
import math
import os

import psycopg

from taosha.compute import liquidity_pool as lp

HOLDOUT = dt.date(2024, 7, 1)


def _env(k):
    v = os.environ.get(k)
    if v:
        return v
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for line in open(os.path.join(root, ".env")):
        line = line.strip()
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError(f"缺 {k}")


def _rolling_trailing_mean(amounts, window):
    """滚动 trailing-window 非空均值(PIT,O(n))。返回与 amounts 等长数组,不足窗前段照非空均值。
    对齐 liquidity_pool.trailing_mean_amount:窗内非空 amount 的算术均值;全空→None。"""
    n = len(amounts)
    out = [None] * n
    s = 0.0
    cnt = 0
    for i in range(n):
        a = amounts[i]
        if a is not None:
            s += a
            cnt += 1
        drop = i - window
        if drop >= 0 and amounts[drop] is not None:
            s -= amounts[drop]
            cnt -= 1
        out[i] = (s / cnt) if cnt > 0 else None
    return out


def run(source_snapshot_id: int, dry: bool = False):
    from psycopg.types.json import Json

    from taosha.experiment import snapshot

    qdsn, tdsn = _env("QBASE_APP_DSN"), _env("TAOSHA_APP_DSN")
    q = psycopg.connect(qdsn)
    qc = q.cursor()

    # 修法#3 窄补: 绑定已发布快照——锚=所读快照向量;读径批次=study_snap_batch(GUC 路由,
    # 权威镜像+attestation fail-closed);~~current/max 现值锚~~作废。
    qc.execute("SELECT set_config('shuheng.study_snapshot_id', %s, false)",
               (str(source_snapshot_id),))
    snap_content, snap_digest = snapshot.read_published_snapshot(qc, source_snapshot_id)
    anchor = {"qbase": snap_content["qbase"],
              "source_manifest": {"snapshot_id": source_snapshot_id, "digest": snap_digest}}
    print(f"源快照绑定: snapshot_id={source_snapshot_id} digest={snap_digest[:12]}…"
          f"(已发布,批次=study_snap_batch 路由)", flush=True)

    # 交易日轴(explore_reader_calendar_snap:SSE 交易日,holdout 焊死,manifest 路由)
    qc.execute("SELECT trade_date FROM explore_reader_calendar_snap ORDER BY trade_date")
    cal = [r[0] for r in qc.fetchall()]
    cal_idx = {d: i for i, d in enumerate(cal)}
    n = len(cal)
    print(f"交易日轴 {n} 日 [{cal[0]}..{cal[-1]}]", flush=True)

    # list_date → 轴索引(上市首个交易日:cal 中首个 ≥ list_date;批次=快照钉死)
    qc.execute("""SELECT ts_code, list_date FROM entity_master
                  WHERE batch_id = public.study_snap_batch('stock_basic')
                    AND ts_code !~ '\\.BJ$'""")
    list_idx = {}
    for ts, ld in qc.fetchall():
        if ld is None:
            list_idx[ts] = None
        else:
            p = bisect.bisect_left(cal, ld)
            list_idx[ts] = p if p < n else None

    # amount 按 sec 密集展开到轴(非 .BJ、holdout;daily 批次=快照钉死);停牌/无行=None
    print("加载 amount(全市场)...", flush=True)
    amt = {}
    qc.execute("""SELECT ts_code, trade_date, amount FROM bar_daily_snap
                  WHERE batch_id = public.study_snap_batch('daily')
                    AND ts_code !~ '\\.BJ$' AND trade_date < %s""", (HOLDOUT,))
    rows = 0
    for ts, td, amount in qc:
        j = cal_idx.get(td)
        if j is None:
            continue                          # off-calendar bar(早年周日噪声,视图轴排除)
        a = amt.get(ts)
        if a is None:
            a = [None] * n
            amt[ts] = a
        a[j] = float(amount) if amount is not None else None
        rows += 1
    q.close()
    print(f"amount 行 {rows}、票 {len(amt)}", flush=True)

    # 滚动 trailing-20d 均值(口径一致自检:抽一票对齐 liquidity_pool)
    tmean = {ts: _rolling_trailing_mean(a, lp.AMOUNT_WINDOW) for ts, a in amt.items()}
    _ts0 = next(iter(amt))
    for _i in (200, 1000, 5000):
        if _i < n:
            ref = lp.trailing_mean_amount(amt[_ts0], _i, lp.AMOUNT_WINDOW)
            got = tmean[_ts0][_i]
            assert (ref is None and got is None) or (ref is not None and abs(ref - got) < 1e-6), \
                f"滚动均值口径不一致 @ {_i}: {ref} vs {got}"
    print("滚动 trailing 均值口径对齐 liquidity_pool ✓", flush=True)

    # 逐评估日 top20%(上市满120交易日宇宙 + trailing 均值降序)
    print("逐评估日算池成员...", flush=True)
    members = []          # (trade_date, ts_code)
    pool_sizes = []
    all_ts = list(amt.keys())
    for i in range(n):
        ranked = []
        for ts in all_ts:
            li = list_idx.get(ts)
            if li is None or (i - li + 1) < lp.LISTING_MIN_DAYS:
                continue
            m = tmean[ts][i]
            if m is None:
                continue
            ranked.append((ts, m))
        if not ranked:
            continue
        ranked.sort(key=lambda x: (-x[1], x[0]))
        k = math.ceil(lp.TOP_FRACTION * len(ranked))
        pool_sizes.append(k)
        d = cal[i]
        for ts, _ in ranked[:k]:
            members.append((d, ts))
        if i % 1000 == 0:
            print(f"  日 {i}/{n} {d} 池 {k}", flush=True)
    n_dates = len(pool_sizes)
    avg_pool = (sum(pool_sizes) / n_dates) if n_dates else 0.0
    min_d = min(d for d, _ in members) if members else cal[0]
    max_d = max(d for d, _ in members) if members else cal[0]
    assert max_d < HOLDOUT, f"holdout 泄漏:{max_d}"
    print(f"池成员 {len(members)} 行、覆盖 {n_dates} 评估日、平均池 {avg_pool:.1f}、[{min_d}..{max_d}]", flush=True)

    if dry:
        print("--dry:快照钉死读径+全量预算完成,不落库。", flush=True)
        return

    # 写 taosha(单事务:建 batch + COPY 成员)
    t = psycopg.connect(tdsn)
    try:
        with t.cursor() as tc:
            tc.execute(
                "INSERT INTO pool_b1_batch (source, frozen_digest, amount_window, listing_min, "
                " top_fraction, holdout_start, min_date, max_date, n_dates, out_rows, avg_pool_size, "
                " pull_time, note, source_anchor) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, now(), %s, %s) "
                "RETURNING batch_id",
                (f"qbase:bar_daily_snap.amount(非.BJ)@snapshot{source_snapshot_id}",
                 lp.audit_digest(), lp.AMOUNT_WINDOW,
                 lp.LISTING_MIN_DAYS, lp.TOP_FRACTION, HOLDOUT, min_d, max_d, n_dates, len(members),
                 avg_pool, f"b1池PIT预计算:trailing-{lp.AMOUNT_WINDOW}d成交额均值降序前{int(lp.TOP_FRACTION*100)}%、"
                 f"上市满{lp.LISTING_MIN_DAYS}交易日、非.BJ、评估日<{HOLDOUT}", Json(anchor)))
            batch_id = tc.fetchone()[0]
            with tc.copy("COPY pool_b1_membership (batch_id, trade_date, ts_code) FROM STDIN") as cp:
                for d, ts in members:
                    cp.write_row((batch_id, d, ts))
        t.commit()
        print(f"✅ batch_id={batch_id} 入库 {len(members)} 行(单事务 COPY;append-only)", flush=True)
    finally:
        t.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-snapshot-id", type=int, default=None,
                    help="修法#3 窄补: 绑定的已发布 StudySnapshot ID(锚+读径同源,必填)")
    ap.add_argument("--dry", action="store_true", help="快照钉死读径+全量预算,不落库")
    a = ap.parse_args()
    if a.source_snapshot_id is None:
        raise SystemExit("修法#3(窄补): 须 --source-snapshot-id 绑定已发布快照(禁 current/max 现值为锚,fail-closed)")
    run(source_snapshot_id=a.source_snapshot_id, dry=a.dry)
