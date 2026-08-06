"""exp19 专属只读输入适配；只消费 dividend 初始预案所需最小列面。"""
from __future__ import annotations

from typing import Optional

from .view import _ENV_QBASE, _resolve_dsn


class DividendSurpriseReader:
    """经 StudySnapshot GUC 读取 exp19 dividend 事实腿；无事件判断。"""

    def __init__(self, snapshot_id: int, qbase_dsn: Optional[str] = None,
                 env_path: Optional[str] = None):
        if snapshot_id is None:
            raise RuntimeError("exp19 reader 必须显式给 StudySnapshot ID")
        qbase_dsn = _resolve_dsn(_ENV_QBASE, qbase_dsn, env_path)
        if not qbase_dsn:
            raise RuntimeError(f"缺 {_ENV_QBASE}(显式参数、环境变量或.env)")
        self._snapshot_id = int(snapshot_id)
        self._qdsn = qbase_dsn

    def _connect(self):
        import psycopg

        conn = psycopg.connect(self._qdsn, options="-c default_transaction_read_only=on")
        conn.execute("SELECT set_config('shuheng.study_snapshot_id', %s, false)",
                     (str(self._snapshot_id),))
        return conn

    @property
    def snapshot_info(self) -> dict:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT m.content,m.digest FROM study_snapshot_mirror m "
                "JOIN study_snapshot_publication p USING(snapshot_id) "
                "WHERE m.snapshot_id=%s AND p.attested_digest=m.digest",
                (self._snapshot_id,),
            )
            row = cur.fetchone()
        if row is None:
            raise RuntimeError(f"StudySnapshot {self._snapshot_id}缺镜像或发布凭证")
        return {"snapshot_id": self._snapshot_id, "content": row[0], "digest": row[1]}

    def dividend_rows(self) -> list[dict]:
        out = []
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT ts_code,end_date,ann_date,div_proc,cash_div_tax,base_date,base_share,"
                "update_flag,snapshot_batch FROM explore_reader_dividend_snap "
                "ORDER BY ts_code,end_date,ann_date,div_proc,update_flag,cash_div_tax NULLS FIRST")
            for ts, end, ann, stage, cash, base_date, base_share, flag, batch in cur.fetchall():
                out.append({"ts_code": ts, "end_date": end, "ann_date": ann,
                            "div_proc": stage, "cash_div_tax": cash,
                            "base_date": base_date, "base_share": base_share,
                            "update_flag": flag, "snapshot_batch": str(batch)})
        return out
