"""淘沙 · StudySnapshot manifest 生成/查看(可信度硬化窗口 ②)。

职责: 由受权角色(taosha_app 写 + qbase_app 读批次表,**非 taosha_engine**)在研究启动时生成
一次性不可变 snapshot manifest(qbase 各源批次向量 + taosha 派生批次),digest 由库触发器权威计算。
口径依据: docs/hardening-window-order-2026-07-12.md ②(fail-closed,禁静默回退 *_current)。
验收档: taosha/docs/hardening-item2-studysnapshot-acceptance-2026-07-12.md。

用法(aliyun):
  set -a; . /opt/quant/.env; set +a
  python -m taosha.experiment.snapshot --create [--note "..."]   # 生成并打印 snapshot_id + digest
  python -m taosha.experiment.snapshot --show N | --latest
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import psycopg
from psycopg.types.json import Json

# 引擎侧视图消费所需的最小键集(qbase 侧;缺任一 → 拒生成,fail-closed 在源头)
REQUIRED_QBASE = {"stock_basic", "namechange", "trade_cal", "daily", "adj_factor", "forecast"}
REQUIRED_TAOSHA = {"market_return", "pool_b1", "pool_b1_return"}

# ── 窄补第三轮 #3-a(2026-07-13): 各派生批次 → 实际 qbase 依赖键映射(不多不少) ──────
# 依据=各 seed 实际读径(逐件核对留档验收档):
#   · market_batch:        explore_reader_prices_snap(daily+adj_factor+stock_basic+namechange)
#                          + explore_reader_calendar_snap(trade_cal)
#   · pool_b1_batch:       bar_daily_snap.amount(daily,原始额不复权)+ entity_master 上市界
#                          (stock_basic)+ explore_reader_calendar_snap(trade_cal)
#                          ——不读 adj_factor/namechange
#   · pool_b1_return_batch: explore_reader_prices_snap+calendar_snap(同 market)+taosha 父池批
#                          (taosha_parent 另锚,非 qbase 键)
# forecast / stk_holdertrade 等与三派生批无依赖 → 不入锚(其刷新不应使派生批"不相容")。
# SQL 权威镜像 = taosha 014 _derived_qbase_deps();本表与之逐键交叉断言(verify_manifest_lineage)。
DERIVED_BATCH_QBASE_DEPS = {
    "market_batch": ("adj_factor", "daily", "namechange", "stock_basic", "trade_cal"),
    "pool_b1_batch": ("daily", "stock_basic", "trade_cal"),
    "pool_b1_return_batch": ("adj_factor", "daily", "namechange", "stock_basic", "trade_cal"),
}


def anchor_qbase_deps(batch_table: str, snap_qbase: dict) -> dict:
    """窄补第三轮 #3-a: 从所读快照 qbase 向量中提取该派生批**实际依赖键集合**作锚(不多不少)。
    快照缺依赖键 → fail-closed(不默认不猜)。"""
    deps = DERIVED_BATCH_QBASE_DEPS.get(batch_table)
    if deps is None:
        raise RuntimeError(f"未知派生批次表 {batch_table!r}(依赖映射未登记,不默认不猜)")
    missing = [k for k in deps if k not in snap_qbase]
    if missing:
        raise RuntimeError(f"所绑定快照 qbase 向量缺 {batch_table} 依赖键 {missing}(fail-closed)")
    return {k: int(snap_qbase[k]) for k in deps}


def _dsn(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"环境无 {name}(应 source /opt/quant/.env,勿回显)")
    return v


def _short_key(source: str, seen: dict) -> str:
    """批次源名 → 短键('tushare:daily'→'daily');撞键退回全名(忠实不合并)。"""
    key = source.split(":", 1)[1] if ":" in source else source
    return source if key in seen else key


def collect_qbase_vector(cur) -> dict:
    """qbase 源批次向量(entity_batch/fact_batch 各 source 现值 max;开放 qbase 游标传入)。
    修法#3 复用点: 三个派生批次 seed 落批时以此为 source_anchor 的 qbase 半(锚=实际所读现值向量)。"""
    vec: dict = {}
    for tbl in ("entity_batch", "fact_batch"):
        cur.execute(f"SELECT source, max(batch_id) FROM {tbl} GROUP BY source ORDER BY source")
        for source, mx in cur.fetchall():
            vec[_short_key(source, vec)] = int(mx)
    return vec


