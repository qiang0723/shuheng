"""exp24 专属只读输入适配；不向通用 ViewReader 塞实验分支。"""
from __future__ import annotations

import os
from typing import Optional

from .view import _ENV_QBASE, _load_env


class SoxSpilloverReader:
    """经 StudySnapshot GUC 读取 SOX 与申万半导体成员最小列面。"""

    def __init__(self, snapshot_id: int, qbase_dsn: Optional[str] = None,
                 env_path: Optional[str] = None):
        if snapshot_id is None:
            raise RuntimeError("SOX reader 必须显式给 StudySnapshot ID")
        if qbase_dsn is None:
            root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            qbase_dsn = _load_env(env_path or os.path.join(root, ".env")).get(_ENV_QBASE)
        if not qbase_dsn:
            raise RuntimeError(f"缺 {_ENV_QBASE}(.env)")
        self._snapshot_id = int(snapshot_id)
        self._qdsn = qbase_dsn

    def _connect(self):
        import psycopg
        conn = psycopg.connect(self._qdsn)
        conn.execute("SELECT set_config('shuheng.study_snapshot_id', %s, false)",
                     (str(self._snapshot_id),))
        return conn

    def sox_rows(self) -> list[dict]:
        out = []
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT trade_date, close, currency, snapshot_batch "
                "FROM explore_reader_sox_daily_snap ORDER BY trade_date")
            for trade_date, close, currency, batch in cur.fetchall():
                out.append({"trade_date": trade_date, "close": close,
                            "currency": currency, "snapshot_batch": str(batch)})
        return out

    def member_rows(self) -> list[dict]:
        out = []
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT index_code, ts_code, in_date, out_date, snapshot_batch "
                "FROM explore_reader_sw_member_snap "
                "ORDER BY ts_code, in_date NULLS FIRST, out_date NULLS LAST")
            for index_code, ts_code, in_date, out_date, batch in cur.fetchall():
                out.append({"index_code": index_code, "ts_code": ts_code,
                            "in_date": in_date, "out_date": out_date,
                            "snapshot_batch": str(batch)})
        return out
