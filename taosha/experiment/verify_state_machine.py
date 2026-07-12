"""淘沙 · 台账状态机焊死自检(可信度硬化窗口 ①,常设)。

职责: 以 taosha_app 身份实测台账触发器——反向(a)非法路径全拒 + 正向(b)合法流程全通。
口径依据: docs/hardening-window-order-2026-07-12.md ①(字段变更绑定唯一合法迁移;人拍A=closure_reason 新列)。
验收档: taosha/docs/hardening-item1-statemachine-acceptance-2026-07-12.md。

机制: 全套用例跑在**单事务内 + 逐用例 SAVEPOINT + 末尾整体 ROLLBACK**——append-only
触发器辖不到未提交行,自检对台账零残留(结尾断言 family 探针行数=0)。
⚠ 已知副作用: exp_id 为 GENERATED IDENTITY,序号消耗不随回滚退回,台账 exp_id
出现空洞属正常(PG 固有行为,行存在与否为准),验收档已登记。

运行: 在 aliyun `python -m taosha.experiment.verify_state_machine`(需 TAOSHA_APP_DSN)。
"""
from __future__ import annotations

import os
import sys

import psycopg

FAMILY = "_smtest_statemachine"
PAP = '{"probe": true, "note": "状态机自检探针,事务内回滚不落库"}'
PAP2 = '{"probe": true, "note": "registered 态 PAP 完善探针(内容变更)"}'
RESULT = '{"probe_result": "自检探针 result(回滚不落库)"}'

_results: list[tuple[str, bool, str]] = []


def _ok(name: str, passed: bool, detail: str = "") -> None:
    _results.append((name, passed, detail))
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {name}" + (f" —— {detail}" if detail else ""))


def _reject(cur, name: str, sql: str, params=()) -> None:
    """反向用例: 期望被数据库拒绝(触发器 RAISE 或权限拒)。"""
    cur.execute("SAVEPOINT p")
    try:
        cur.execute(sql, params)
    except psycopg.Error as e:
        cur.execute("ROLLBACK TO SAVEPOINT p")
        _ok(name, True, str(e).splitlines()[0][:120])
        return
    cur.execute("ROLLBACK TO SAVEPOINT p")
    _ok(name, False, "本应被拒却放行")


def _allow(cur, name: str, sql: str, params=()) -> None:
    """正向用例: 期望放行;效果保留在事务内供后续用例走状态链。"""
    cur.execute("SAVEPOINT p")
    try:
        cur.execute(sql, params)
    except psycopg.Error as e:
        cur.execute("ROLLBACK TO SAVEPOINT p")
        _ok(name, False, f"合法操作被误拒: {str(e).splitlines()[0][:120]}")
        return
    cur.execute("RELEASE SAVEPOINT p")
    _ok(name, True)


def _insert_registered(cur, title: str) -> int:
    cur.execute(
        """INSERT INTO experiment (family, family_trial, title, source_type, verdict_power,
                                   contamination_note, pap_json, data_class, crowding_prior)
           VALUES (%s, 0, %s, 'human', 'full', '状态机自检探针行(事务内回滚,不落库)',
                   %s::jsonb, '量价', '低') RETURNING exp_id""",
        (FAMILY, title, PAP))
    return cur.fetchone()[0]


def _catalog_assertions(cur) -> None:
    """结构断言: 四触发器在位 + closure_reason 列存在(005 已 apply)。"""
    cur.execute("""SELECT tgname FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
                   WHERE c.relname='experiment' AND NOT t.tgisinternal ORDER BY tgname""")
    names = {r[0] for r in cur.fetchall()}
    need = {"trg_experiment_biu", "trg_experiment_bu",
            "trg_experiment_no_delete", "trg_experiment_no_truncate"}
    _ok("S1 四触发器在位", need <= names, f"缺 {need - names}" if not need <= names else "")
    cur.execute("""SELECT count(*) FROM information_schema.columns
                   WHERE table_name='experiment' AND column_name='closure_reason'""")
    _ok("S2 closure_reason 列存在(005 已 apply)", cur.fetchone()[0] == 1)


