"""淘沙 · reader · ViewReader(切片3 步4:真实 explore_reader 视图 + 市场基准表)。

契约实现之二(承 SyntheticReader 同签名:prices()/prices_by_security()/events()/calendar()):
数据源 = qbase `explore_reader` 三视图(role `taosha_engine` 只读、物理隔离)+ taosha
`market_return_current`(全市场等权基准,步3 预计算)。engine 侧零改造——runner 经 calendar()/
market_return() 消费,与合成同签名(合成回退 equal_weight_market,ViewReader 读表不现算)。

红线(taosha CLAUDE.md §2):不 import 兄弟目录;数据入口 = qbase 归一视图(只读账号 taosha_engine)。
  · holdout(<2024-07-01)/北交所.BJ排除/后复权 close 由视图定义**结构性保证**;reader 侧
    contract.enforce_* 再挡一道(纵深防御,骗不了人)。
  · **事件票取数(非全宇宙)**:先读 events 定样本 ts_code,再按样本拉 prices(不载全 15M 行)。
  · **轴=日历(约束②)**:prices/events 均 ∩ explore_reader_calendar——个股侧遇 bar 落非交易日
    (标准处置,人 2026-07-08 standing 裁定)结构性剔除、收益跨到前一日历交易日(returns.py 跨缺口)。
秘钥纪律:DSN 只从 .env 读(TAOSHA_ENGINE_QBASE_DSN / TAOSHA_ENGINE_TAOSHA_DSN),不回显、不进 git。
"""
from __future__ import annotations

import datetime as dt
import os
from typing import Iterator, Optional

from .contract import (
    CalendarRow, EventRow, PriceRow,
    enforce_holdout_calendar, enforce_holdout_event, enforce_holdout_price,
)

_ENV_QBASE = "TAOSHA_ENGINE_QBASE_DSN"
_ENV_TAOSHA = "TAOSHA_ENGINE_TAOSHA_DSN"


def _load_env(path: str) -> dict:
    """只取需要键,绝不回显值(秘钥纪律)。"""
    env = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


