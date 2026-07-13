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


def create(note: str | None = None) -> tuple[int, str, dict]:
    """生成 manifest(单事务;digest 由库触发器权威计算)。返回 (snapshot_id, digest, content)。"""
    content = collect_content()
    with psycopg.connect(_dsn("TAOSHA_APP_DSN")) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO study_snapshot (content, note) VALUES (%s, %s) "
            "RETURNING snapshot_id, digest", (Json(content), note))
        sid, digest = cur.fetchone()
        conn.commit()
    return sid, digest, content


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
    g.add_argument("--show", type=int)
    g.add_argument("--latest", action="store_true")
    ap.add_argument("--note", default=None)
    a = ap.parse_args()

    if a.create:
        sid, digest, content = create(a.note)
        print(f"StudySnapshot 已生成: snapshot_id={sid} digest={digest}")
        print(json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True))
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
