"""淘沙 · manifest 批次血缘一致性自检(外审五项修法 #3 + 第二/三轮窄补,常设)。

职责: 以 taosha_app 身份实测——反向(a)血缘不相容/血缘不可证/缺源锚/越权写 registry
     + 窄补二(2026-07-13): 空锚{}/缺关键字段/伪 digest/锚值≠绑定快照/锚≠新 manifest 全拒
     + 窄补三 #3-a/#3-b(2026-07-13): 锚=实际依赖键集合不多不少(全向量多键拒/少键拒)、
       python↔SQL 依赖映射交叉断言、无依赖源刷新不碰派生批相容(manifest 放行)、
       源级快照(仅 qbase 半)生成放行/缺必需键拒/合法再种链探针(源快照→依赖锚批→manifest)
     + 正向(b)现值向量 manifest 正常生成、依赖键锚新批正常落且可入 manifest。
口径依据: docs/postaudit-five-order-2026-07-13.md #3 + docs/postaudit-round2-narrow-order-2026-07-13.md
         + docs/postaudit-round3-narrow-order-2026-07-13.md(#3-a 依赖键映射/#3-b 合法再种)。
注记(窄补三): 存量 4 registry verified 锚=全向量式**历史事实**(当时确实读了整个快照),
         不改写;manifest 双检只查所引批次的锚,#3-b 真实再种后最新批换代为依赖键锚。
验收档: taosha/docs/postaudit-round3-narrow-acceptance-2026-07-13.md(承前两轮)。

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

        # ── 正向 F1(窄补三改判): 一致读向量 manifest 正常生成——qbase 半=最新派生批绑定源
        #   快照之向量(锚定源=引擎一致读;~~恒用现值向量~~作废: E2E 后无关新源批并发落地时
        #   现值口径与派生批锚不相容被正确拒,见 create(from_source_snapshot)) ──
        cur.execute("""SELECT coalesce(b.source_anchor, r.source_anchor)
                       FROM pool_b1_return_batch b
                       LEFT JOIN batch_lineage_registry r
                         ON r.batch_table='pool_b1_return_batch' AND r.batch_id=b.batch_id
                        AND r.lineage_status='verified'
                       ORDER BY b.batch_id DESC LIMIT 1""")
        latest_anchor = cur.fetchone()[0]
        cur.execute("SELECT content->'qbase' FROM study_snapshot WHERE snapshot_id=%s",
                    (int(latest_anchor["source_manifest"]["snapshot_id"]),))
        bound_qbase = cur.fetchone()[0]
        coherent = {"qbase": bound_qbase, "taosha": content["taosha"]}
        cur.execute("SAVEPOINT f1")
        try:
            cur.execute("INSERT INTO study_snapshot (content, note) VALUES (%s, %s) "
                        "RETURNING snapshot_id, digest",
                        (Json(coherent), "[修法#3 自检探针] 一致读向量,回滚不落库"))
            sid, dg = cur.fetchone()
            cur.execute("RELEASE SAVEPOINT f1")
            import re
            _ok("F1 一致读向量 manifest 生成放行(qbase 半=最新批绑定源快照;digest 库算 64hex)",
                bool(re.fullmatch(r"[0-9a-f]{64}", dg)), f"snapshot_id={sid}(回滚后不存在)")
        except psycopg.Error as e:
            cur.execute("ROLLBACK TO SAVEPOINT f1")
            _ok("F1 一致读向量 manifest 生成放行(qbase 半=最新批绑定源快照;digest 库算 64hex)",
                False, str(e).splitlines()[0][:120])

        # ── 参照 manifest(锚绑定用): #1=存量已发布快照(digest 2a8a271f…在案) ──
        cur.execute("SELECT snapshot_id, digest, content FROM study_snapshot WHERE snapshot_id=1")
        ref_sid, ref_digest, ref_content = cur.fetchone()

        # ── 窄补三 T1: python↔SQL 依赖键映射逐键交叉断言(口径唯一,两权威镜像一致) ──
        dep_ok = True
        dep_detail = []
        for tbl, py_deps in sorted(snapshot.DERIVED_BATCH_QBASE_DEPS.items()):
            cur.execute("SELECT public._derived_qbase_deps(%s)", (tbl,))
            sql_deps = cur.fetchone()[0]
            same = sorted(py_deps) == sorted(sql_deps or [])
            dep_ok &= same
            dep_detail.append(f"{tbl}:{'==' if same else '≠'}")
        _ok("T1 依赖键映射 python(snapshot)==SQL(_derived_qbase_deps) 三表逐键一致",
            dep_ok, " ".join(dep_detail))

        def _dep_anchor(tbl: str = "market_batch", **extra) -> dict:
            """窄补三合法锚: 实际依赖键集合(不多不少)+ source_manifest{id,digest}。"""
            a = {"qbase": snapshot.anchor_qbase_deps(tbl, ref_content["qbase"]),
                 "source_manifest": {"snapshot_id": ref_sid, "digest": ref_digest}}
            a.update(extra)
            return a

        _batch_ins = (
            "INSERT INTO market_batch (source,hypothesis,compounding,frozen_digest,"
            "holdout_start,view_rows,out_rows,min_date,max_date,pull_time,note,source_anchor) "
            "VALUES ('probe','market','continuous','probe','2024-07-01',0,0,"
            "'2020-01-01','2020-01-02',now(),%s,%s) RETURNING batch_id")

        _pool_ins = (
            "INSERT INTO pool_b1_batch (source,frozen_digest,amount_window,listing_min,"
            "top_fraction,holdout_start,min_date,max_date,n_dates,out_rows,avg_pool_size,"
            "pull_time,note,source_anchor) VALUES ('probe','probe',20,120,0.2,'2024-07-01',"
            "'2020-01-01','2020-01-02',0,0,0,now(),%s,%s) RETURNING batch_id")
        _pret_ins = (
            "INSERT INTO pool_b1_return_batch (source,pool_batch_id,compounding,frozen_digest,"
            "holdout_start,view_rows,out_rows,min_date,max_date,avg_n_stocks,pull_time,note,"
            "source_anchor) VALUES ('probe',%s,'continuous','probe','2024-07-01',0,0,"
            "'2020-01-01','2020-01-02',0,now(),%s,%s) RETURNING batch_id")

        def _seed_three_probes(bind_sid, bind_dg, vec, tag):
            """三批依赖键锚探针(绑定 snapshot bind_sid;vec=其 qbase 向量)→ (mr, p, pr)。"""
            def _a(tbl, **extra):
                a = {"qbase": snapshot.anchor_qbase_deps(tbl, vec),
                     "source_manifest": {"snapshot_id": bind_sid, "digest": bind_dg}}
                a.update(extra)
                return a
            cur.execute(_batch_ins, (f"[{tag}] 再种market", Json(_a("market_batch"))))
            mr = cur.fetchone()[0]
            cur.execute(_pool_ins, (f"[{tag}] 再种pool", Json(_a("pool_b1_batch"))))
            p = cur.fetchone()[0]
            cur.execute(_pret_ins, (p, f"[{tag}] 再种pool_return",
                                    Json(_a("pool_b1_return_batch",
                                            taosha_parent={"pool_b1": p}))))
            pr = cur.fetchone()[0]
            return mr, p, pr

        # ── 正向 F2(窄补三改判×2): 依赖键锚新批落库放行,且 manifest 引用它可信。
        #   三批全探针+参照快照向量(~~混用现值 taosha 半~~作废: E2E 后存量最新批绑定源≠
        #   参照#1,混引正确拒;探针自洽=测"依赖键锚批可落可入 manifest"本义)──
        cur.execute("SAVEPOINT f2")
        try:
            mr2, p2, pr2 = _seed_three_probes(ref_sid, ref_digest, ref_content["qbase"], "修法#3F2")
            c2 = {"qbase": ref_content["qbase"],
                  "taosha": {"market_return": mr2, "pool_b1": p2, "pool_b1_return": pr2}}
            cur.execute("INSERT INTO study_snapshot (content, note) VALUES (%s, %s)",
                        (Json(c2), "[修法#3 自检探针] 引用带锚新批,回滚不落库"))
            cur.execute("ROLLBACK TO SAVEPOINT f2")
            _ok("F2 依赖键锚新批落库+manifest 引用放行(前向血缘路径;窄补三改判)", True,
                f"probe batches=({mr2},{p2},{pr2})(回滚后不存在)")
        except psycopg.Error as e:
            cur.execute("ROLLBACK TO SAVEPOINT f2")
            _ok("F2 依赖键锚新批落库+manifest 引用放行(前向血缘路径;窄补三改判)", False,
                str(e).splitlines()[0][:120])

        # ── 窄补三 F5(#3-a 验收点): 无依赖源刷新不碰派生批相容——manifest 只比对实际依赖键。
        #   三批全为依赖键锚探针(绑 snapshot#1;存量批 registry 全向量历史锚会正确拒=换代前
        #   实况,#3-b 真实再种后换代);manifest 向量 stk_holdertrade 值改动 → 放行。──
        cur.execute("SAVEPOINT f5")
        try:
            mr5, p5, pr5 = _seed_three_probes(ref_sid, ref_digest, ref_content["qbase"], "窄补三F5")
            c5 = {"qbase": dict(ref_content["qbase"], stk_holdertrade=999999),
                  "taosha": {"market_return": mr5, "pool_b1": p5, "pool_b1_return": pr5}}
            cur.execute("INSERT INTO study_snapshot (content, note) VALUES (%s, %s)",
                        (Json(c5), "[窄补三F5] 无依赖源(stk_holdertrade)刷新,应放行"))
            cur.execute("ROLLBACK TO SAVEPOINT f5")
            _ok("F5 无依赖源(stk_holdertrade)刷新→manifest 放行(#3-a: 只比对实际依赖键)", True,
                "三批锚均不含 stk_holdertrade → 其批次号变动与相容性无关")
        except psycopg.Error as e:
            cur.execute("ROLLBACK TO SAVEPOINT f5")
            _ok("F5 无依赖源(stk_holdertrade)刷新→manifest 放行(#3-a: 只比对实际依赖键)", False,
                str(e).splitlines()[0][:130])

        # ── 窄补三 F6(#3-b 结构探针): 源级快照生成放行 + 合法再种链全通路(事务内静态半;
        #   真实端到端+并发=E2E 实测另录验收档,本探针证触发器通路)。trade_cal 为三批共同
        #   依赖 → 三批全再种(只种一批则其余批 registry 锚与新向量不相容=正确拒,F7 反证)──
        cur.execute("SAVEPOINT f6")
        try:
            src_c = {"qbase": dict(ref_content["qbase"], trade_cal=999999)}   # 模拟源刷新后向量
            cur.execute("INSERT INTO study_snapshot (content, note) VALUES (%s, %s) "
                        "RETURNING snapshot_id, digest",
                        (Json(src_c), "[窄补三探针] 源级快照(仅 qbase 半),回滚不落库"))
            src_sid, src_dg = cur.fetchone()
            import re as _re
            ok_src = bool(_re.fullmatch(r"[0-9a-f]{64}", src_dg))
            b6_mr, b6_p, b6_pr = _seed_three_probes(src_sid, src_dg, src_c["qbase"], "窄补三F6")
            c6 = {"qbase": src_c["qbase"],
                  "taosha": {"market_return": b6_mr, "pool_b1": b6_p, "pool_b1_return": b6_pr}}
            cur.execute("INSERT INTO study_snapshot (content, note) VALUES (%s, %s)",
                        (Json(c6), "[窄补三F6] 三批再种后研究 manifest,应放行"))
            cur.execute("ROLLBACK TO SAVEPOINT f6")
            _ok("F6 合法再种链通路: 源级快照(digest 库算)→三批依赖锚绑之→研究 manifest 放行(#3-b)",
                ok_src, f"src={src_sid} batches=({b6_mr},{b6_p},{b6_pr})(回滚后不存在)")
        except psycopg.Error as e:
            cur.execute("ROLLBACK TO SAVEPOINT f6")
            _ok("F6 合法再种链通路: 源级快照(digest 库算)→三批依赖锚绑之→研究 manifest 放行(#3-b)",
                False, str(e).splitlines()[0][:130])

        # ── 窄补三 F7(反证=fail-closed 未弱化): 源刷新后只种一批,研究 manifest 仍拒 ──
        cur.execute("SAVEPOINT f7")
        try:
            src_c7 = {"qbase": dict(ref_content["qbase"], trade_cal=888888)}
            cur.execute("INSERT INTO study_snapshot (content, note) VALUES (%s, %s) "
                        "RETURNING snapshot_id, digest",
                        (Json(src_c7), "[窄补三探针] 源级快照,回滚不落库"))
            s7, d7 = cur.fetchone()
            a7 = {"qbase": snapshot.anchor_qbase_deps("market_batch", src_c7["qbase"]),
                  "source_manifest": {"snapshot_id": s7, "digest": d7}}
            cur.execute(_batch_ins, ("[窄补三探针] 只再种market", Json(a7)))
            b7 = cur.fetchone()[0]
            c7 = {"qbase": src_c7["qbase"],
                  "taosha": dict(content["taosha"], market_return=b7)}   # pool 两批未再种
            cur.execute("INSERT INTO study_snapshot (content, note) VALUES (%s, %s)",
                        (Json(c7), "[窄补三探针] 池批未再种,应拒"))
            cur.execute("ROLLBACK TO SAVEPOINT f7")
            _ok("F7 反证: 源刷新后池批未再种→研究 manifest 拒(fail-closed 未弱化)", False,
                "本应被拒却放行")
        except psycopg.Error as e:
            cur.execute("ROLLBACK TO SAVEPOINT f7")
            _ok("F7 反证: 源刷新后池批未再种→研究 manifest 拒(fail-closed 未弱化)",
                "不相容" in str(e), str(e).splitlines()[0][:130])

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
                             Json(_dep_anchor(source_manifest={"snapshot_id": ref_sid,
                                                               "digest": "a" * 64}))))
        _reject(cur, "R9 锚依赖键值≠所绑定快照向量值拒(锚必须=实际所读快照之依赖键值)",
                _batch_ins, ("[窄补探针] 锚值偏移",
                             Json(_dep_anchor(qbase=dict(
                                 snapshot.anchor_qbase_deps("market_batch", ref_content["qbase"]),
                                 daily=999999)))))
        # ── 窄补三 #3-a 反向: 键集合不多不少 ──
        _reject(cur, "R11 全向量锚(含无依赖键 forecast/stk_holdertrade)拒(窄补三: 多键=过锚)",
                _batch_ins, ("[窄补三探针] 全向量锚",
                             Json({"qbase": ref_content["qbase"],
                                   "source_manifest": {"snapshot_id": ref_sid,
                                                       "digest": ref_digest}})))
        _r12_q = snapshot.anchor_qbase_deps("market_batch", ref_content["qbase"])
        _r12_q.pop("trade_cal")
        _reject(cur, "R12 少键锚(缺依赖键 trade_cal)拒(窄补三: 少键=依赖不可证)",
                _batch_ins, ("[窄补三探针] 少键锚", Json(_dep_anchor(qbase=_r12_q))))
        _r13_q = dict(ref_content["qbase"])
        _r13_q.pop("forecast")
        _reject(cur, "R13 源级快照缺必需键(forecast)拒(窄补三 #3-b: REQUIRED 六键 fail-closed)",
                "INSERT INTO study_snapshot (content, note) VALUES (%s, %s)",
                (Json({"qbase": _r13_q}), "[窄补三探针] 缺键源级快照,应拒"))
        # R10(窄补反向测试④): 锚合法在位,但新 manifest 的 qbase 向量与锚不匹配 → 生成拒
        cur.execute("SAVEPOINT r10")
        try:
            cur.execute(_batch_ins, ("[窄补探针] 合法锚批,用于不相容manifest", Json(_dep_anchor())))
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
