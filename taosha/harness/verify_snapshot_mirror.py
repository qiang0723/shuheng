"""淘沙 · qbase 快照路由防伪自检(外审五项修法 #2,常设)。

职责: 实测权威镜像+发布凭证机制——
  受权角色侧(qbase_app): 镜像 digest 库算权威/半成品不可消费/两库 digest 不一致拒发布/
  镜像缺失拒发布/append-only;两库 canonical digest 同式=实测向量验证(跨库);
  引擎侧(taosha_engine): 已授权且 digest 一致的 snapshot 正常读取(正向控制)。
  (引擎零写权/伪造 JSON 失效/不存在 id 拒 → 见 verify_study_snapshot --mode probes P-q3..P-q6。)
口径依据: docs/postaudit-five-order-2026-07-13.md #2。
验收档: taosha/docs/postaudit-item2-snapshot-mirror-acceptance-2026-07-13.md。

机制: 反向用例走单事务+SAVEPOINT+ROLLBACK,零残留(半成品审计行仅事务内构造)。
运行: aliyun `python -m taosha.harness.verify_snapshot_mirror`
     (需 QBASE_APP_DSN / TAOSHA_APP_DSN / TAOSHA_ENGINE_QBASE_DSN)。
"""
from __future__ import annotations

import json
import os
import sys

import psycopg

TEST_VECTOR = {"qbase": {"probe_a": 1}, "taosha": {"probe_b": 2}}   # 两库 digest 同式实测向量

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
        _ok(name, True, str(e).splitlines()[0][:120])
        return
    cur.execute("ROLLBACK TO SAVEPOINT p")
    _ok(name, False, "本应被拒却放行")


def _dsn(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"环境无 {name}(应 source /opt/quant/.env,勿回显)")
    return v


