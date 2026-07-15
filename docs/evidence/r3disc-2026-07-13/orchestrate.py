#!/usr/bin/env python3
"""判别力并发补测编排(第三轮窄补·外部复核回件令,2026-07-13)。

隔离验证环境专用(qbase_iso / taosha_iso;生产库、生产代码零触碰):
  Run1: seed_market_return   --source-snapshot-id 38 运行期间,并发提交水印 trade_cal 批 W1
  Run2: seed_pool_b1_return  --source-snapshot-id 38 运行期间,并发提交水印 trade_cal 批 W2

水印 = 批8 全量拷贝、仅 5 行 is_open 翻转(内容可区分,且若被误读必然改变 seed 产出):
  翻关(1→0): 2000-01-04 / 2015-06-15 / 2023-06-15(三日在 market_eqw_return 与 pool_b1_return 均有行)
  翻开(0→1): 1992-10-04 / 1993-01-03(两日在钉批价视图有真实 bar——误读则新增产出行)

证据(写 /root/r3disc/evidence.json):
  ① 产出内容逐行来自批8:全量 EXCEPT 0/0 + 翻关探针日行在且值全等 + 翻开探针日行缺
  ② source_anchor.qbase.trade_cal = 8(且 source_manifest.snapshot_id=38),≠ 水印批
  ③ 水印 commit 时间戳落 seed 运行窗内,且先于 seed 的 SQL 独立复算相位(该相位全程读于水印之后)
  ④ 对照:批9/10 vs 批8 内容 EXCEPT 0/0(旧并发测试无判别力的实录)+ 水印批 vs 批8 EXCEPT 5/5
  ⑤ 反事实通路:max 批次路由下探针日可见水印内容(若 seed 读 current/max 必消费水印)
  ⑥ 生产零触碰:生产 qbase trade_cal 批次清单、生产 taosha 批次表 max、/opt/quant git 干净
"""
import datetime
import json
import os
import subprocess
import threading

import psycopg

ROOT = "/root/r3disc/quant"
PY = "/opt/venvs/qbase-ingest/bin/python"
OUT = "/root/r3disc"
SNAP = "38"
FLIP_OFF = ["2000-01-04", "2015-06-15", "2023-06-15"]
FLIP_ON = ["1992-10-04", "1993-01-03"]

env = dict(l.split("=", 1) for l in open(f"{ROOT}/.env").read().splitlines() if "=" in l)
QDSN, TDSN = env["QBASE_APP_DSN"], env["TAOSHA_APP_DSN"]

LOGF = open(f"{OUT}/orchestrate.log", "a", buffering=1)


def now_s():
    return datetime.datetime.now().isoformat(timespec="milliseconds")


def log(msg):
    line = f"{now_s()} {msg}"
    print(line, flush=True)
    LOGF.write(line + "\n")


def db_now(conn):
    return str(conn.execute("SELECT clock_timestamp()").fetchone()[0])


def watermark(tag):
    """单事务提交水印批(qbase_app 身份,与真实并发回填同权限路径);返回时间戳与批id。"""
    with psycopg.connect(QDSN) as c:
        t0 = db_now(c)
        with c.transaction():
            bid = c.execute(
                "INSERT INTO fact_batch (source, asof_date, pull_time, note) "
                "VALUES ('tushare:trade_cal', current_date, now(), %s) RETURNING batch_id",
                (f"DISCRIMINATIVE-WATERMARK {tag}(隔离验证专用,仅存 qbase_iso;"
                 f"外部复核判别力补测令 2026-07-13):批8全量拷贝仅5行is_open翻转,"
                 f"翻关{FLIP_OFF},翻开{FLIP_ON}",),
            ).fetchone()[0]
            cur = c.execute(
                "INSERT INTO trade_cal_snap (batch_id, exchange, cal_date, is_open, pretrade_date, valid_time) "
                "SELECT %s, exchange, cal_date, "
                " CASE WHEN cal_date = ANY(%s::date[]) THEN 0 "
                "      WHEN cal_date = ANY(%s::date[]) THEN 1 "
                "      ELSE is_open END, "
                " pretrade_date, valid_time "
                "FROM trade_cal_snap WHERE batch_id = 8",
                (bid, FLIP_OFF, FLIP_ON),
            )
            nrows = cur.rowcount
        t1 = db_now(c)
        wall = now_s()
    return {"wm_batch": bid, "wm_rows": nrows, "wm_txn_begin_db": t0,
            "wm_after_commit_db": t1, "wm_after_commit_wall": wall, "tag": tag}


