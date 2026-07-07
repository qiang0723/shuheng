"""淘沙 · reader · explore_reader 列契约(单一真源)。

《explore_reader 列契约(淘沙侧要求)》的**机器可读镜像**(docs/explore-reader-contract.md 为叙述本)。
切片2 SyntheticReader 与 Q3 真视图都必须产出下列同名同序列;engine 只依赖这些形状。

红线:holdout 焊死(HOLDOUT_START,契约 §0);close 停牌=None(禁零填充);只读。
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Optional

# holdout 线(spec / STATE:焊在视图 WHERE;reader 结构上拿不到 >= 此日的数据)
HOLDOUT_START = dt.date(2024, 7, 1)

# 契约列(顺序即视图列顺序;Q3 视图须逐列对齐)
PRICE_COLUMNS = (
    "ts_code", "trade_date", "close", "is_suspended",
    "limit_status", "board", "is_st", "industry",
)
EVENT_COLUMNS = (
    "ts_code", "event_id", "first_ann_date", "event_type_layer", "snapshot_batch",
)

# limit_status / board 值域(契约 §1)
LIMIT_STATUS = ("none", "limit_up", "limit_down", "one_word")
BOARDS = ("main", "chinext", "star", "bse")


@dataclass(frozen=True)
class PriceRow:
    """explore_reader_prices 一行(契约 §1)。close=None ⇔ 停牌/无交易(禁零填充)。"""
    ts_code: str
    trade_date: dt.date
    close: Optional[float]
    is_suspended: bool
    limit_status: str
    board: str
    is_st: bool
    industry: str

    def __post_init__(self):
        if self.limit_status not in LIMIT_STATUS:
            raise ValueError(f"limit_status 非法: {self.limit_status!r}")
        if self.board not in BOARDS:
            raise ValueError(f"board 非法: {self.board!r}")
        if self.is_suspended and self.close is not None:
            raise ValueError(f"{self.ts_code}@{self.trade_date}: 停牌日 close 必须 None(禁零填充)")


@dataclass(frozen=True)
class EventRow:
    """explore_reader_events 一行(契约 §2)。first_ann_date=事件日锚,无 fallback。"""
    ts_code: str
    event_id: str
    first_ann_date: dt.date
    event_type_layer: str
    snapshot_batch: str


def enforce_holdout_price(rows):
    """结构性 holdout 过滤:只放行 trade_date < HOLDOUT_START。
    这是"探索代码结构上拿不到 holdout"的落地——真视图在 WHERE 焊,reader 侧再挡一道。"""
    for r in rows:
        if r.trade_date < HOLDOUT_START:
            yield r


def enforce_holdout_event(rows):
    """事件锚落 holdout 区的事件结构上取不到。"""
    for r in rows:
        if r.first_ann_date < HOLDOUT_START:
            yield r
