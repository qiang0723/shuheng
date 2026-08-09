"""exp14 冻结前对账 reader；只读专属事实视图，不读取价格或收益。"""
from __future__ import annotations

from typing import Optional

from .view import _ENV_QBASE, _resolve_dsn


VIEWS = {
    "current": {
        "dividend": "explore_reader_ex_div_gap",
        "factor": "explore_reader_ex_div_factor",
    },
    "snapshot": {
        "dividend": "explore_reader_ex_div_gap_snap",
        "factor": "explore_reader_ex_div_factor_snap",
    },
}


class ExDivGapReader:
    """读取current或snapshot375最小列面；事件判断全部留在compute。"""

    def __init__(self, snapshot_id: int, mode: str,
                 qbase_dsn: Optional[str] = None, env_path: Optional[str] = None):
        if snapshot_id is None or mode not in VIEWS:
            raise RuntimeError("exp14 reader须显式给snapshot ID与current/snapshot模式")
        qbase_dsn = _resolve_dsn(_ENV_QBASE, qbase_dsn, env_path)
        if not qbase_dsn:
            raise RuntimeError(f"缺 {_ENV_QBASE}(显式参数、环境变量或.env)")
        self._snapshot_id = int(snapshot_id)
        self._mode = mode
        self._views = VIEWS[mode]
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

    def read_only_status(self) -> str:
        with self._connect() as conn:
            return conn.execute("SHOW transaction_read_only").fetchone()[0]

    def dividend_rows(self) -> list[dict]:
        query = (
            "SELECT ts_code,end_date,ann_date,div_proc,stk_div,stk_bo_rate,stk_co_rate,"
            "record_date,ex_date,imp_ann_date,update_flag,snapshot_batch "
            f"FROM {self._views['dividend']} "
            "ORDER BY ts_code,end_date,ex_date,imp_ann_date,record_date NULLS FIRST,"
            "stk_div NULLS FIRST,stk_bo_rate NULLS FIRST,stk_co_rate NULLS FIRST"
        )
        out = []
        with self._connect() as conn:
            for values in conn.execute(query):
                keys = ("ts_code", "end_date", "ann_date", "div_proc", "stk_div",
                        "stk_bo_rate", "stk_co_rate", "record_date", "ex_date",
                        "imp_ann_date", "update_flag", "snapshot_batch")
                out.append(dict(zip(keys, values)))
        return out

    def calendar_dates(self) -> list:
        with self._connect() as conn:
            return [row[0] for row in conn.execute(
                "SELECT trade_date FROM explore_reader_calendar_snap ORDER BY trade_date")]

    def source_batches(self) -> dict:
        out = {}
        with self._connect() as conn:
            for key, view in self._views.items():
                row = conn.execute(f"SELECT snapshot_batch FROM {view} LIMIT 1").fetchone()
                if row is None:
                    raise RuntimeError(f"exp14 {self._mode}/{key}视图为空，无法确认批次")
                out[key] = row[0]
        return out

    @staticmethod
    def _arrays(keys: list[tuple]) -> tuple[list, list]:
        return [key[0] for key in keys], [key[1] for key in keys]

    def factor_rows(self, keys: list[tuple]) -> list[dict]:
        if not keys:
            return []
        codes, dates = self._arrays(keys)
        query = (
            "WITH wanted(ts_code,trade_date) AS ("
            "SELECT * FROM unnest(%s::text[],%s::date[])) "
            "SELECT f.ts_code,f.trade_date,f.adj_factor,f.snapshot_batch "
            f"FROM {self._views['factor']} f JOIN wanted w USING(ts_code,trade_date) "
            "ORDER BY f.ts_code,f.trade_date,f.adj_factor NULLS FIRST"
        )
        with self._connect() as conn:
            return [{"ts_code": ts, "trade_date": day, "adj_factor": factor,
                     "snapshot_batch": batch}
                    for ts, day, factor, batch in conn.execute(query, (codes, dates))]
