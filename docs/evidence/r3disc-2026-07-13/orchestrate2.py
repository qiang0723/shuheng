#!/usr/bin/env python3
"""判别力并发补测 v2——时序修正编排(外部复核第三回件令,2026-07-13)。

与 v1(orchestrate.py)唯一差别 = 水印提交时序 + 时点取证;水印设计/隔离环境/证据集不变。

时序要求(令原文):T_anchor < T_watermark_commit < T_main_select_start < T_finish。
实现:
  - 触发点="源快照绑定"行(= source snapshot 38 及 anchor 读取完成后的第一行输出);
  - 触发即提交水印批(锚读完成 → 水印 → 诊断计数查询仍在跑 → 主读游标尚未开始);
  - T_main_select_start 主证 = pg_stat_activity.query_start(服务器钟),主读语句签名=
    命名游标 mkt_prices_stream / pool_prices_stream(DECLARE/FETCH 文本必含);
    辅证 = "逐票聚合中"/"门控聚合中"相位打印时戳(代码序先于游标 DECLARE = 主读开启下界)。
  - 全部时钟同宿主机(seed / PostgreSQL / 编排同机)。
加强项:v1 水印批 11/12 已存 iso 且为 max(trade_cal)——本轮 seed 启动起任意相位任意语句走
  current/max 皆必见可区分内容(含锚读与诊断计数查询);诊断计数值与 v1 实测全等另作断言。
"""
import datetime
import json
import os
import re
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

LOGF = open(f"{OUT}/orchestrate2.log", "a", buffering=1)


def now_dt():
    return datetime.datetime.now()


def iso(x):
    if isinstance(x, datetime.datetime):
        if x.tzinfo is not None:
            x = x.astimezone().replace(tzinfo=None)
        return x.isoformat(timespec="milliseconds")
    return str(x)


def log(msg):
    line = f"{iso(now_dt())} {msg}"
    print(line, flush=True)
    LOGF.write(line + "\n")


def db_now(conn):
    return conn.execute("SELECT clock_timestamp()").fetchone()[0]


def to_naive(x):
    return x.astimezone().replace(tzinfo=None) if x.tzinfo is not None else x