def collect_content() -> dict:
    """读两库批次表现值,产批次向量(受权角色;拒 taosha_engine)。"""
    content: dict = {"qbase": {}, "taosha": {}}
    with psycopg.connect(_dsn("QBASE_APP_DSN")) as qc, qc.cursor() as cur:
        cur.execute("SELECT current_user")
        assert cur.fetchone()[0] != "taosha_engine", "生成角色不得为 taosha_engine(硬化②)"
        content["qbase"] = collect_qbase_vector(cur)
    with psycopg.connect(_dsn("TAOSHA_APP_DSN")) as tc, tc.cursor() as cur:
        for key, tbl in (("market_return", "market_batch"), ("pool_b1", "pool_b1_batch"),
                         ("pool_b1_return", "pool_b1_return_batch")):
            cur.execute(f"SELECT max(batch_id) FROM {tbl}")
            mx = cur.fetchone()[0]
            if mx is not None:
                content["taosha"][key] = int(mx)
    missing = (REQUIRED_QBASE - set(content["qbase"])) | (REQUIRED_TAOSHA - set(content["taosha"]))
    if missing:
        raise RuntimeError(f"批次向量缺必需键 {sorted(missing)}:先补齐源批次再生成 manifest")
    return content


def create(note: str | None = None,
           from_source_snapshot: int | None = None) -> tuple[int, str, dict]:
    """生成**研究 manifest**(两半向量;单事务;digest 由库触发器权威计算)+ 发布到 qbase
    (修法#2 流程①→②③)。返回 (snapshot_id, digest, content)。

    from_source_snapshot(窄补第三轮 #3-b,E2E 并发实测揪出): qbase 半改自**已发布源级快照**
    N 的向量(fail-closed 经 read_published_snapshot),taosha 半仍取派生批现值——再种链收口时
    若有无关新源批并发落地(现值向量已前移),现值口径 manifest 与派生批锚(=快照向量)不相容
    被正确拒;研究 manifest 的 qbase 半本义=派生数据实际所出之源向量,锚定源快照方为一致读
    (引擎经 manifest 路由读到的 qbase 批 == 派生批当时所读)。None=两半均现值(源无刷新时两者同)。"""
    content = collect_content()
    if from_source_snapshot is not None:
        with psycopg.connect(_dsn("QBASE_APP_DSN")) as qc, qc.cursor() as cur:
            snap_content, _ = read_published_snapshot(cur, from_source_snapshot)
        content["qbase"] = snap_content["qbase"]
    with psycopg.connect(_dsn("TAOSHA_APP_DSN")) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO study_snapshot (content, note) VALUES (%s, %s) "
            "RETURNING snapshot_id, digest", (Json(content), note))
        sid, digest = cur.fetchone()
        conn.commit()
    publish(sid)
    return sid, digest, content


def create_source(note: str | None = None) -> tuple[int, str, dict]:
    """窄补第三轮 #3-b(2026-07-13): 生成**源级快照**(content 仅 qbase 半)并发布。

    用途=合法再种链条第一环: qbase 既有源刷新后,研究 manifest 因旧派生批不相容而拒生成
    (013 fail-closed,正确),但三 seed 又必须绑定已发布快照 → 源级快照先行发布打断循环:
      刷新源 → create_source(新 qbase 向量) → 三 seed --source-snapshot-id 绑之再种
      → create() 研究 manifest(此时最新派生批锚与新向量相容,双检放行)。
    结构: 同表同 digest 同发布机制(镜像+attestation);content **无 taosha 键** = 源级快照
    标识(taosha 014: 研究 manifest 双检只对含 taosha 半者施加;引擎 ViewReader 对缺 taosha
    半的快照 fail-closed 拒读 = 源级快照不可当研究 manifest 消费)。"""
    content: dict = {"qbase": {}}
    with psycopg.connect(_dsn("QBASE_APP_DSN")) as qc, qc.cursor() as cur:
        cur.execute("SELECT current_user")
        assert cur.fetchone()[0] != "taosha_engine", "生成角色不得为 taosha_engine(硬化②)"
        content["qbase"] = collect_qbase_vector(cur)
    missing = REQUIRED_QBASE - set(content["qbase"])
    if missing:
        raise RuntimeError(f"源级快照缺必需键 {sorted(missing)}:先补齐源批次")
    with psycopg.connect(_dsn("TAOSHA_APP_DSN")) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO study_snapshot (content, note) VALUES (%s, %s) "
            "RETURNING snapshot_id, digest", (Json(content), note))
        sid, digest = cur.fetchone()
        conn.commit()
    publish(sid)
    return sid, digest, content