class ViewReader:
    """契约实现之二:真 explore_reader 视图 + 市场基准表(role taosha_engine 只读)。

    sample: 可选限定 ts_code 集合;缺省=events 视图的证券全集(事件票取数)。
    """

    def __init__(self, qbase_dsn: Optional[str] = None, taosha_dsn: Optional[str] = None,
                 env_path: Optional[str] = None, sample: Optional[set] = None):
        if qbase_dsn is None or taosha_dsn is None:
            root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            env = _load_env(env_path or os.path.join(root, ".env"))
            qbase_dsn = qbase_dsn or env.get(_ENV_QBASE)
            taosha_dsn = taosha_dsn or env.get(_ENV_TAOSHA)
        if not qbase_dsn or not taosha_dsn:
            raise RuntimeError(f"缺 {_ENV_QBASE} / {_ENV_TAOSHA}(.env);ViewReader 需引擎只读 DSN")
        self._qdsn = qbase_dsn
        self._tdsn = taosha_dsn
        self._sample = sample
        self._sample_cache: Optional[list] = None

    def _connect(self, dsn):
        import psycopg
        return psycopg.connect(dsn)

    # ── events(holdout 焊死;再挡一道)──────────────────────────────────────────
    def _raw_events(self) -> Iterator[EventRow]:
        with self._connect(self._qdsn) as c, c.cursor() as cur:
            cur.execute(
                "SELECT ts_code, event_id, first_ann_date, event_type_layer, snapshot_batch "
                "FROM explore_reader_events ORDER BY ts_code, event_id")
            for ts, eid, fad, layer, batch in cur.fetchall():
                yield EventRow(ts_code=ts, event_id=str(eid), first_ann_date=fad,
                               event_type_layer=layer, snapshot_batch=str(batch))

    def events(self) -> Iterator[EventRow]:
        return enforce_holdout_event(self._raw_events())

    def _sample_codes(self) -> list:
        """样本证券 = 显式 sample,否则 events 视图证券全集(事件票取数,非全宇宙)。"""
        if self._sample is not None:
            return sorted(self._sample)
        if self._sample_cache is None:
            self._sample_cache = sorted({e.ts_code for e in self.events()})
        return self._sample_cache

    # ── prices(∩ calendar 轴;样本内;holdout+.BJ+后复权 视图结构性保证,再挡一道)──
    def _raw_prices(self) -> Iterator[PriceRow]:
        codes = self._sample_codes()
        if not codes:
            return
        with self._connect(self._qdsn) as c:
            with c.cursor(name="vr_prices_stream") as cur:
                cur.itersize = 100_000
                cur.execute(
                    "SELECT p.ts_code, p.trade_date, p.close, p.is_suspended, p.limit_status, "
                    '       p.board, p.is_st, p.industry, p."open" '            # open=视图末列(010 增)
                    "FROM explore_reader_prices p "
                    "JOIN explore_reader_calendar cal USING (trade_date) "   # 轴=日历(约束②)
                    "WHERE p.ts_code = ANY(%s) "
                    "ORDER BY p.ts_code, p.trade_date", (codes,))
                for ts, td, close, susp, lim, board, is_st, ind, opn in cur:
                    yield PriceRow(
                        ts_code=ts, trade_date=td,
                        close=None if close is None else float(close),
                        is_suspended=bool(susp), limit_status=lim, board=board,
                        is_st=bool(is_st), industry=ind,
                        open=None if opn is None else float(opn))

    def prices(self) -> Iterator[PriceRow]:
        return enforce_holdout_price(self._raw_prices())

    def prices_by_security(self) -> dict[str, list[PriceRow]]:
        """{ts_code: [PriceRow 按 trade_date 升序]};holdout 已滤、样本内、∩日历轴。"""
        out: dict[str, list[PriceRow]] = {}
        for row in self.prices():
            out.setdefault(row.ts_code, []).append(row)
        for rows in out.values():
            rows.sort(key=lambda r: r.trade_date)
        return out

    # ── calendar(视图权威交易日轴;holdout 焊死)────────────────────────────────
    def calendar(self) -> Iterator[CalendarRow]:
        with self._connect(self._qdsn) as c, c.cursor() as cur:
            cur.execute("SELECT trade_date, pretrade_date FROM explore_reader_calendar "
                        "ORDER BY trade_date")
            rows = [CalendarRow(trade_date=d, pretrade_date=p) for d, p in cur.fetchall()]
        return enforce_holdout_calendar(rows)

    # ── b1 池成员(#2b;预计算 pool_b1_current;引擎读表不现算全市场 amount)──────────
    def pool_membership(self) -> dict:
        """{trade_date: frozenset(ts_code)} 从 taosha `pool_b1_current`(max batch 路由)读 b1 池成员。
        供 #2b 事件生成的 PIT 过滤(进场日在池)。口径=liquidity_pool(003 预计算,frozen_digest 在 batch)。"""
        out: dict = {}
        with self._connect(self._tdsn) as c, c.cursor() as cur:
            cur.execute("SELECT trade_date, ts_code FROM pool_b1_current")
            for d, ts in cur.fetchall():
                out.setdefault(d, set()).add(ts)
        return {d: frozenset(s) for d, s in out.items()}

    # ── 市场基准(步3 预计算全市场等权;引擎读表不现算)────────────────────────
    def market_return(self, dates: list) -> list:
        """按给定 date 轴返回全市场等权连续(对数)日收益;轴上无该日(如首日/表未覆盖)→ None。
        读 taosha `market_return_current`(max batch 路由视图)。"""
        with self._connect(self._tdsn) as c, c.cursor() as cur:
            cur.execute("SELECT trade_date, ret_eqw FROM market_return_current")
            m = {d: float(r) for d, r in cur.fetchall()}
        return [m.get(d) for d in dates]

    # ── #2b b1 池等权 PIT 活基准(004 预计算;基准成分逐日=当日池快照;引擎读表不现算)────
    def pool_return(self, dates: list) -> list:
        """按给定 date 轴返回 b1 池等权连续(对数)日收益;轴上无该日(首日/表未覆盖/池空)→ None。
        读 taosha `pool_b1_return_current`(max batch 路由视图)。逐日 ret = 当日池快照成员
        (pool_b1_current[d])中有present bar且有前序present bar的票 log(close_d/close_前序)的等权平均
        (004 seed 落库,验收硬项=抽日成分==当日池快照)。#2b SIM regressor rm(口径②池内假设=池等权)。"""
        with self._connect(self._tdsn) as c, c.cursor() as cur:
            cur.execute("SELECT trade_date, ret_pool_eqw FROM pool_b1_return_current")
            m = {d: float(r) for d, r in cur.fetchall()}
        return [m.get(d) for d in dates]


if __name__ == "__main__":
    # 冒烟(需 .env 引擎 DSN + 真视图/表):证契约可读、样本取自事件票、市场基准对齐。
    rd = ViewReader()
    codes = rd._sample_codes()
    cal = list(rd.calendar())
    mkt = rd.market_return([c.trade_date for c in cal])
    n_mkt = sum(1 for x in mkt if x is not None)
    print(f"ViewReader OK:样本证券 {len(codes)} / 日历轴 {len(cal)} 日 / 市场基准非空 {n_mkt} 日")
    assert all(c.trade_date < dt.date(2024, 7, 1) for c in cal), "holdout 泄漏"
