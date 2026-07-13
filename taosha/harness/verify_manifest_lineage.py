"""淘沙 · manifest 批次血缘一致性自检(外审五项修法 #3 + 第二轮窄补,常设)。

职责: 以 taosha_app 身份实测——反向(a)血缘不相容/血缘不可证/缺源锚/越权写 registry
     + 窄补(2026-07-13): 空锚{}/缺关键字段/伪 digest/锚向量≠绑定 manifest/锚向量≠新 manifest
     全拒 + 正向(b)现值向量 manifest 正常生成、严格 schema 锚新批次正常落且可入 manifest。
口径依据: docs/postaudit-five-order-2026-07-13.md #3 + docs/postaudit-round2-narrow-order-2026-07-13.md
         (严格 schema 拒 {} 及缺关键字段;manifest 生成比对派生批 qbase 向量,不相容拒,非仅非 NULL)。
验收档: taosha/docs/postaudit-round2-narrow-acceptance-2026-07-13.md(承 postaudit-item3)。

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

        # ── 参照 manifest(锚绑定用): #1=存量已发布快照(digest 2a8a271f…在案) ──
        cur.execute("SELECT snapshot_id, digest, content FROM study_snapshot WHERE snapshot_id=1")
        ref_sid, ref_digest, ref_content = cur.fetchone()

        def _anchor(**extra) -> dict:
            """严格 schema 合法锚(窄补): 所读快照 qbase 向量 + source_manifest{id,digest}。"""
            a = {"qbase": ref_content["qbase"],
                 "source_manifest": {"snapshot_id": ref_sid, "digest": ref_digest}}
            a.update(extra)
            return a

        _batch_ins = (
            "INSERT INTO market_batch (source,hypothesis,compounding,frozen_digest,"
            "holdout_start,view_rows,out_rows,min_date,max_date,pull_time,note,source_anchor) "
            "VALUES ('probe','market','continuous','probe','2024-07-01',0,0,"
            "'2020-01-01','2020-01-02',now(),%s,%s) RETURNING batch_id")

        # ── 正向 F2: 严格 schema 锚新批落库放行,且 manifest 引用它可信(anchor 路径) ──
        cur.execute("SAVEPOINT f2")
        try:
            cur.execute(_batch_ins, ("[修法#3 自检探针] 严格schema锚新批", Json(_anchor())))
            new_bid = cur.fetchone()[0]
            c2 = {"qbase": ref_content["qbase"],
                  "taosha": dict(content["taosha"], market_return=new_bid)}
            cur.execute("INSERT INTO study_snapshot (content, note) VALUES (%s, %s)",
                        (Json(c2), "[修法#3 自检探针] 引用带锚新批,回滚不落库"))
            cur.execute("RELEASE SAVEPOINT f2")
            _ok("F2 严格schema锚新批落库+manifest 引用放行(前向血缘路径)", True,
                f"probe batch_id={new_bid}(回滚后不存在)")
        except psycopg.Error as e:
            cur.execute("ROLLBACK TO SAVEPOINT f2")
            _ok("F2 严格schema锚新批落库+manifest 引用放行(前向血缘路径)", False,
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

        # ── 窄补(外审第二轮 2026-07-13): 严格 schema + 血缘真相容 ──
        _reject(cur, "R6 空锚 source_anchor={} 批次 INSERT 拒(窄补反向测试③,严格 schema)",
                _batch_ins, ("[窄补探针] 空锚", Json({})))
        _reject(cur, "R7 缺关键字段锚拒(有 qbase 无 source_manifest)",
                _batch_ins, ("[窄补探针] 缺source_manifest", Json({"qbase": ref_content["qbase"]})))
        _reject(cur, "R8 伪 digest 锚拒(source_manifest.digest 与 manifest 库内不一致)",
                _batch_ins, ("[窄补探针] 伪digest",
                             Json(_anchor(source_manifest={"snapshot_id": ref_sid,
                                                           "digest": "a" * 64}))))
        _reject(cur, "R9 锚 qbase 向量≠所绑定 manifest 的 qbase 半拒(锚必须=实际所读快照向量)",
                _batch_ins, ("[窄补探针] 锚向量偏移",
                             Json(_anchor(qbase=dict(ref_content["qbase"], daily=999999)))))
        # R10(窄补反向测试④): 锚合法在位,但新 manifest 的 qbase 向量与锚不匹配 → 生成拒
        cur.execute("SAVEPOINT r10")
        try:
            cur.execute(_batch_ins, ("[窄补探针] 合法锚批,用于不相容manifest", Json(_anchor())))
            r10_bid = cur.fetchone()[0]
            c3 = {"qbase": dict(ref_content["qbase"], daily=999999),
                  "taosha": dict(content["taosha"], market_return=r10_bid)}
            cur.execute("INSERT INTO study_snapshot (content, note) VALUES (%s, %s)",
                        (Json(c3), "[窄补探针] 向量与锚不相容,应被拒"))
            cur.execute("ROLLBACK TO SAVEPOINT r10")
            _ok("R10 锚在位但与 manifest qbase 向量不匹配→生成拒(窄补反向测试④,非仅非NULL)",
                False, "本应被拒却放行")
        except psycopg.Error as e:
            cur.execute("ROLLBACK TO SAVEPOINT r10")
            _ok("R10 锚在位但与 manifest qbase 向量不匹配→生成拒(窄补反向测试④,非仅非NULL)",
                "不相容" in str(e), str(e).splitlines()[0][:130])

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