def publish(snapshot_id: int) -> str:
    """修法#2 发布流程②③(受权角色专责,append-only,不 UPDATE):
    ② qbase 落相同 snapshot_id/content 的不可变镜像(digest 由 qbase 触发器同式库算);
    ③ 校验两库 content/digest 一致后另行 INSERT publication attestation。
    幂等: 镜像/凭证已在且 digest 一致 → 跳过;镜像在而 digest 不一致 → RAISE(半成品/
    错镜像留审计不改不删,须另起新 manifest)。返回 attested digest。"""
    row = get(snapshot_id)
    if row is None:
        raise RuntimeError(f"taosha manifest {snapshot_id} 不存在,无从发布")
    t_content, t_digest = row["content"], row["digest"]
    with psycopg.connect(_dsn("QBASE_APP_DSN")) as qc, qc.cursor() as cur:
        cur.execute("SELECT content, digest FROM study_snapshot_mirror WHERE snapshot_id=%s",
                    (snapshot_id,))
        m = cur.fetchone()
        if m is None:
            cur.execute("INSERT INTO study_snapshot_mirror (snapshot_id, content) "
                        "VALUES (%s, %s) RETURNING digest", (snapshot_id, Json(t_content)))
            m_digest = cur.fetchone()[0]
        else:
            m_content, m_digest = m
            if m_content != t_content:
                raise RuntimeError(
                    f"snapshot {snapshot_id} 镜像 content 与 taosha 不一致(半成品留审计,"
                    f"不改不删;须另起新 manifest)")
        if m_digest != t_digest:   # 两库 canonical digest 同式 → content 同则必同;不同即中止
            raise RuntimeError(
                f"snapshot {snapshot_id} 两库 digest 不一致(taosha {t_digest[:12]}… / "
                f"qbase {m_digest[:12]}…),拒发布")
        cur.execute("SELECT count(*) FROM study_snapshot_publication "
                    "WHERE snapshot_id=%s AND attested_digest=%s", (snapshot_id, t_digest))
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO study_snapshot_publication (snapshot_id, attested_digest) "
                        "VALUES (%s, %s)", (snapshot_id, t_digest))
        qc.commit()
    return t_digest


def read_published_snapshot(qcur, snapshot_id: int) -> tuple[dict, str]:
    """修法#3 窄补(2026-07-13): 读 qbase 权威镜像中的**已发布** snapshot(mirror+attestation),
    供 seed 绑定源锚——锚=所读快照的 qbase 向量+{snapshot_id, digest},非运行时 current/max 现值。
    传入开放的 qbase 游标(qbase_app 对两表有 SELECT);无镜像/未 attested → RuntimeError(fail-closed)。"""
    qcur.execute(
        "SELECT m.content, m.digest FROM study_snapshot_mirror m "
        "WHERE m.snapshot_id = %s AND EXISTS ("
        "  SELECT 1 FROM study_snapshot_publication p "
        "  WHERE p.snapshot_id = m.snapshot_id AND p.attested_digest = m.digest)",
        (snapshot_id,))
    row = qcur.fetchone()
    if row is None:
        raise RuntimeError(
            f"修法#3(窄补): snapshot {snapshot_id} 无已发布镜像(mirror+attestation 任一缺),"
            "seed 拒运行——须先经受权角色 publish(fail-closed,禁绑定未发布快照)")
    return row[0], row[1]


def get(snapshot_id: int | None = None) -> dict | None:
    """读 manifest(None=最新)。"""
    with psycopg.connect(_dsn("TAOSHA_APP_DSN")) as conn, \
         conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        if snapshot_id is None:
            cur.execute("SELECT * FROM study_snapshot ORDER BY snapshot_id DESC LIMIT 1")
        else:
            cur.execute("SELECT * FROM study_snapshot WHERE snapshot_id=%s", (snapshot_id,))
        return cur.fetchone()


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--create", action="store_true")
    g.add_argument("--create-source", action="store_true",
                   help="窄补第三轮 #3-b: 生成源级快照(仅 qbase 半;合法再种链条第一环)")
    g.add_argument("--show", type=int)
    g.add_argument("--latest", action="store_true")
    g.add_argument("--publish", type=int, metavar="N",
                   help="修法#2: 对既有 manifest N 执行 qbase 镜像+attestation 发布(幂等)")
    ap.add_argument("--note", default=None)
    ap.add_argument("--from-source-snapshot", type=int, default=None, metavar="N",
                    help="窄补三#3-b: 研究 manifest 的 qbase 半锚定已发布源级快照 N(再种链收口)")
    a = ap.parse_args()

    if a.create:
        sid, digest, content = create(a.note, from_source_snapshot=a.from_source_snapshot)
        print(f"StudySnapshot 已生成并发布: snapshot_id={sid} digest={digest}")
        print(json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if a.create_source:
        sid, digest, content = create_source(a.note)
        print(f"源级快照已生成并发布(仅 qbase 半,#3-b): snapshot_id={sid} digest={digest}")
        print(json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    if a.publish is not None:
        d = publish(a.publish)
        print(f"StudySnapshot 已发布(镜像+attestation,幂等): snapshot_id={a.publish} digest={d}")
        return 0
    row = get(a.show if a.show is not None else None)
    if row is None:
        print("无此 manifest", file=sys.stderr)
        return 1
    print(f"snapshot_id={row['snapshot_id']} digest={row['digest']} "
          f"created_by={row['created_by']} created_at={row['created_at']} note={row['note']!r}")
    print(json.dumps(row["content"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
