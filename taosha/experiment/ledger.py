"""淘沙 · 台账 ledger 接口(切片1)。

唯一写入对象 = experiment 台账(spec §2)。app 角色 taosha_app 仅 SELECT/INSERT/UPDATE,
无 DELETE/TRUNCATE/属主 → 触发器禁不掉(真焊死)。本模块 app 侧也做前置校验,
但**权威 enforcement 在数据库触发器**(pap 冻结不可改 / status 单向推进 / result 一次性 /
family_trial 自增 / llm→prescreen / append-only)。

DSN 只从环境变量 TAOSHA_APP_DSN 读(秘钥住 .env,不入代码/git)。
"""
from __future__ import annotations

import os

import psycopg
from psycopg.types.json import Json

from . import pap as pap_mod


def _dsn() -> str:
    dsn = os.environ.get("TAOSHA_APP_DSN")
    if not dsn:
        raise RuntimeError("环境无 TAOSHA_APP_DSN(应 source /opt/quant/.env,勿回显)")
    return dsn


def connect():
    return psycopg.connect(_dsn())


def register(*, family, title, source_type, verdict_power, pap, contamination_note,
             data_class=None, crowding_prior=None, allow_meta_null=False, conn=None) -> int:
    """登记一条假设(status=registered)。family_trial 由触发器自增,忽略传值。
    源效力校验:llm→prescreen 由触发器强制,此处提前挡以给友好报错。返回 exp_id。

    裁3(v1.5):data_class/crowding_prior 新登记**强制填写**;仅创始存量转录可用
    allow_meta_null=True 豁免(留 NULL、不回填)。"""
    if source_type not in pap_mod.VALID_SOURCE_TYPES:
        raise ValueError(f"source_type 非法: {source_type}")
    if verdict_power not in pap_mod.VALID_VERDICT_POWER:
        raise ValueError(f"verdict_power 非法: {verdict_power}")
    if source_type == "llm" and verdict_power != "prescreen":
        raise ValueError("铁律①: source_type=llm 强制 verdict_power=prescreen")
    if not allow_meta_null and (data_class is None or crowding_prior is None):
        raise ValueError("裁3: 新登记强制填 data_class 与 crowding_prior(存量转录用 allow_meta_null)")
    pap_mod.validate_pap(pap)

    own = conn is None
    conn = conn or connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO experiment
                     (family, family_trial, title, source_type, verdict_power,
                      contamination_note, pap_json, data_class, crowding_prior)
                   VALUES (%s, 0, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING exp_id, family_trial""",
                (family, title, source_type, verdict_power, contamination_note,
                 Json(pap), data_class, crowding_prior),
            )
            exp_id, trial = cur.fetchone()
        if own:
            conn.commit()
        return exp_id
    finally:
        if own:
            conn.close()


def freeze(exp_id: int, *, conn=None) -> None:
    """冻结:registered→frozen,置 frozen_at。pap_json 自此不可改(触发器)。"""
    own = conn is None
    conn = conn or connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE experiment SET status='frozen', frozen_at=now()
                   WHERE exp_id=%s AND status='registered'""", (exp_id,))
            if cur.rowcount != 1:
                raise RuntimeError(f"exp {exp_id} 冻结失败(非 registered 态或不存在)")
        if own:
            conn.commit()
    finally:
        if own:
            conn.close()


def close(exp_id: int, reason: str, *, conn=None) -> None:
    """关闭(被后续变体取代,不跑):→closed,result_json 记关闭原因(一次性),done_at 置。"""
    own = conn is None
    conn = conn or connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE experiment
                     SET status='closed', result_json=%s, done_at=now()
                   WHERE exp_id=%s AND status IN ('registered','frozen')""",
                (Json({"closure": reason}), exp_id))
            if cur.rowcount != 1:
                raise RuntimeError(f"exp {exp_id} 关闭失败(态非 registered/frozen 或不存在)")
        if own:
            conn.commit()
    finally:
        if own:
            conn.close()


def set_meta(exp_id: int, *, data_class, crowding_prior, conn=None) -> None:
    """填/改元数据列 data_class/crowding_prior(非冻结列,不作筛选依据;裁3:#2b 等)。"""
    own = conn is None
    conn = conn or connect()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE experiment SET data_class=%s, crowding_prior=%s WHERE exp_id=%s",
                        (data_class, crowding_prior, exp_id))
            if cur.rowcount != 1:
                raise RuntimeError(f"exp {exp_id} set_meta 失败(不存在)")
        if own:
            conn.commit()
    finally:
        if own:
            conn.close()


def get(exp_id: int, *, conn=None) -> dict | None:
    own = conn is None
    conn = conn or connect()
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT * FROM experiment WHERE exp_id=%s", (exp_id,))
            return cur.fetchone()
    finally:
        if own:
            conn.close()


def list_all(*, conn=None) -> list[dict]:
    own = conn is None
    conn = conn or connect()
    try:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("""SELECT exp_id, family, family_trial, title, source_type,
                                  verdict_power, status, data_class, crowding_prior,
                                  frozen_at FROM experiment ORDER BY exp_id""")
            return cur.fetchall()
    finally:
        if own:
            conn.close()