def _suite(cur) -> None:
    # ── 行 A: registered → frozen → running → done 全链 + 各态反向探针 ──
    cur.execute("SAVEPOINT walk_a")
    a = _insert_registered(cur, "[探针A] 全链行")
    _ok("F1 (b) INSERT 登记 registered 放行", True, f"exp_id={a}(回滚后不存在)")

    _reject(cur, "R1 (a) registered 态写 result(无迁移)",
            "UPDATE experiment SET result_json=%s::jsonb WHERE exp_id=%s", (RESULT, a))
    _reject(cur, "R2 (a) registered 态提前写 frozen_at(无迁移)",
            "UPDATE experiment SET frozen_at=now() WHERE exp_id=%s", (a,))
    _reject(cur, "R3 (a) 跳态迁移 registered→running",
            "UPDATE experiment SET status='running' WHERE exp_id=%s", (a,))
    _reject(cur, "R4 (a) 跳态迁移 registered→done(带 result+done_at)",
            "UPDATE experiment SET status='done', result_json=%s::jsonb, done_at=now() WHERE exp_id=%s",
            (RESULT, a))
    _reject(cur, "R5 (a) →closed 缺 closure_reason(完备性)",
            "UPDATE experiment SET status='closed', done_at=now() WHERE exp_id=%s", (a,))
    _reject(cur, "R6 (a) registered 态写 closure_reason(无迁移)",
            "UPDATE experiment SET closure_reason='x' WHERE exp_id=%s", (a,))
    _reject(cur, "R7 (a) 绕态改 done_at(registered 态,无迁移)",
            "UPDATE experiment SET done_at=now() WHERE exp_id=%s", (a,))
    _reject(cur, "R8 (a) 不可变列 title 被改",
            "UPDATE experiment SET title='改名' WHERE exp_id=%s", (a,))
    _reject(cur, "R9 (a) →frozen 缺 frozen_at(完备性)",
            "UPDATE experiment SET status='frozen' WHERE exp_id=%s", (a,))

    _allow(cur, "F2 (b) registered 态 PAP 正常完善(pap_json 可改)",
           "UPDATE experiment SET pap_json=%s::jsonb WHERE exp_id=%s", (PAP2, a))
    _allow(cur, "F3 (b) set_meta 类允许字段不误伤(registered)",
           "UPDATE experiment SET data_class='量价', crowding_prior='中', "
           "contamination_note='探针追记' WHERE exp_id=%s", (a,))
    _allow(cur, "F4 (b) registered→frozen(同置 frozen_at)",
           "UPDATE experiment SET status='frozen', frozen_at=now() WHERE exp_id=%s", (a,))

    _reject(cur, "R10 (a) pap_json 冻结后被改(铁律④)",
            "UPDATE experiment SET pap_json=%s::jsonb WHERE exp_id=%s", (PAP, a))
    _reject(cur, "R11 (a) frozen_at 二次写",
            "UPDATE experiment SET frozen_at=now() WHERE exp_id=%s", (a,))
    _reject(cur, "R12 (a) 跳态迁移 frozen→done",
            "UPDATE experiment SET status='done', result_json=%s::jsonb, done_at=now() WHERE exp_id=%s",
            (RESULT, a))
    _reject(cur, "R13 (a) frozen 态写 result(无迁移)",
            "UPDATE experiment SET result_json=%s::jsonb WHERE exp_id=%s", (RESULT, a))
    _allow(cur, "F5 (b) set_meta 类不误伤(frozen,contamination 追记先例)",
           "UPDATE experiment SET contamination_note='探针追记2' WHERE exp_id=%s", (a,))
    _allow(cur, "F6 (b) frozen→running",
           "UPDATE experiment SET status='running' WHERE exp_id=%s", (a,))

    _reject(cur, "R14 (a) 非法迁移 running→closed",
            "UPDATE experiment SET status='closed', closure_reason='x', done_at=now() WHERE exp_id=%s",
            (a,))
    _reject(cur, "R15 (a) running 态写 result(无迁移)",
            "UPDATE experiment SET result_json=%s::jsonb WHERE exp_id=%s", (RESULT, a))
    _reject(cur, "R16 (a) 绕态改 done_at(running 态,无迁移)",
            "UPDATE experiment SET done_at=now() WHERE exp_id=%s", (a,))
    _reject(cur, "R17 (a) running→done 缺 result(完备性)",
            "UPDATE experiment SET status='done', done_at=now() WHERE exp_id=%s", (a,))
    _allow(cur, "F7 (b) running→done(result+done_at 同置,唯一合法首写)",
           "UPDATE experiment SET status='done', result_json=%s::jsonb, done_at=now() WHERE exp_id=%s",
           (RESULT, a))

    _reject(cur, "R18 (a) done 后逆行 done→running",
            "UPDATE experiment SET status='running' WHERE exp_id=%s", (a,))
    _reject(cur, "R19 (b硬项) 合法完成后 result 拒二次写",
            "UPDATE experiment SET result_json='{\"x\":1}'::jsonb WHERE exp_id=%s", (a,))
    _reject(cur, "R20 (a) done_at 二次写",
            "UPDATE experiment SET done_at=now() WHERE exp_id=%s", (a,))
    _allow(cur, "F8 (b) set_meta 类不误伤(done 终态)",
           "UPDATE experiment SET crowding_prior='低' WHERE exp_id=%s", (a,))

    # ── 行 B: registered→closed;行 C: frozen→closed ──
    b = _insert_registered(cur, "[探针B] 关闭链行")
    _allow(cur, "F9 (b) registered→closed(closure_reason+done_at 同置)",
           "UPDATE experiment SET status='closed', closure_reason='探针关闭原因', done_at=now() "
           "WHERE exp_id=%s", (b,))
    _reject(cur, "R21 (a) closed 后写 result(result 仅随 running→done)",
            "UPDATE experiment SET result_json=%s::jsonb WHERE exp_id=%s", (RESULT, b))
    _reject(cur, "R22 (a) closure_reason 二次写",
            "UPDATE experiment SET closure_reason='改口' WHERE exp_id=%s", (b,))
    _reject(cur, "R23 (a) closed 后逆行 closed→running",
            "UPDATE experiment SET status='running' WHERE exp_id=%s", (b,))

    c = _insert_registered(cur, "[探针C] 冻结后关闭行")
    _allow(cur, "F10a (b) C 行 registered→frozen",
           "UPDATE experiment SET status='frozen', frozen_at=now() WHERE exp_id=%s", (c,))
    _allow(cur, "F10b (b) frozen→closed 走通",
           "UPDATE experiment SET status='closed', closure_reason='探针: 冻结后关闭', done_at=now() "
           "WHERE exp_id=%s", (c,))

    # ── INSERT 出生焊死 ──
    ins = ("INSERT INTO experiment (family, family_trial, title, source_type, verdict_power, "
           "contamination_note, pap_json, data_class, crowding_prior, status{cols}) "
           "VALUES (%s, 0, %s, %s, %s, '探针', %s::jsonb, '量价', '低', %s{vals})")
    _reject(cur, "R24 (a) INSERT 出生即 done 带 result",
            ins.format(cols=", result_json, done_at", vals=", %s::jsonb, now()"),
            (FAMILY, "[探针] 出生done", "human", "full", PAP, "done", RESULT))
    _reject(cur, "R25 (a) INSERT 出生即 running",
            ins.format(cols="", vals=""), (FAMILY, "[探针] 出生running", "human", "full", PAP, "running"))
    _reject(cur, "R26 (a) INSERT 出生即 closed",
            ins.format(cols=", closure_reason, done_at", vals=", 'x', now()"),
            (FAMILY, "[探针] 出生closed", "human", "full", PAP, "closed"))
    _reject(cur, "R27 (a) INSERT registered 带 result_json",
            ins.format(cols=", result_json", vals=", %s::jsonb"),
            (FAMILY, "[探针] 出生带result", "human", "full", PAP, "registered", RESULT))
    _reject(cur, "R28 (a) INSERT registered 带 frozen_at",
            ins.format(cols=", frozen_at", vals=", now()"),
            (FAMILY, "[探针] 出生带frozen_at", "human", "full", PAP, "registered"))
    _reject(cur, "R29 (a) 铁律① llm+full 拒(既有回归)",
            ins.format(cols="", vals=""), (FAMILY, "[探针] llm+full", "llm", "full", PAP, "registered"))

    _reject(cur, "R30 (a) DELETE 拒(append-only/权限双层任一)",
            "DELETE FROM experiment WHERE exp_id=%s", (a,))


def main() -> int:
    dsn = os.environ.get("TAOSHA_APP_DSN")
    if not dsn:
        print("环境无 TAOSHA_APP_DSN(应 source /opt/quant/.env,勿回显)", file=sys.stderr)
        return 2
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            _catalog_assertions(cur)
            _suite(cur)
        conn.rollback()  # 整体回滚: 台账零残留(identity 序号消耗不可回退,exp_id 空洞正常)
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM experiment WHERE family=%s", (FAMILY,))
            n = cur.fetchone()[0]
            _ok("Z1 回滚后探针零残留(family 行数=0)", n == 0, f"n={n}")
        conn.rollback()
    failed = [r for r in _results if not r[1]]
    print(f"\n== 状态机自检: {len(_results) - len(failed)}/{len(_results)} PASS ==")
    if failed:
        for name, _, detail in failed:
            print(f"  FAIL: {name} {detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
