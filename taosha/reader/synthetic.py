"""淘沙 · reader · SyntheticReader(切片2:对合成 fixture,不建 mock 视图)。

读 make_ashare_fixture 产出的 prices.csv + events.csv,产出与《explore_reader 列契约》
§1/§2 **同列同序**的 PriceRow / EventRow 迭代器。holdout 结构性隔离(contract.enforce_*)。

Q3 交付真 explore_reader 视图时,只需实现同签名的 ViewReader(换数据源=视图),
engine 侧**零改造**——这正是"接口签名按契约写死"的落地。
"""
from __future__ import annotations

import csv
import datetime as dt
from typing import Iterator

from .contract import (
    EventRow, PriceRow, enforce_holdout_event, enforce_holdout_price,
)


def _date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


class SyntheticReader:
    """契约实现之一:合成 fixture。接口 = prices()/events(),与 Q3 ViewReader 同签名。"""

    def __init__(self, prices_path: str, events_path: str):
        self._prices_path = prices_path
        self._events_path = events_path

    def _raw_prices(self) -> Iterator[PriceRow]:
        with open(self._prices_path, newline="") as fh:
            for r in csv.DictReader(fh):
                yield PriceRow(
                    ts_code=r["ts_code"],
                    trade_date=_date(r["trade_date"]),
                    close=None if r["close"] == "" else float(r["close"]),
                    is_suspended=bool(int(r["is_suspended"])),
                    limit_status=r["limit_status"],
                    board=r["board"],
                    is_st=bool(int(r["is_st"])),
                    industry=r["industry"],
                )

    def _raw_events(self) -> Iterator[EventRow]:
        with open(self._events_path, newline="") as fh:
            for r in csv.DictReader(fh):
                yield EventRow(
                    ts_code=r["ts_code"],
                    event_id=r["event_id"],
                    first_ann_date=_date(r["first_ann_date"]),
                    event_type_layer=r["event_type_layer"],
                    snapshot_batch=r["snapshot_batch"],
                )

    # ── 契约接口(Q3 ViewReader 须同名同签名)────────────────────────────────
    def prices(self) -> Iterator[PriceRow]:
        """全宇宙逐 [证券×交易日] 价格行(holdout 焊死:只放行 trade_date < 2024-07-01)。"""
        return enforce_holdout_price(self._raw_prices())

    def events(self) -> Iterator[EventRow]:
        """逐 [证券×事件] 事件锚(holdout 焊死:first_ann_date < 2024-07-01)。"""
        return enforce_holdout_event(self._raw_events())

    # ── 便利:按证券索引价格(engine 组估计窗/事件窗用)──────────────────────
    def prices_by_security(self) -> dict[str, list[PriceRow]]:
        """{ts_code: [PriceRow 按 trade_date 升序]};holdout 已滤。"""
        out: dict[str, list[PriceRow]] = {}
        for row in self.prices():
            out.setdefault(row.ts_code, []).append(row)
        for rows in out.values():
            rows.sort(key=lambda r: r.trade_date)
        return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--prices", required=True)
    ap.add_argument("--events", required=True)
    a = ap.parse_args()
    rd = SyntheticReader(a.prices, a.events)
    evs = list(rd.events())
    by_sec = rd.prices_by_security()
    print(f"SyntheticReader OK:{len(evs)} 事件 / {len(by_sec)} 证券")
    print("样例事件:", evs[0])
    print("样例价格行数(A01):", len(by_sec["A01"]))
    # holdout 结构性校验:无任何 trade_date >= 2024-07-01
    assert all(r.trade_date < dt.date(2024, 7, 1) for rows in by_sec.values() for r in rows)
    print("holdout 隔离 OK(无 >= 2024-07-01 的行)")
