"""淘沙 · manifest 批次血缘一致性自检(外审五项修法 #3,常设)。

职责: 以 taosha_app 身份实测——反向(a)血缘不相容/血缘不可证/缺源锚/越权写 registry 全拒
     + 正向(b)现值向量 manifest 正常生成、带源锚新批次正常落且可入 manifest。
口径依据: docs/postaudit-five-order-2026-07-13.md #3(相容性≠批次号相等;历史批走 registry;
         新批 ingest 起强制源锚)。
验收档: taosha/docs/postaudit-item3-manifest-lineage-acceptance-2026-07-13.md。

机制: 同 verify_state_machine——单事务 + SAVEPOINT + 末尾 ROLLBACK,零残留。
运行: aliyun `python -m taosha.harness.verify_manifest_lineage`(需 TAOSHA_APP_DSN/QBASE_APP_DSN)。
"""
from __future__ import annotations

import os
import sys

import psycopg
from psycopg.types.json import Json

from taosha.experiment import snapshot

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


def main() -> int:
    dsn = os.environ.get("TAOSHA_APP_DSN")
    if not dsn:
        print("环境无 TAOSHA_APP_DSN(应 source /opt/quant/.env,勿回显)", file=sys.stderr)
        return 2
    content = snapshot.collect_content()   # 现值向量(qbase 半经 QBASE_APP_DSN)

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM study_snapshot")
        n_manifest_before = cur.fetchone()[0]

        # ── 结构断言 ──
        cur.execute("""SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
                       WHERE c.relname='batch_lineage_registry' AND NOT t.tgisinternal""")
        _ok("S1 lineage registry 表+焊死触发器在位", cur.fetchone()[0] >= 2)
        cur.execute("""SELECT count(*) FILTER (WHERE lineage_status='verified' AND source_anchor IS NOT NULL),
                              count(*) FROM batch_lineage_registry""")
        nv, nt = cur.fetchone()
        _ok("S2 存量 4 历史批全 verified 且锚非空", (nv, nt) == (4, 4), f"verified={nv}/total={nt}")
        cur.execute("""SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
                       WHERE c.relname IN ('market_batch','pool_b1_batch','pool_b1_return_batch')
                         AND t.tgname LIKE '%%_bi' AND NOT t.tgisinternal""")
        _ok("S3 三派生批次表 BEFORE INSERT 源锚触发器在位", cur.fetchone()[0] == 3)

        # ── 正向 F1: 现值向量 manifest 正常生成(历史批经 registry 可信) ──
        cur.execute("SAVEPOINT f1")
        try:
            cur.execute("INSERT INTO study_snapshot (content, note) VALUES (%s, %s) "
                        "RETURNING snapshot_id, digest",
                        (Json(content), "[修法#3 自检探针] 现值向量,回滚不落库"))
            sid, dg = cur.fetchone()
            cur.execute("RELEASE SAVEPOINT f1")
            import re
            _ok("F1 现值向量 manifest 生成放行(digest 库算 64hex)",
                bool(re.fullmatch(r"[0-9a-f]{64}", dg)), f"snapshot_id={sid}(回滚后不存在)")
        except psycopg.Error as e:
            cur.execute("ROLLBACK TO SAVEPOINT f1")
            _ok("F1 现值向量 manifest 生成放行(digest 库算 64hex)", False,
                str(e).splitlines()[0][:120])

        # ── 正向 F2: 带源锚新批次落库放行,且 manifest 引用它可信(anchor 路径) ──
        cur.execute("SAVEPOINT f2")
        try:
            cur.execute(
                """INSERT INTO market_batch (source,hypothesis,compounding,frozen_digest,
                     holdout_start,view_rows,out_rows,min_date,max_date,pull_time,note,source_anchor)
                   VALUES ('probe','market','continuous','probe','2024-07-01',0,0,
                           '2020-01-01','2020-01-02',now(),'[修法#3 自检探针] 带源锚新批',
                           %s) RETURNING batch_id""",
                (Json({"qbase": content["qbase"]}),))
            new_bid = cur.fetchone()[0]
            c2 = {"qbase": content["qbase"],
                  "taosha": dict(content["taosha"], market_return=new_bid)}
            cur.execute("INSERT INTO study_snapshot (content, note) VALUES (%s, %s)",
                        (Json(c2), "[修法#3 自检探针] 引用带锚新批,回滚不落库"))
            cur.execute("RELEASE SAVEPOINT f2")
            _ok("F2 带源锚新批落库+manifest 引用放行(前向血缘路径)", True,
                f"probe batch_id={new_bid}(回滚后不存在)")
        except psycopg.Error as e:
            cur.execute("ROLLBACK TO SAVEPOINT f2")
            _ok("F2 带源锚新批落库+manifest 引用放行(前向血缘路径)", False,
                str(e).splitlines()[0][:120])

        # ── 反向 ──
        bad1 = {"qbase": content["qbase"],
                "taosha": dict(content["taosha"], pool_b1=999999)}
        _reject(cur, "R1 血缘不相容拒: manifest.pool_b1 ≠ pool_b1_return 批父池批",
                "INSERT INTO study_snapshot (content) VALUES (%s)", (Json(bad1),))
        _reject(cur, "R2 新派生批缺源锚拒(ingest 起强制)",
                "INSERT INTO market_batch (source,hypothesis,compounding,frozen_digest,"
                "holdout_start,view_rows,out_rows,min_date,max_date,pull_time) "
                "VALUES ('probe','market','continuous','probe','2024-07-01',0,0,"
                "'2020-01-01','2020-01-02',now())")
        bad3 = {"qbase": content["qbase"],
                "taosha": dict(content["taosha"], market_return=999999)}
        _reject(cur, "R3 血缘不可证拒: manifest 引用未登记/不存在派生批",
                "INSERT INTO study_snapshot (content) VALUES (%s)", (Json(bad3),))
        _reject(cur, "R4 taosha_app 写 lineage registry 拒(登记=属主专责)",
                "INSERT INTO batch_lineage_registry (batch_table,batch_id,lineage_status,"
                "source_anchor,evidence_ref,approval_ref) "
                "VALUES ('market_batch',999,'verified','{}'::jsonb,'x','x')")
        _reject(cur, "R5 UPDATE registry 拒(append-only/权限双层任一)",
                "UPDATE batch_lineage_registry SET lineage_status='legacy-unverified' "
                "WHERE lineage_id=1")

        conn.rollback()
        cur.execute("SELECT count(*) FROM study_snapshot")
        _ok("Z1 回滚后 manifest 行数不变(存量未扰)", cur.fetchone()[0] == n_manifest_before)
        cur.execute("SELECT count(*) FROM market_batch WHERE source='probe'")
        _ok("Z2 回滚后批次探针零残留", cur.fetchone()[0] == 0)
        conn.rollback()

    failed = [r for r in _results if not r[1]]
    print(f"\n== manifest 血缘自检: {len(_results) - len(failed)}/{len(_results)} PASS ==")
    if failed:
        for name, _, detail in failed:
            print(f"  FAIL: {name} {detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