def watermark(tag):
    with psycopg.connect(QDSN) as c:
        t0 = db_now(c)
        with c.transaction():
            bid = c.execute(
                "INSERT INTO fact_batch (source, asof_date, pull_time, note) "
                "VALUES ('tushare:trade_cal', current_date, now(), %s) RETURNING batch_id",
                (f"DISCRIMINATIVE-WATERMARK v2 {tag}(隔离验证专用,仅存 qbase_iso;"
                 f"复核第三回件时序令 2026-07-13):批8全量拷贝仅5行is_open翻转,"
                 f"翻关{FLIP_OFF},翻开{FLIP_ON};提交时序=锚读完成后、主读游标开始前",),
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
        wall = now_dt()
    return {"wm_batch": bid, "wm_rows": nrows,
            "wm_txn_begin_db": to_naive(t0), "wm_commit_db": to_naive(t1),
            "wm_commit_wall": wall, "tag": tag}


class ActivityPoller(threading.Thread):
    """轮询 pg_stat_activity(qbase_iso),记录所有非本连接的活动语句(pid, query_start, query)。"""

    def __init__(self):
        super().__init__(daemon=True)
        self.stop_ev = threading.Event()
        self.records = {}   # (pid, query_start, q160) -> first_seen_wall

    def run(self):
        conn = psycopg.connect(QDSN)
        conn.autocommit = True
        while not self.stop_ev.is_set():
            try:
                rows = conn.execute(
                    "SELECT pid, query_start, left(query,160) FROM pg_stat_activity "
                    "WHERE datname = current_database() AND pid <> pg_backend_pid() "
                    "AND state = 'active'").fetchall()
                for pid, qs, q in rows:
                    key = (pid, iso(to_naive(qs)) if qs else None, q)
                    self.records.setdefault(key, iso(now_dt()))
            except Exception as e:  # 轮询失败不致命,记日志
                log(f"poller error: {e}")
            self.stop_ev.wait(0.12)
        conn.close()

    def stop(self):
        self.stop_ev.set()


def run_seed_v2(module, logname, tag, main_sig, phase_word):
    lf = open(f"{OUT}/{logname}", "a", buffering=1)
    mon = psycopg.connect(QDSN)
    mon.autocommit = True
    pre_max = mon.execute(
        "SELECT max(batch_id) FROM fact_batch WHERE source='tushare:trade_cal'").fetchone()[0]
    pre_max_probes = [list(map(str, r)) for r in mon.execute(
        "SELECT cal_date, is_open FROM trade_cal_snap WHERE batch_id=%s "
        "AND cal_date = ANY(%s::date[]) ORDER BY cal_date",
        (pre_max, FLIP_OFF + FLIP_ON)).fetchall()]
    poller = ActivityPoller()
    poller.start()
    t_start_db, t_start_wall = to_naive(db_now(mon)), now_dt()
    log(f"{tag}: 启动 {module}(--source-snapshot-id {SNAP});跑前 max(trade_cal)={pre_max}(水印内容)")
    proc = subprocess.Popen(
        [PY, "-u", "-m", module, "--source-snapshot-id", SNAP],
        cwd=ROOT, env={**os.environ, "PYTHONPATH": ROOT},
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    anchor_ev, lines = threading.Event(), []
    t_marks = {}

    def pump():
        for raw in proc.stdout:
            line = raw.rstrip("\n")
            ts = now_dt()
            lf.write(f"{iso(ts)} {line}\n")
            lines.append((ts, line))
            if "源快照绑定" in line and "anchor" not in t_marks:
                t_marks["anchor"] = ts
                anchor_ev.set()
            if phase_word in line and "phase" not in t_marks:
                t_marks["phase"] = ts

    th = threading.Thread(target=pump)
    th.start()
    if not anchor_ev.wait(timeout=300):
        raise RuntimeError(f"{tag}: 300s 未见〔源快照绑定〕行,中止(seed 日志已留)")
    wm = watermark(tag)
    log(f"{tag}: 锚读完成 {iso(t_marks['anchor'])} → 水印批 {wm['wm_batch']} "
        f"commit {iso(wm['wm_commit_db'])}({wm['wm_rows']} 行)")
    rc = proc.wait()
    th.join()
    t_finish_db, t_finish_wall = to_naive(db_now(mon)), now_dt()
    poller.stop()
    poller.join(timeout=3)
    mon.close()
    lf.close()

    main_stmts = sorted(
        [{"pid": k[0], "query_start_db": k[1], "query": k[2], "first_seen": v}
         for k, v in poller.records.items() if main_sig in (k[2] or "")],
        key=lambda r: r["query_start_db"] or "")
    all_stmts = sorted(
        [{"pid": k[0], "query_start_db": k[1], "query": (k[2] or "")[:100], "first_seen": v}
         for k, v in poller.records.items()],
        key=lambda r: r["query_start_db"] or "")
    t_anchor = t_marks.get("anchor")
    t_phase = t_marks.get("phase")
    t_main_db = (datetime.datetime.fromisoformat(main_stmts[0]["query_start_db"])
                 if main_stmts else None)
    ordering = {
        "T_anchor": iso(t_anchor),
        "T_watermark_commit_db": iso(wm["wm_commit_db"]),
        "T_watermark_commit_wall": iso(wm["wm_commit_wall"]),
        "T_main_select_lower_bound_phase_print": iso(t_phase),
        "T_main_select_start_pg_query_start": iso(t_main_db) if t_main_db else None,
        "T_finish_db": iso(t_finish_db),
        "strict_1_anchor_lt_wm": t_anchor < wm["wm_commit_wall"],
        "strict_2_wm_lt_main_phase_print": wm["wm_commit_wall"] < t_phase if t_phase else None,
        "strict_2b_wm_lt_main_pg_query_start": (wm["wm_commit_db"] < t_main_db) if t_main_db else None,
        "strict_3_main_lt_finish": (t_main_db < t_finish_db) if t_main_db else None,
        "margin_wm_to_main_seconds": ((t_main_db - wm["wm_commit_db"]).total_seconds()
                                      if t_main_db else None),
        "clock_note": "seed/PostgreSQL/编排同宿主机同时钟;wall=进程钟,db=clock_timestamp()",
    }
    landing = next((l for ts, l in lines if "✓ 落库" in l), None)
    log(f"{tag}: rc={rc};{landing};主读 query_start={ordering['T_main_select_start_pg_query_start']}"
        f"(水印后 {ordering['margin_wm_to_main_seconds']}s)")
    return {
        "tag": tag, "module": module, "rc": rc,
        "pre_run_max_trade_cal_batch": pre_max,
        "pre_run_max_batch_probe_is_open": pre_max_probes,
        "seed_start_db": iso(t_start_db), "seed_finish_db": iso(t_finish_db),
        "watermark": {k: iso(v) if isinstance(v, datetime.datetime) else v for k, v in wm.items()},
        "ordering": ordering,
        "main_statements_observed": main_stmts[:6],
        "activity_sample_all": all_stmts,
        "landing_line": landing,
        "log_file": f"{OUT}/{logname}",
    }


def parse_counts(path, pattern):
    txt = open(path, encoding="utf-8").read()
    m = re.findall(pattern, txt)
    return m[-1] if m else None


def fetchall(conn, sql, args=()):
    return [list(map(str, r)) for r in conn.execute(sql, args).fetchall()]


def collect(run1, run2):
    ev = {"order": "docs/postaudit-round3-disc2-order-2026-07-13.md",
          "generated_wall": iso(now_dt()),
          "iso_env": {"qbase": "qbase_iso", "taosha": "taosha_iso"}, "code_tree": ROOT}
    q = psycopg.connect(QDSN)
    q.autocommit = True
    t = psycopg.connect(TDSN)
    t.autocommit = True
    q.execute("SELECT set_config('shuheng.study_snapshot_id', %s, false)", (SNAP,))
    ev["code_head"] = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                     capture_output=True, text=True).stdout.strip()
    w3, w4 = run1["watermark"]["wm_batch"], run2["watermark"]["wm_batch"]
    exc = ("SELECT count(*) FROM (SELECT exchange, cal_date, is_open FROM trade_cal_snap WHERE batch_id=%s "
           "EXCEPT SELECT exchange, cal_date, is_open FROM trade_cal_snap WHERE batch_id=%s) x")
    ev["watermark_discriminative"] = {
        "W3_except_8": q.execute(exc, (w3, 8)).fetchone()[0],
        "8_except_W3": q.execute(exc, (8, w3)).fetchone()[0],
        "W4_except_8": q.execute(exc, (w4, 8)).fetchone()[0],
        "8_except_W4": q.execute(exc, (8, w4)).fetchone()[0],
    }
    # 诊断计数查询判别断言:本轮跑前 max 批已=可区分水印(批11/12)→计数查询若走 current/max
    # 其快照(先于新水印、晚于旧水印)必见翻转日历,计数必异于 v1;实测须与 v1 全等。
    ev["count_query_discriminative"] = {
        "v1_mret_raw_input": parse_counts(f"{OUT}/mret_seed.log", r"raw=(\d+) 日历轴input=(\d+)"),
        "v2_mret_raw_input": parse_counts(f"{OUT}/mret_seed2.log", r"raw=(\d+) 日历轴input=(\d+)"),
        "v1_pret_view_rows": parse_counts(f"{OUT}/pret_seed.log", r"价视图\(池宇宙∩calendar\): rows=(\d+)"),
        "v2_pret_view_rows": parse_counts(f"{OUT}/pret_seed2.log", r"价视图\(池宇宙∩calendar\): rows=(\d+)"),
    }
    ev["count_query_discriminative"]["mret_equal"] = (
        ev["count_query_discriminative"]["v1_mret_raw_input"]
        == ev["count_query_discriminative"]["v2_mret_raw_input"])
    ev["count_query_discriminative"]["pret_equal"] = (
        ev["count_query_discriminative"]["v1_pret_view_rows"]
        == ev["count_query_discriminative"]["v2_pret_view_rows"])

    b1 = t.execute("SELECT max(batch_id) FROM market_batch").fetchone()[0]
    meta1 = t.execute(
        "SELECT out_rows, source_anchor->'qbase'->>'trade_cal', source_anchor->'source_manifest', "
        "source_anchor->'qbase' FROM market_batch WHERE batch_id=%s", (b1,)).fetchone()
    mexc = ("SELECT count(*) FROM (SELECT trade_date, ret_eqw, n_stocks FROM market_eqw_return WHERE batch_id=%s "
            "EXCEPT SELECT trade_date, ret_eqw, n_stocks FROM market_eqw_return WHERE batch_id=%s) x")
    ev["run1_market_return"] = {
        **run1, "new_batch_id": b1, "out_rows": meta1[0],
        "anchor_trade_cal": meta1[1], "anchor_source_manifest": meta1[2],
        "anchor_qbase_vector": meta1[3],
        "content_newbatch_except_39": t.execute(mexc, (b1, 39)).fetchone()[0],
        "content_39_except_newbatch": t.execute(mexc, (39, b1)).fetchone()[0],
        "flip_off_rows_present": fetchall(t,
            "SELECT trade_date, ret_eqw, n_stocks FROM market_eqw_return "
            "WHERE batch_id=%s AND trade_date = ANY(%s::date[]) ORDER BY trade_date", (b1, FLIP_OFF)),
        "flip_on_rows_absent": t.execute(
            "SELECT count(*) FROM market_eqw_return WHERE batch_id=%s AND trade_date = ANY(%s::date[])",
            (b1, FLIP_ON)).fetchone()[0],
    }
    b2 = t.execute("SELECT max(batch_id) FROM pool_b1_return_batch").fetchone()[0]
    meta2 = t.execute(
        "SELECT out_rows, source_anchor->'qbase'->>'trade_cal', source_anchor->'source_manifest', "
        "source_anchor FROM pool_b1_return_batch WHERE batch_id=%s", (b2,)).fetchone()
    pexc = ("SELECT count(*) FROM (SELECT trade_date, ret_pool_eqw, n_pool_stocks FROM pool_b1_return WHERE batch_id=%s "
            "EXCEPT SELECT trade_date, ret_pool_eqw, n_pool_stocks FROM pool_b1_return WHERE batch_id=%s) x")
    ev["run2_pool_b1_return"] = {
        **run2, "new_batch_id": b2, "out_rows": meta2[0],
        "anchor_trade_cal": meta2[1], "anchor_source_manifest": meta2[2],
        "anchor_full": meta2[3],
        "content_newbatch_except_5": t.execute(pexc, (b2, 5)).fetchone()[0],
        "content_5_except_newbatch": t.execute(pexc, (5, b2)).fetchone()[0],
        "flip_off_rows_present": fetchall(t,
            "SELECT trade_date, ret_pool_eqw, n_pool_stocks FROM pool_b1_return "
            "WHERE batch_id=%s AND trade_date = ANY(%s::date[]) ORDER BY trade_date", (b2, FLIP_OFF)),
        "flip_on_rows_absent": t.execute(
            "SELECT count(*) FROM pool_b1_return WHERE batch_id=%s AND trade_date = ANY(%s::date[])",
            (b2, FLIP_ON)).fetchone()[0],
    }
    mx = q.execute("SELECT max(batch_id) FROM fact_batch WHERE source='tushare:trade_cal'").fetchone()[0]
    ev["current_route_counterfactual"] = {
        "max_trade_cal_batch_after_runs": mx, "is_watermark": mx == w4,
        "probe_is_open_on_max_batch": fetchall(q,
            "SELECT cal_date, is_open FROM trade_cal_snap WHERE batch_id=%s "
            "AND cal_date = ANY(%s::date[]) ORDER BY cal_date", (mx, FLIP_OFF + FLIP_ON)),
    }
    q.close()
    t.close()
    return ev


def production_untouched():
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
    log("== 判别力并发补测 v2(时序修正)开始 ==")
    run1 = run_seed_v2("taosha.ingest.seed_market_return", "mret_seed2.log",
                       "RUN3-mret", "mkt_prices_stream", "逐票聚合中")
    if run1["rc"] != 0:
        log("⛔ RUN3 seed 非零退出,中止")
        json.dump({"aborted": "run3", "run1": run1}, open(f"{OUT}/evidence2.json", "w"),
                  ensure_ascii=False, indent=1, default=str)
        return
    run2 = run_seed_v2("taosha.ingest.seed_pool_b1_return", "pret_seed2.log",
                       "RUN4-pret", "pool_prices_stream", "门控聚合中")
    if run2["rc"] != 0:
        log("⛔ RUN4 seed 非零退出,中止")
        json.dump({"aborted": "run4", "run1": run1, "run2": run2},
                  open(f"{OUT}/evidence2.json", "w"), ensure_ascii=False, indent=1, default=str)
        return
    ev = collect(run1, run2)
    ev["production_untouched"] = production_untouched()
    json.dump(ev, open(f"{OUT}/evidence2.json", "w"), ensure_ascii=False, indent=1, default=str)
    log("== 证据已写 /root/r3disc/evidence2.json ==")
    for k in ("run1_market_return", "run2_pool_b1_return"):
        r = ev[k]
        o = r["ordering"]
        log(f"{r['tag']}: batch={r['new_batch_id']} rows={r['out_rows']} anchor_tc={r['anchor_trade_cal']} "
            f"序={o['strict_1_anchor_lt_wm']}/{o['strict_2_wm_lt_main_phase_print']}/"
            f"{o['strict_2b_wm_lt_main_pg_query_start']}/{o['strict_3_main_lt_finish']} "
            f"余量={o['margin_wm_to_main_seconds']}s")
    log("== 全部完成 ==")


if __name__ == "__main__":
    main()
