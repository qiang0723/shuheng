"""淘沙 · experiment_addendum 审计附属表自检(可信度硬化窗口 ⑤,常设)。

职责: 以 taosha_app 身份实测附属表焊死——INSERT 可、UPDATE/DELETE 全拒、result_json 未被触碰。
口径依据: docs/hardening-window-order-2026-07-12.md ⑤(append-only;原 result_json 一字不动)。
验收档: taosha/docs/hardening-item5-addendum-acceptance-2026-07-12.md。

机制: 同 verify_state_machine——单事务 + SAVEPOINT + 末尾 ROLLBACK,零残留。
运行: aliyun `python -m taosha.experiment.verify_addendum`(需 TAOSHA_APP_DSN)。
"""
from __future__ import annotations

import os
import sys

import psycopg

_results: list[tuple[str, bool, str]] = []


def _ok(name: str, passed: bool, detail: str = "") -> None:
    _results.append((name, passed, detail))
    print(f"[{'PASS' if passed else 'FAIL'}] {name}" + (f" —— {detail}" if detail else ""))


def _reject(cur, name: str, sql: str, params=()) -> None:
    cur.execute("SAVEPOINT p")
    try:
        cur.execute(sql, params)
    except psycopg.Error as e:
        cur.execute("ROLLBACK TO SAVEPOINT p")
        _ok(name, True, str(e).splitlines()[0][:110])
        return
    cur.execute("ROLLBACK TO SAVEPOINT p")
    _ok(name, False, "本应被拒却放行")


def main() -> int:
    dsn = os.environ.get("TAOSHA_APP_DSN")
    if not dsn:
        print("环境无 TAOSHA_APP_DSN", file=sys.stderr)
        return 2
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        # 结构断言: 表 + 两触发器在位
        cur.execute("""SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
                       WHERE c.relname='experiment_addendum' AND NOT t.tgisinternal""")
        _ok("S1 附属表触发器在位(freeze+no_truncate)", cur.fetchone()[0] >= 2)

        # 正向: INSERT 探针(事务内,回滚不落库)
        cur.execute(
            """INSERT INTO experiment_addendum
                 (exp_id, result_sha256, category, body, affects_verdict, approval_ref)
               VALUES (3, 'probe', '_smtest_probe', '自检探针(回滚不落库)', false, 'probe')
               RETURNING addendum_id""")
        aid = cur.fetchone()[0]
        _ok("F1 taosha_app INSERT 附注放行", True, f"addendum_id={aid}(回滚后不存在)")

        # 反向: UPDATE / DELETE 全拒(对探针行与既有行同理)
        _reject(cur, "R1 UPDATE 附注正文拒(append-only)",
                "UPDATE experiment_addendum SET body='改' WHERE addendum_id=%s", (aid,))
        _reject(cur, "R2 UPDATE affects_verdict 拒",
                "UPDATE experiment_addendum SET affects_verdict=true WHERE addendum_id=%s", (aid,))
        _reject(cur, "R3 DELETE 附注拒",
                "DELETE FROM experiment_addendum WHERE addendum_id=%s", (aid,))
        _reject(cur, "R4 外键: exp 不存在拒",
                "INSERT INTO experiment_addendum (exp_id, category, body, affects_verdict, approval_ref) "
                "VALUES (999999, 'x', 'x', false, 'x')")

        # 载荷不动断言: 附注插入前后 exp3/exp5 result_json 摘要不变(同事务读一致性下的结构证)
        cur.execute("""SELECT exp_id, encode(sha256(convert_to(result_json::text,'UTF8')),'hex')
                       FROM experiment WHERE exp_id IN (3,5) ORDER BY exp_id""")
        before = cur.fetchall()
        conn.rollback()
        cur.execute("""SELECT exp_id, encode(sha256(convert_to(result_json::text,'UTF8')),'hex')
                       FROM experiment WHERE exp_id IN (3,5) ORDER BY exp_id""")
        _ok("Z1 原 result_json 一字未动(exp3/5 sha 前后同)", cur.fetchall() == before)
        cur.execute("SELECT count(*) FROM experiment_addendum WHERE category='_smtest_probe'")
        _ok("Z2 回滚后探针零残留", cur.fetchone()[0] == 0)
        conn.rollback()

    failed = [r for r in _results if not r[1]]
    print(f"\n== addendum 自检: {len(_results) - len(failed)}/{len(_results)} PASS ==")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
