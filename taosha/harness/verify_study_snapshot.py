"""淘沙 · StudySnapshot 快照锁定验收件(可信度硬化窗口 ②,常设)。

职责: 以 taosha_engine 身份实测 fail-closed(--mode probes)+ manifest 读面确定性摘要(--mode dump)。
口径依据: docs/hardening-window-order-2026-07-12.md ②(无 manifest 拒运行/禁静默回退 *_current)。
验收档: taosha/docs/hardening-item2-studysnapshot-acceptance-2026-07-12.md。

验收编排(aliyun):
  probes                                    # 非法路径全拒实测
  dump --snapshot-id N --out d1.json        # 读面摘要 #1
  dump --snapshot-id N --out d2.json        # 读面摘要 #2(期间并发落新批次)→ digest 必须与 #1 逐字节同
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import psycopg

from taosha.reader.view import ViewReader, _load_env, _ENV_QBASE, _ENV_TAOSHA

_results: list[tuple[str, bool, str]] = []


def _ok(name: str, passed: bool, detail: str = "") -> None:
    _results.append((name, passed, detail))
    print(f"[{'PASS' if passed else 'FAIL'}] {name}" + (f" —— {detail}" if detail else ""))


def _engine_dsns() -> tuple[str, str]:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env = _load_env(os.path.join(root, ".env"))
    q, t = env.get(_ENV_QBASE), env.get(_ENV_TAOSHA)
    if not q or not t:
        raise SystemExit(f"缺 {_ENV_QBASE}/{_ENV_TAOSHA}(.env)")
    return q, t


def _expect_reject(conn, name: str, sql: str, setup: tuple | None = None) -> None:
    """期望被拒(权限拒/GUC 未设报错/严格函数 RAISE 任一层)。每探针独立事务。"""
    try:
        with conn.cursor() as cur:
            if setup:
                cur.execute(*setup)
            cur.execute(sql)
        _ok(name, False, "本应被拒却放行")
    except psycopg.Error as e:
        _ok(name, True, str(e).splitlines()[0][:110])
    conn.rollback()


def probes() -> None:
    qdsn, tdsn = _engine_dsns()
    with psycopg.connect(qdsn) as qc:
        for v in ("explore_reader_prices", "explore_reader_calendar", "explore_reader_events"):
            _expect_reject(qc, f"P-q1 引擎读 {v}(current 路由)拒", f"SELECT count(*) FROM {v}")
        _expect_reject(qc, "P-q2 snap 视图无 GUC(无 manifest)拒",
                       "SELECT count(*) FROM explore_reader_calendar_snap")
        # 修法#2(外审 2026-07-13): 引擎自报完整伪造 JSON 批次向量必须失效(旧 study_batches
        # 路由作废,路由只认受权角色落库的镜像+发布凭证;此探针在 014 前=可穿透的攻击原型)
        _expect_reject(qc, "P-q3 完整伪造批次向量 JSON 自报拒(修法#2,旧 shuheng.study_batches 失效)",
                       "SELECT count(*) FROM explore_reader_calendar_snap",
                       setup=("SELECT set_config('shuheng.study_batches', %s, false)",
                              ('{"stock_basic":999,"namechange":999,"trade_cal":999,"daily":999,'
                               '"adj_factor":999,"forecast":999,"stk_holdertrade":999}',)))
        _expect_reject(qc, "P-q4 不存在 snapshot_id 拒(qbase 侧无镜像/凭证)",
                       "SELECT count(*) FROM explore_reader_calendar_snap",
                       setup=("SELECT set_config('shuheng.study_snapshot_id','999999', false)", ()))
        _expect_reject(qc, "P-q5 引擎写权威镜像拒(受权角色专责)",
                       "INSERT INTO study_snapshot_mirror (snapshot_id, content) "
                       "VALUES (999999, '{\"qbase\":{},\"taosha\":{}}'::jsonb)")
        _expect_reject(qc, "P-q6 引擎写发布凭证拒(受权角色专责)",
                       "INSERT INTO study_snapshot_publication (snapshot_id, attested_digest) "
                       "VALUES (1, repeat('0',64))")
    with psycopg.connect(tdsn) as tc:
        for v in ("market_return_current", "pool_b1_current", "pool_b1_return_current",
                  "market_eqw_return", "pool_b1_membership", "pool_b1_return"):
            _expect_reject(tc, f"P-t1 引擎读 {v}(current/底表)拒", f"SELECT count(*) FROM {v}")
        _expect_reject(tc, "P-t2 snap 视图无 GUC(无 manifest)拒",
                       "SELECT count(*) FROM market_return_snap")
        _expect_reject(tc, "P-t3 manifest 不存在拒(id=999999)",
                       "SELECT count(*) FROM market_return_snap",
                       setup=("SELECT set_config('shuheng.study_snapshot_id','999999', false)", ()))
        with tc.cursor() as cur:  # 引擎写 manifest 必须拒(生成=受权角色专责)
            try:
                cur.execute("INSERT INTO study_snapshot (content) VALUES ('{}'::jsonb)")
                _ok("P-t4 引擎写 study_snapshot 拒", False, "本应被拒却放行")
            except psycopg.Error as e:
                _ok("P-t4 引擎写 study_snapshot 拒", True, str(e).splitlines()[0][:110])
        tc.rollback()
    # python 层 fail-closed
    try:
        ViewReader()
        _ok("P-py1 ViewReader 无 snapshot_id 拒", False, "本应被拒却放行")
    except RuntimeError as e:
        _ok("P-py1 ViewReader 无 snapshot_id 拒", True, str(e)[:110])
    try:
        ViewReader(snapshot_id=999999)
        _ok("P-py2 ViewReader manifest 不存在拒", False, "本应被拒却放行")
    except RuntimeError as e:
        _ok("P-py2 ViewReader manifest 不存在拒", True, str(e)[:110])


def dump(snapshot_id: int, out: str) -> None:
    """manifest 读面全量确定性摘要(引擎视角):calendar/events/两基准/池成员/定样本 prices。"""
    rd = ViewReader(snapshot_id=snapshot_id)
    h = hashlib.sha256()
    counts: dict = {"snapshot_id": snapshot_id, "manifest_digest": rd.snapshot_info["digest"]}

    cal = list(rd.calendar())
    for r in cal:
        h.update(f"C|{r.trade_date}|{r.pretrade_date}\n".encode())
    counts["calendar_rows"] = len(cal)

    ev = list(rd.events())
    for e in ev:
        h.update(f"E|{e.ts_code}|{e.event_id}|{e.first_ann_date}|{e.event_type_layer}|{e.snapshot_batch}\n".encode())
    counts["event_rows"] = len(ev)

    dates = [c.trade_date for c in cal]
    for tag, series in (("M", rd.market_return(dates)), ("P", rd.pool_return(dates))):
        n = 0
        for d, v in zip(dates, series):
            if v is not None:
                h.update(f"{tag}|{d}|{v!r}\n".encode())
                n += 1
        counts[f"{tag}_nonnull"] = n

    mem = rd.pool_membership()
    for d in sorted(mem):
        h.update(f"B|{d}|{','.join(sorted(mem[d]))}\n".encode())
    counts["pool_days"] = len(mem)
    counts["pool_member_rows"] = sum(len(v) for v in mem.values())

    sample = sorted({e.ts_code for e in ev})[:20]   # 确定性定样本(manifest 给定则恒定)
    rd2 = ViewReader(snapshot_id=snapshot_id, sample=set(sample))
    n = 0
    for p in rd2.prices():
        h.update(f"X|{p.ts_code}|{p.trade_date}|{p.close!r}|{p.limit_status}|{p.board}|"
                 f"{p.is_st}|{p.industry}|{p.open!r}\n".encode())
        n += 1
    counts["price_rows_sample20"] = n

    counts["surface_sha256"] = h.hexdigest()
    with open(out, "w") as fh:
        json.dump(counts, fh, ensure_ascii=False, indent=2, sort_keys=True, default=str)
    print(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True, default=str))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("probes", "dump"), required=True)
    ap.add_argument("--snapshot-id", type=int)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.mode == "probes":
        probes()
        failed = [r for r in _results if not r[1]]
        print(f"\n== fail-closed 探针: {len(_results) - len(failed)}/{len(_results)} PASS ==")
        return 1 if failed else 0
    if a.snapshot_id is None or a.out is None:
        raise SystemExit("dump 模式需 --snapshot-id 与 --out")
    dump(a.snapshot_id, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