def run_seed(module, logname, trigger, tag):
    """启动 seed(隔离树+iso .env),触发行出现后立即并发提交水印;逐行时间戳日志。"""
    lf = open(f"{OUT}/{logname}", "a", buffering=1)
    mon = psycopg.connect(QDSN)
    mon.autocommit = True
    t_start_db, t_start_wall = db_now(mon), now_s()
    log(f"{tag}: 启动 {module}(--source-snapshot-id {SNAP})")
    proc = subprocess.Popen(
        [PY, "-u", "-m", module, "--source-snapshot-id", SNAP],
        cwd=ROOT, env={**os.environ, "PYTHONPATH": ROOT},
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    seen = threading.Event()
    lines = []

    def pump():
        for raw in proc.stdout:
            line = raw.rstrip("\n")
            ts = now_s()
            lf.write(f"{ts} {line}\n")
            lines.append((ts, line))
            if trigger in line:
                seen.set()

    th = threading.Thread(target=pump)
    th.start()
    if not seen.wait(timeout=180):
        log(f"⚠ {tag}: 触发行 180s 未现,兜底改为立即提交水印(seed 仍在跑)")
    wm = watermark(tag)
    log(f"{tag}: 水印批 {wm['wm_batch']} 已提交({wm['wm_rows']} 行)"
        f" commit≈{wm['wm_after_commit_db']}")
    rc = proc.wait()
    th.join()
    t_end_db, t_end_wall = db_now(mon), now_s()
    mon.close()
    lf.close()
    sql_phase = next((ts for ts, l in lines if "独立复算中" in l), None)
    land_line = next((l for ts, l in lines if "✓ 落库" in l), None)
    log(f"{tag}: seed 退出 rc={rc};SQL复算相位起点={sql_phase};{land_line}")
    return {
        "tag": tag, "module": module, "rc": rc,
        "seed_start_db": t_start_db, "seed_start_wall": t_start_wall,
        "seed_end_db": t_end_db, "seed_end_wall": t_end_wall,
        "watermark": wm,
        "sql_recompute_phase_wall": sql_phase,
        "wm_before_sql_recompute": (sql_phase is not None
                                    and wm["wm_after_commit_wall"] < sql_phase),
        "landing_line": land_line,
        "log_file": f"{OUT}/{logname}",
    }


def fetchall(conn, sql, args=()):
    return [list(map(str, r)) for r in conn.execute(sql, args).fetchall()]


def collect(run1, run2):
    ev = {"order": "docs/postaudit-round3-disc-order-2026-07-13.md",
          "generated_wall": now_s(), "iso_env": {"qbase": "qbase_iso", "taosha": "taosha_iso"},
          "code_tree": ROOT}
    q = psycopg.connect(QDSN)
    q.autocommit = True
    t = psycopg.connect(TDSN)
    t.autocommit = True
    q.execute("SELECT set_config('shuheng.study_snapshot_id', %s, false)", (SNAP,))
    ev["code_head"] = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                     capture_output=True, text=True).stdout.strip()

    w1, w2 = run1["watermark"]["wm_batch"], run2["watermark"]["wm_batch"]
    exc = ("SELECT count(*) FROM (SELECT exchange, cal_date, is_open FROM trade_cal_snap WHERE batch_id=%s "
           "EXCEPT SELECT exchange, cal_date, is_open FROM trade_cal_snap WHERE batch_id=%s) x")
    ev["watermark_discriminative"] = {
        "W1_vs_8_diff_rows": fetchall(q,
            "SELECT cal_date, is_open FROM (SELECT cal_date, is_open FROM trade_cal_snap WHERE batch_id=%s "
            "EXCEPT SELECT cal_date, is_open FROM trade_cal_snap WHERE batch_id=8) x ORDER BY cal_date", (w1,)),
        "W1_except_8": q.execute(exc, (w1, 8)).fetchone()[0],
        "8_except_W1": q.execute(exc, (8, w1)).fetchone()[0],
        "W2_except_8": q.execute(exc, (w2, 8)).fetchone()[0],
        "8_except_W2": q.execute(exc, (8, w2)).fetchone()[0],
        "old_batch9_except_8": q.execute(exc, (9, 8)).fetchone()[0],
        "old_8_except_batch9": q.execute(exc, (8, 9)).fetchone()[0],
        "old_batch10_except_8": q.execute(exc, (10, 8)).fetchone()[0],
        "old_8_except_batch10": q.execute(exc, (8, 10)).fetchone()[0],
        "open_days_pre_holdout_batch8": q.execute(
            "SELECT count(*) FROM trade_cal_snap WHERE batch_id=8 AND is_open=1 AND cal_date<'2024-07-01'").fetchone()[0],
        "open_days_pre_holdout_W1": q.execute(
            "SELECT count(*) FROM trade_cal_snap WHERE batch_id=%s AND is_open=1 AND cal_date<'2024-07-01'", (w1,)).fetchone()[0],
    }
    ev["counterfactual_foundation"] = {
        "pinned_prices_bars_on_flip_on": {
            d: q.execute("SELECT count(*) FROM explore_reader_prices_snap WHERE trade_date=%s", (d,)).fetchone()[0]
            for d in FLIP_ON},
        "note": "翻开日在钉批(快照38→trade_cal=8同源 daily/adj 批)价视图有真实 bar:若 seed 读到水印日历(此两日 is_open=1),产出必新增这些日期的行;翻关三日从水印日历消失,产出必缺行。",
    }

    # Run1 产物证据(market_eqw_return)
    b1 = t.execute("SELECT max(batch_id) FROM market_batch").fetchone()[0]
    meta1 = t.execute(
        "SELECT batch_id, out_rows, min_date, max_date, left(frozen_digest,8), "
        "source_anchor->'qbase'->>'trade_cal', source_anchor->'source_manifest', source_anchor->'qbase' "
        "FROM market_batch WHERE batch_id=%s", (b1,)).fetchone()
    mexc = ("SELECT count(*) FROM (SELECT trade_date, ret_eqw, n_stocks FROM market_eqw_return WHERE batch_id=%s "
            "EXCEPT SELECT trade_date, ret_eqw, n_stocks FROM market_eqw_return WHERE batch_id=%s) x")
    ev["run1_market_return"] = {
        **run1,
        "new_batch_id": b1,
        "out_rows": meta1[1], "min_date": str(meta1[2]), "max_date": str(meta1[3]),
        "frozen_digest8": meta1[4],
        "anchor_trade_cal": meta1[5],
        "anchor_source_manifest": meta1[6],
        "anchor_qbase_vector": meta1[7],
        "content_newbatch_except_39": t.execute(mexc, (b1, 39)).fetchone()[0],
        "content_39_except_newbatch": t.execute(mexc, (39, b1)).fetchone()[0],
        "flip_off_rows_present": fetchall(t,
            "SELECT trade_date, ret_eqw, n_stocks FROM market_eqw_return "
            "WHERE batch_id=%s AND trade_date = ANY(%s::date[]) ORDER BY trade_date", (b1, FLIP_OFF)),
        "flip_off_equal_batch39": fetchall(t,
            "SELECT a.trade_date, (a.ret_eqw = b.ret_eqw AND a.n_stocks = b.n_stocks) "
            "FROM market_eqw_return a JOIN market_eqw_return b USING (trade_date) "
            "WHERE a.batch_id=%s AND b.batch_id=39 AND a.trade_date = ANY(%s::date[]) "
            "ORDER BY a.trade_date", (b1, FLIP_OFF)),
        "flip_on_rows_absent": t.execute(
            "SELECT count(*) FROM market_eqw_return WHERE batch_id=%s AND trade_date = ANY(%s::date[])",
            (b1, FLIP_ON)).fetchone()[0],
    }

    # Run2 产物证据(pool_b1_return)
    b2 = t.execute("SELECT max(batch_id) FROM pool_b1_return_batch").fetchone()[0]
    cols2 = [r[0] for r in t.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name='pool_b1_return_batch'").fetchall()]
    meta2 = t.execute(
        "SELECT batch_id, out_rows, source_anchor->'qbase'->>'trade_cal', "
        "source_anchor->'source_manifest', source_anchor->'qbase', source_anchor "
        "FROM pool_b1_return_batch WHERE batch_id=%s", (b2,)).fetchone()
    pexc = ("SELECT count(*) FROM (SELECT trade_date, ret_pool_eqw, n_pool_stocks FROM pool_b1_return WHERE batch_id=%s "
            "EXCEPT SELECT trade_date, ret_pool_eqw, n_pool_stocks FROM pool_b1_return WHERE batch_id=%s) x")
    ev["run2_pool_b1_return"] = {
        **run2,
        "new_batch_id": b2,
        "batch_table_columns": cols2,
        "out_rows": meta2[1],
        "anchor_trade_cal": meta2[2],
        "anchor_source_manifest": meta2[3],
        "anchor_qbase_vector": meta2[4],
        "anchor_full": meta2[5],
        "content_newbatch_except_5": t.execute(pexc, (b2, 5)).fetchone()[0],
        "content_5_except_newbatch": t.execute(pexc, (5, b2)).fetchone()[0],
        "flip_off_rows_present": fetchall(t,
            "SELECT trade_date, ret_pool_eqw, n_pool_stocks FROM pool_b1_return "
            "WHERE batch_id=%s AND trade_date = ANY(%s::date[]) ORDER BY trade_date", (b2, FLIP_OFF)),
        "flip_off_equal_batch5": fetchall(t,
            "SELECT a.trade_date, (a.ret_pool_eqw = b.ret_pool_eqw AND a.n_pool_stocks = b.n_pool_stocks) "
            "FROM pool_b1_return a JOIN pool_b1_return b USING (trade_date) "
            "WHERE a.batch_id=%s AND b.batch_id=5 AND a.trade_date = ANY(%s::date[]) "
            "ORDER BY a.trade_date", (b2, FLIP_OFF)),
        "flip_on_rows_absent": t.execute(
            "SELECT count(*) FROM pool_b1_return WHERE batch_id=%s AND trade_date = ANY(%s::date[])",
            (b2, FLIP_ON)).fetchone()[0],
    }

    # 反事实通路:current/max 路由下水印可见
    mx = q.execute("SELECT max(batch_id) FROM fact_batch WHERE source='tushare:trade_cal'").fetchone()[0]
    ev["current_route_counterfactual"] = {
        "max_trade_cal_batch_after_runs": mx,
        "is_watermark": mx == w2,
        "probe_is_open_on_max_batch": fetchall(q,
            "SELECT cal_date, is_open FROM trade_cal_snap WHERE batch_id=%s "
            "AND cal_date = ANY(%s::date[]) ORDER BY cal_date", (mx, FLIP_OFF + FLIP_ON)),
        "probe_is_open_on_batch8": fetchall(q,
            "SELECT cal_date, is_open FROM trade_cal_snap WHERE batch_id=8 "
            "AND cal_date = ANY(%s::date[]) ORDER BY cal_date", (FLIP_OFF + FLIP_ON,)),
        "note": "若 seed 走 current/max 批次路由(旧作废模式),读到的即水印翻转值;实测产出与批8全等、与水印矛盾=实际读取源=批8。",
    }
    q.close()
    t.close()
    return ev


def production_untouched():
    """生产零触碰核验(只读)。"""
    r = subprocess.run(["sudo", "-u", "postgres", "psql", "qbase", "-tAc",
                        "SELECT string_agg(batch_id::text, ',' ORDER BY batch_id) "
                        "FROM fact_batch WHERE source='tushare:trade_cal'"],
                       capture_output=True, text=True)
    r2 = subprocess.run(["sudo", "-u", "postgres", "psql", "taosha", "-tAc",
                         "SELECT (SELECT max(batch_id) FROM market_batch) || '/' || "
                         "(SELECT max(batch_id) FROM pool_b1_return_batch)"],
                        capture_output=True, text=True)
    g = subprocess.run(["git", "-C", "/opt/quant", "status", "--porcelain"],
                       capture_output=True, text=True)
    return {"prod_qbase_trade_cal_batches": r.stdout.strip(),
            "prod_taosha_max_batches_mret/pret": r2.stdout.strip(),
            "prod_git_porcelain_lines": len([l for l in g.stdout.splitlines() if l.strip()])}


def main():
    log("== 判别力并发补测开始(隔离环境 qbase_iso/taosha_iso)==")
    run1 = run_seed("taosha.ingest.seed_market_return", "mret_seed.log",
                    "逐票聚合中", "RUN1-mret")
    if run1["rc"] != 0:
        log("⛔ RUN1 seed 非零退出,中止(证据日志已留)")
        json.dump({"aborted": "run1", "run1": run1}, open(f"{OUT}/evidence.json", "w"),
                  ensure_ascii=False, indent=1, default=str)
        return
    run2 = run_seed("taosha.ingest.seed_pool_b1_return", "pret_seed.log",
                    "逐票门控聚合中", "RUN2-pret")
    if run2["rc"] != 0:
        log("⛔ RUN2 seed 非零退出,中止(证据日志已留)")
        json.dump({"aborted": "run2", "run1": run1, "run2": run2},
                  open(f"{OUT}/evidence.json", "w"), ensure_ascii=False, indent=1, default=str)
        return
    ev = collect(run1, run2)
    ev["production_untouched"] = production_untouched()
    json.dump(ev, open(f"{OUT}/evidence.json", "w"), ensure_ascii=False, indent=1, default=str)
    log("== 证据已写 /root/r3disc/evidence.json ==")
    # 摘要行(供 orchestrate.log 快读)
    r1, r2v = ev["run1_market_return"], ev["run2_pool_b1_return"]
    log(f"R1: batch={r1['new_batch_id']} rows={r1['out_rows']} anchor_tc={r1['anchor_trade_cal']} "
        f"except39={r1['content_newbatch_except_39']}/{r1['content_39_except_newbatch']} "
        f"flip_on_absent={r1['flip_on_rows_absent']}")
    log(f"R2: batch={r2v['new_batch_id']} rows={r2v['out_rows']} anchor_tc={r2v['anchor_trade_cal']} "
        f"except5={r2v['content_newbatch_except_5']}/{r2v['content_5_except_newbatch']} "
        f"flip_on_absent={r2v['flip_on_rows_absent']}")
    log("== 全部完成 ==")


if __name__ == "__main__":
    main()