def main() -> int:
    qdsn, tdsn = _dsn("QBASE_APP_DSN"), _dsn("TAOSHA_APP_DSN")
    edsn = _dsn("TAOSHA_ENGINE_QBASE_DSN")
    vec_text = json.dumps(TEST_VECTOR, sort_keys=True)

    # taosha 侧同式计算(实测向量的跨库参照值)
    with psycopg.connect(tdsn) as tc, tc.cursor() as cur:
        cur.execute("SELECT encode(sha256(convert_to(%s::jsonb::text,'UTF8')),'hex')", (vec_text,))
        t_vec_digest = cur.fetchone()[0]

    with psycopg.connect(qdsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM study_snapshot_mirror")
        n_mirror_before = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM study_snapshot_publication")
        n_pub_before = cur.fetchone()[0]

        # ── 结构 + 存量发布断言 ──
        cur.execute("""SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
                       WHERE c.relname IN ('study_snapshot_mirror','study_snapshot_publication')
                         AND NOT t.tgisinternal""")
        _ok("S1 镜像+凭证两表触发器在位(bi/freeze/no_truncate)", cur.fetchone()[0] >= 6)
        cur.execute("""SELECT m.snapshot_id, m.digest,
                              EXISTS (SELECT 1 FROM study_snapshot_publication p
                                      WHERE p.snapshot_id=m.snapshot_id
                                        AND p.attested_digest=m.digest)
                       FROM study_snapshot_mirror m ORDER BY m.snapshot_id""")
        rows = cur.fetchall()
        want = {1: "2a8a271f", 2: "f660d76b"}
        got_ok = (len(rows) >= 2 and
                  all(r[1].startswith(want[r[0]]) and r[2] for r in rows if r[0] in want))
        _ok("S2 存量 manifest#1/#2 镜像已回填且已 attested(digest==taosha 在案值)", got_ok,
            "; ".join(f"id={r[0]} {r[1][:8]} attested={r[2]}" for r in rows))

        # ── V1 两库 canonical digest 同式(实测向量,跨库) ──
        cur.execute("SAVEPOINT v1")
        try:
            cur.execute("INSERT INTO study_snapshot_mirror (snapshot_id, content) "
                        "VALUES (999996, %s::jsonb) RETURNING digest", (vec_text,))
            q_vec_digest = cur.fetchone()[0]
            cur.execute("ROLLBACK TO SAVEPOINT v1")
            _ok("V1 两库 canonical digest 同式(实测向量: qbase 镜像库算==taosha 同式)",
                q_vec_digest == t_vec_digest, f"{q_vec_digest[:16]}…(回滚不落库)")
        except psycopg.Error as e:
            cur.execute("ROLLBACK TO SAVEPOINT v1")
            _ok("V1 两库 canonical digest 同式(实测向量)", False, str(e).splitlines()[0][:120])

        # ── R1 半成品不可消费: 仅镜像无凭证 → 路由拒(同事务内构造,回滚即弃=审计语义) ──
        cur.execute("SAVEPOINT r1")
        try:
            cur.execute("INSERT INTO study_snapshot_mirror (snapshot_id, content) "
                        "VALUES (999995, %s::jsonb)", (vec_text,))
            cur.execute("SELECT set_config('shuheng.study_snapshot_id','999995', true)")
            cur.execute("SELECT count(*) FROM explore_reader_calendar_snap")
            cur.execute("ROLLBACK TO SAVEPOINT r1")
            _ok("R1 半成品(有镜像无凭证)不可消费", False, "本应被拒却放行")
        except psycopg.Error as e:
            cur.execute("ROLLBACK TO SAVEPOINT r1")
            _ok("R1 半成品(有镜像无凭证)不可消费", True, str(e).splitlines()[0][:120])

        # ── R2 两库 digest 不一致拒发布(镜像库算 ≠ 证词) ──
        cur.execute("SAVEPOINT r2")
        cur.execute("INSERT INTO study_snapshot_mirror (snapshot_id, content) "
                    "VALUES (999994, %s::jsonb)", (vec_text,))
        _reject(cur, "R2 两库 digest 不一致拒发布(伪证词 0×64)",
                "INSERT INTO study_snapshot_publication (snapshot_id, attested_digest) "
                "VALUES (999994, repeat('0',64))")
        cur.execute("ROLLBACK TO SAVEPOINT r2")

        _reject(cur, "R3 镜像缺失拒发布",
                "INSERT INTO study_snapshot_publication (snapshot_id, attested_digest) "
                "VALUES (999993, repeat('0',64))")
        _reject(cur, "R4 UPDATE 镜像拒(append-only)",
                "UPDATE study_snapshot_mirror SET content='{}'::jsonb WHERE snapshot_id=1")
        _reject(cur, "R5 UPDATE 凭证拒(append-only)",
                "UPDATE study_snapshot_publication SET attested_digest=repeat('0',64) "
                "WHERE snapshot_id=1")

        conn.rollback()
        cur.execute("SELECT count(*) FROM study_snapshot_mirror")
        _ok("Z1 回滚后镜像行数不变", cur.fetchone()[0] == n_mirror_before)
        cur.execute("SELECT count(*) FROM study_snapshot_publication")
        _ok("Z2 回滚后凭证行数不变", cur.fetchone()[0] == n_pub_before)
        conn.rollback()

    # ── F1 正向: 引擎身份 + 已发布 snapshot=1 正常读取 ──
    with psycopg.connect(edsn) as ec, ec.cursor() as cur:
        cur.execute("SELECT set_config('shuheng.study_snapshot_id','1', false)")
        cur.execute("SELECT count(*) FROM explore_reader_calendar_snap")
        n = cur.fetchone()[0]
        _ok("F1 引擎读已授权且 digest 一致的 snapshot=1 放行(正向控制)", n > 0, f"calendar 行数={n}")
        ec.rollback()

    failed = [r for r in _results if not r[1]]
    print(f"\n== 快照镜像自检: {len(_results) - len(failed)}/{len(_results)} PASS ==")
    if failed:
        for name, _, detail in failed:
            print(f"  FAIL: {name} {detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
