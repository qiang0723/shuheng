"""淘沙 · PAP 可执行离场硬门自检(外审五项修法 #1,常设)。

职责: 以 taosha_app 身份实测三层硬门之层②(冻结触发器 _pap_freeze_gate)+层③(策略驱动
启动校验,子进程实测)——反向(a)禁组合/缺必填/白名单外/缺schema/伪称legacy/legacy升级为
策略/越权写registry 全拒 + 正向(b)legacy事件版冻结、两类合法执行方式、纯事件schema 全通。
(层①=python validate_pap,自检在 `python -m taosha.experiment.pap`。)
口径依据: docs/postaudit-five-order-2026-07-13.md #1(人终签 2026-07-13)。
验收档: taosha/docs/postaudit-item1-pap-execution-gate-acceptance-2026-07-13.md。

机制: 单事务 + 逐用例 SAVEPOINT + 末尾整体 ROLLBACK,台账/registry 零残留。
运行: aliyun `python -m taosha.experiment.verify_pap_gate`(需 TAOSHA_APP_DSN;层③子进程
     另需 TAOSHA_ENGINE_* DSN 于环境中)。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import psycopg

FAMILY = "_smtest_papgate"

SE_C2N = {"execution_profile": "close_to_next_open", "decision_time": "close_confirmed",
          "fill_time": "next_open", "fill_price": "next_adjusted_open",
          "slippage_rule": "frozen_cost"}
SE_PCT = {"execution_profile": "preclose_to_tail", "decision_cutoff": "探针占位(人定)",
          "decision_price_source": "探针占位(人定)", "fill_window": "探针占位",
          "fill_price_rule": "探针占位(人定)", "slippage_rule": "frozen_cost"}

_results: list[tuple[str, bool, str]] = []


def _ok(name: str, passed: bool, detail: str = "") -> None:
    _results.append((name, passed, detail))
    print(f"[{'PASS' if passed else 'FAIL'}] {name}" + (f" —— {detail}" if detail else ""))


def _pap(**extra) -> str:
    base = {"probe": True, "note": "papgate 探针,事务内回滚不落库"}
    base.update(extra)
    return json.dumps(base, ensure_ascii=False)


def _insert(cur, title: str, pap_text: str) -> int:
    cur.execute(
        """INSERT INTO experiment (family, family_trial, title, source_type, verdict_power,
                                   contamination_note, pap_json, data_class, crowding_prior)
           VALUES (%s, 0, %s, 'human', 'full', 'papgate 探针行(回滚不落库)',
                   %s::jsonb, '量价', '低') RETURNING exp_id""",
        (FAMILY, title, pap_text))
    return cur.fetchone()[0]


def _freeze_reject(cur, name: str, pap_text: str) -> None:
    """插入探针行→尝试冻结,期望被层② gate 拒;SAVEPOINT 全程回滚。"""
    cur.execute("SAVEPOINT c")
    try:
        e = _insert(cur, f"[papgate] {name}", pap_text)
        cur.execute("UPDATE experiment SET status='frozen', frozen_at=now() WHERE exp_id=%s", (e,))
    except psycopg.Error as err:
        cur.execute("ROLLBACK TO SAVEPOINT c")
        _ok(name, True, str(err).splitlines()[0][:130])
        return
    cur.execute("ROLLBACK TO SAVEPOINT c")
    _ok(name, False, "本应被拒却放行")


def _freeze_allow(cur, name: str, pap_text: str) -> None:
    cur.execute("SAVEPOINT c")
    try:
        e = _insert(cur, f"[papgate] {name}", pap_text)
        cur.execute("UPDATE experiment SET status='frozen', frozen_at=now() WHERE exp_id=%s", (e,))
        cur.execute("ROLLBACK TO SAVEPOINT c")
        _ok(name, True)
    except psycopg.Error as err:
        cur.execute("ROLLBACK TO SAVEPOINT c")
        _ok(name, False, f"合法路径被误拒: {str(err).splitlines()[0][:130]}")


def main() -> int:
    dsn = os.environ.get("TAOSHA_APP_DSN")
    if not dsn:
        print("环境无 TAOSHA_APP_DSN(应 source /opt/quant/.env,勿回显)", file=sys.stderr)
        return 2
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        # ── 结构断言: registry 物化普查 ──
        cur.execute("""SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
                       WHERE c.relname='pap_legacy_registry' AND NOT t.tgisinternal""")
        _ok("S1 legacy registry 表+焊死触发器在位", cur.fetchone()[0] >= 2)
        cur.execute("""SELECT count(*),
                              count(*) FILTER (WHERE status_at_migration='registered'),
                              count(*) FILTER (WHERE status_at_migration='frozen'),
                              count(*) FILTER (WHERE status_at_migration='done'),
                              count(*) FILTER (WHERE status_at_migration='closed')
                       FROM pap_legacy_registry""")
        tot, r, f_, d, c = cur.fetchone()
        _ok("S2 物化普查=全 25 存量(确认点②含 frozen/done/closed)",
            (tot, r, f_, d, c) == (25, 18, 3, 3, 1), f"total={tot} reg={r} froz={f_} done={d} closed={c}")
        cur.execute("SELECT count(*) FROM pap_legacy_registry WHERE exp_id IN (3,4,5)")
        _ok("S3 exp3(#2b)/exp4(#3)/exp5(#4) 在册", cur.fetchone()[0] == 3)

        # ── 正向(b) ──
        cur.execute("SAVEPOINT f1")
        try:
            cur.execute("UPDATE experiment SET status='frozen', frozen_at=now() "
                        "WHERE exp_id=8 AND status='registered'")
            ok = cur.rowcount == 1
            cur.execute("ROLLBACK TO SAVEPOINT f1")
            _ok("F1 既有 registered 纯事件 legacy 实验(exp8)事件版冻结放行", ok)
        except psycopg.Error as err:
            cur.execute("ROLLBACK TO SAVEPOINT f1")
            _ok("F1 既有 registered 纯事件 legacy 实验(exp8)事件版冻结放行", False,
                str(err).splitlines()[0][:130])
        _freeze_allow(cur, "F2 合法 close_to_next_open PAP 冻结放行",
                      _pap(pap_schema_version=2, analysis_type="strategy", strategy_execution=SE_C2N))
        _freeze_allow(cur, "F3 合法 preclose_to_tail PAP(必填全给)冻结放行",
                      _pap(pap_schema_version=2, analysis_type="event_and_strategy",
                           strategy_execution=SE_PCT))
        _freeze_allow(cur, "F4 新纯事件 schema PAP 冻结放行(不要求 strategy_execution)",
                      _pap(pap_schema_version=2, analysis_type="event"))

        # ── 反向(a) ──
        _freeze_reject(cur, "R1 新登记删除 pap_schema_version 冻结拒",
                       _pap())
        _freeze_reject(cur, "R2 close_confirmed+same_close 禁组合冻结拒(信息时序)",
                       _pap(pap_schema_version=2, analysis_type="strategy",
                            strategy_execution={"execution_profile": "close_to_next_open",
                                                "decision_time": "close_confirmed",
                                                "fill_time": "same_close",
                                                "fill_price": "same_close",
                                                "slippage_rule": "frozen_cost"}))
        _freeze_reject(cur, "R3 preclose_to_tail 缺 decision_cutoff/decision_price_source 冻结拒",
                       _pap(pap_schema_version=2, analysis_type="strategy",
                            strategy_execution={"execution_profile": "preclose_to_tail",
                                                "fill_window": "尾盘", "fill_price_rule": "x",
                                                "slippage_rule": "frozen_cost"}))
        _freeze_reject(cur, "R4 execution_profile 白名单外冻结拒",
                       _pap(pap_schema_version=2, analysis_type="strategy",
                            strategy_execution={"execution_profile": "same_close_exec"}))
        _freeze_reject(cur, "R5 伪称 legacy(pap 带 legacy 字段/自报 registered_at)冻结拒",
                       _pap(legacy=True, registered_at_claim="2026-07-01"))
        cur.execute("SAVEPOINT r6")
        try:
            cur.execute("UPDATE experiment SET pap_json = pap_json || %s::jsonb "
                        "WHERE exp_id=8 AND status='registered'",
                        (json.dumps({"pap_schema_version": 2, "analysis_type": "strategy",
                                     "strategy_execution": SE_C2N}),))
            cur.execute("UPDATE experiment SET status='frozen', frozen_at=now() WHERE exp_id=8")
            cur.execute("ROLLBACK TO SAVEPOINT r6")
            _ok("R6 legacy 升级 schema 后 analysis_type=strategy 冻结拒(legacy 只许事件版)",
                False, "本应被拒却放行")
        except psycopg.Error as err:
            cur.execute("ROLLBACK TO SAVEPOINT r6")
            _ok("R6 legacy 升级 schema 后 analysis_type=strategy 冻结拒(legacy 只许事件版)",
                True, str(err).splitlines()[0][:130])
        cur.execute("SAVEPOINT r7")
        try:
            cur.execute("INSERT INTO pap_legacy_registry (exp_id, status_at_migration, note) "
                        "VALUES (26, 'registered', 'x')")
            cur.execute("ROLLBACK TO SAVEPOINT r7")
            _ok("R7 taosha_app 写 legacy registry 拒(权限验证)", False, "本应被拒却放行")
        except psycopg.Error as err:
            cur.execute("ROLLBACK TO SAVEPOINT r7")
            _ok("R7 taosha_app 写 legacy registry 拒(权限验证)", True,
                str(err).splitlines()[0][:120])

        conn.rollback()
        cur.execute("SELECT count(*) FROM experiment WHERE family=%s", (FAMILY,))
        n1 = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM experiment")
        n2 = cur.fetchone()[0]
        _ok("Z1 回滚后零残留(探针 0 行/台账 25 行)", n1 == 0 and n2 == 25, f"probe={n1} total={n2}")
        conn.rollback()

    # ── 层③: 策略驱动启动校验(子进程实测,exp3=legacy 在册) ──
    p = subprocess.run(
        [sys.executable, "-m", "taosha.harness.run_drawdown_strategy",
         "--exp-id", "3", "--snapshot-id", "1", "--diagnostic", "--reason", "papgate 层③探针"],
        capture_output=True, text=True, timeout=120)
    out = (p.stdout or "") + (p.stderr or "")
    _ok("L1 层③ 策略驱动对 legacy(exp3)一律拒(含 --diagnostic)",
        p.returncode != 0 and "修法#1" in out and "pap_legacy_registry" in out,
        out.strip().splitlines()[-1][:130] if out.strip() else f"rc={p.returncode}")

    failed = [r for r in _results if not r[1]]
    print(f"\n== PAP 硬门自检: {len(_results) - len(failed)}/{len(_results)} PASS ==")
    if failed:
        for name, _, detail in failed:
            print(f"  FAIL: {name} {detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
