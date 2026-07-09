"""淘沙 · engine · #2b drawdown-rebuy 事件生成(接 ViewReader;附录 F-rev1;exp_id 3)。

#2b 事件非台账读取(不同于 #4 forecast),而是**从价格模式 PIT 计算**:逐票后复权收盘序列(交易日轴)
过 compute.drawdown_signal 状态机 → 进场事件锚 T;再由 **b1 池 PIT 过滤**(进场日在池,liquidity_pool)。

数据流:reader.prices_by_security()(后复权 close,真实 bar 无 None)→ generate_entries → 映射 idx→date
→ 可选 in_pool(ts, date) 过滤 → 事件列表(含 D1/D2/D3 诊断,F2 报告项)。

红线:一个数不改冻结口径;PIT(信号只回看)。b1 池成员由预计算表提供(引擎读表不现算全市场 amount)。
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Callable, Optional

from taosha.compute.drawdown_signal import generate_entries


@dataclass(frozen=True)
class DrawdownEvent:
    ts_code: str
    event_date: dt.date              # 事件锚 T = 进场日(收盘确认;τ=0:=T+1)
    event_id: str                    # ts_code:YYYYMMDD(逐次独立事件唯一键)
    d1_never_broke_ma10: bool        # F2 D1
    d2_episode_to_entry_days: int    # F2 D2
    d3_broke_ma20_before_entry: bool  # F2 D3
    in_pool: bool                    # 进场日是否 b1 池成员(过滤依据;记录留痕)


@dataclass(frozen=True)
class DrawdownEventRow:
    """runner 事件源适配(承 EventRow 同接口:ts_code/event_id/first_ann_date/event_type_layer)。

    #2b 事件锚 T = 进场日(event_date)→ first_ann_date(clean_event 消费:T 定位、τ=0:=T+1,与 #4 同轴)。
    event_type_layer=None:#2b 单信号事件,三层(预喜/预亏/扭亏)**不适用**(runner strata_enabled=False)。
    D1/D2/D3 随事件带入(runner 存 se_meta → _assemble 聚合成 drawdown_diagnostic 报告项,不进 verdict)。"""
    ts_code: str
    event_id: str
    first_ann_date: dt.date
    snapshot_batch: str
    d1_never_broke_ma10: bool
    d2_episode_to_entry_days: int
    d3_broke_ma20_before_entry: bool
    event_type_layer: object = None   # 三层不适用(#2b 单信号);None → strata 跳过、不误入 'unknown' 层


def to_event_rows(events: list, snapshot_batch: str) -> list:
    """DrawdownEvent 列表 → runner 事件源(DrawdownEventRow)。事件锚=进场日 event_date→first_ann_date。"""
    return [DrawdownEventRow(
        ts_code=e.ts_code, event_id=e.event_id, first_ann_date=e.event_date,
        snapshot_batch=snapshot_batch,
        d1_never_broke_ma10=e.d1_never_broke_ma10,
        d2_episode_to_entry_days=e.d2_episode_to_entry_days,
        d3_broke_ma20_before_entry=e.d3_broke_ma20_before_entry) for e in events]


def diagnostic_summary(triples: list) -> dict:
    """D1/D2/D3 诊断聚合(F2;报告项·不进 verdict)。triples=[(d1:bool, d2:int, d3:bool), ...]。

    D1 从未破 ma10 占比;D2 回撤触发→进场交易日数分布(min/mean/median/max);D3 进场前曾破 ma20 占比。
    纯计数陈述、不下判断(铁律⑤)。空 → n=0、各项 None。"""
    n = len(triples)
    if n == 0:
        return {"n": 0, "d1_never_broke_ma10_frac": None, "d2": None,
                "d3_broke_ma20_before_entry_frac": None}
    d1 = sum(1 for d1, _, _ in triples if d1)
    d3 = sum(1 for _, _, d3 in triples if d3)
    d2s = sorted(d2 for _, d2, _ in triples)
    mid = n // 2
    median = d2s[mid] if n % 2 else (d2s[mid - 1] + d2s[mid]) / 2
    return {
        "n": n,
        "d1_never_broke_ma10_frac": d1 / n, "d1_count": d1,
        "d2": {"min": d2s[0], "max": d2s[-1], "mean": sum(d2s) / n, "median": median},
        "d3_broke_ma20_before_entry_frac": d3 / n, "d3_count": d3,
    }


def events_for_security(ts_code: str, rows: list,
                        in_pool: Optional[Callable[[str, dt.date], bool]] = None) -> list:
    """单票:后复权 close 序列(rows 按 trade_date 升序)→ 进场事件(可选 b1 池 PIT 过滤)。

    rows: PriceRow 列表(ViewReader/Synthetic;close 后复权)。in_pool: (ts,date)->bool,None=不过滤。
    """
    pairs = [(r.trade_date, r.close) for r in rows if r.close is not None]
    pairs.sort(key=lambda x: x[0])
    dates = [d for d, _ in pairs]
    closes = [c for _, c in pairs]
    out = []
    for e in generate_entries(closes):
        d = dates[e.entry_idx]
        pooled = True if in_pool is None else bool(in_pool(ts_code, d))
        if in_pool is not None and not pooled:
            continue                 # b1 池 PIT 过滤:进场日不在池 → 剔
        out.append(DrawdownEvent(
            ts_code=ts_code, event_date=d,
            event_id=f"{ts_code}:{d.strftime('%Y%m%d')}",
            d1_never_broke_ma10=e.d1_never_broke_ma10,
            d2_episode_to_entry_days=e.d2_episode_to_entry_days,
            d3_broke_ma20_before_entry=e.d3_broke_ma20_before_entry,
            in_pool=pooled))
    return out


def generate_events(reader, in_pool: Optional[Callable[[str, dt.date], bool]] = None) -> list:
    """全样本:reader.prices_by_security() 逐票 → #2b 进场事件列表(按 ts_code, event_date 排序)。

    in_pool=None → 原始信号事件(未过滤,供诊断/规模评估);传 b1 池成员判定 → 池内事件(#2b 正式样本)。
    """
    by_sec = reader.prices_by_security()
    out = []
    for ts in sorted(by_sec):
        out.extend(events_for_security(ts, by_sec[ts], in_pool))
    out.sort(key=lambda e: (e.ts_code, e.event_date))
    return out


if __name__ == "__main__":
    # 冒烟(合成/桩):构造两票各一条 R1 死锁序列,验事件生成 + 池过滤开关。
    import datetime as _dt
    from taosha.reader.contract import PriceRow

    def _mk_rows(ts, closes, start=_dt.date(2019, 1, 2)):
        rows, d = [], start
        out = []
        for c in closes:
            out.append(PriceRow(ts_code=ts, trade_date=d, close=c, is_suspended=False,
                                limit_status="none", board="main", is_st=False, industry="银行"))
            # 简化:连续自然日充当交易日轴(冒烟只验索引→date 映射与过滤)
            d = d + _dt.timedelta(days=1)
        return out

    R1 = ([100.0] * 40 + [100 - k * 0.75 for k in range(1, 21)] + [85.0] * 25
          + [86.0, 87.0, 88.0, 89.0, 90.0])
    rows_a = _mk_rows("A01", R1)

    class _Rd:
        def prices_by_security(self):
            return {"A01": rows_a}

    evs = generate_events(_Rd())
    assert len(evs) >= 1 and evs[0].ts_code == "A01", "事件生成"
    # 池过滤:全部剔除 → 空
    evs_pool = generate_events(_Rd(), in_pool=lambda ts, d: False)
    assert evs_pool == [], "池过滤(全不在池)→ 空"
    # 池过滤:全保留
    evs_keep = generate_events(_Rd(), in_pool=lambda ts, d: True)
    assert len(evs_keep) == len(evs) and evs_keep[0].in_pool is True, "池过滤(全在池)保留"
    print(f"drawdown_events.py 冒烟 OK:A01 进场 {len(evs)} 条(event_id={evs[0].event_id},"
          f"D1={evs[0].d1_never_broke_ma10}/D2={evs[0].d2_episode_to_entry_days}/"
          f"D3={evs[0].d3_broke_ma20_before_entry});池过滤开关生效")
