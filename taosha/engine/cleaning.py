"""淘沙 · engine · A股清洗预处理(切片2 item 6/7/8;spec §5)。

对每个事件做几何与合格性判定,动作全落 result(可审计):
  - 估计窗 [T-250, T-91](160 日),覆盖门槛由 compute 侧 SimFit.delta 判(item 6)。
  - 事件落停牌期 → 剔除(item 7);剔除原因 + 年份记账。
  - ST → 剔除(spec §5"ST 剔除");板块分层报告仍计其为"ST 层(已剔除)"(item 8;
    与 item 8"ST 分层"的调和:ST 从检验样本剔除、在板块分层里作已剔除层留痕、不进池化检验)。
  - 一字板 T+1 → 事件窗顺延(item 8;τ=0 移到首个可成交日)。
  - τ 轴:τ=0 := 首个可交易日 = T+1(S2-DEC3);盘后披露前视规避。

红线:不发明口径;剔除是保守处置(偏差方向声明见 report.py)。纯函数(除读价格行)。
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

from taosha.compute import frozen_ashare as fa
from taosha.compute import frozen_config as fc
from taosha.reader.contract import PriceRow

# 顺延上限:一字板连封超过此数视为无法进场(事件不可用)
MAX_POSTPONE = 5


@dataclass
class CleanedEvent:
    """单事件清洗结果(几何 + 合格性;compute 前)。"""
    ts_code: str
    event_id: str
    first_ann_date: dt.date
    board: str
    is_st: bool
    industry: str
    regime_segment: str                       # 创业板 regime 分段(pre_10pct/post_20pct);他板同样标注
    t_idx: int                                # 事件日 T 在 date 轴索引
    rejected: bool = False
    reject_reason: Optional[str] = None        # 'history'/'suspension'/'st'/'coverage'/'postpone'
    reject_year: Optional[int] = None
    tau0_idx: Optional[int] = None            # τ=0(首个可交易日=T+1,含顺延)date 轴索引
    postponed: int = 0                        # 一字板顺延交易日数
    coverage_valid_days: Optional[int] = None  # 估计窗内有效交易日(compute 回填 delta)
    coverage_ok: Optional[bool] = None
    notes: list[str] = field(default_factory=list)


def _est_window_idx(t_idx: int) -> tuple[int, int]:
    """估计窗 date 轴索引区间 [T-250, T-91](含端点),口径③冻结。"""
    return t_idx + fc.EST_WINDOW_OFFSET_START, t_idx + fc.EST_WINDOW_OFFSET_END


def clean_event(rows: list[PriceRow], event, date_index: dict) -> CleanedEvent:
    """对一个事件做清洗几何 + 前置剔除(停牌/ST/顺延)。覆盖门槛留 compute 回填。

    rows: 该证券按 trade_date 升序的全期 PriceRow;event: EventRow;date_index: {date: idx}。
    """
    t_idx = date_index.get(event.first_ann_date)
    r0 = rows[0]
    ce = CleanedEvent(
        ts_code=event.ts_code, event_id=event.event_id,
        first_ann_date=event.first_ann_date, board=r0.board, is_st=r0.is_st,
        industry=r0.industry, regime_segment=fa.regime_segment(event.first_ann_date),
        t_idx=t_idx if t_idx is not None else -1,
    )
    yr = event.first_ann_date.year

    # 事件日不在交易轴(不应发生于合成域)→ 剔除
    if t_idx is None:
        ce.rejected, ce.reject_reason, ce.reject_year = True, "history", yr
        ce.notes.append("事件日非交易日,无法定位")
        return ce

    # 历史不足:估计窗左端越界(< 250 日历史)→ 剔除
    est_lo, est_hi = _est_window_idx(t_idx)
    if est_lo < 0:
        ce.rejected, ce.reject_reason, ce.reject_year = True, "history", yr
        ce.notes.append(f"估计窗左端越界(需 ≥250 日历史,T_idx={t_idx})")
        return ce

    by_idx = {date_index[r.trade_date]: r for r in rows}

    # ST 剔除(spec §5);板块分层里作"ST 已剔除层"留痕(item 8 调和)
    if ce.is_st:
        ce.rejected, ce.reject_reason, ce.reject_year = True, "st", yr
        ce.notes.append("ST 剔除(spec §5);板块分层计入 ST 已剔除层")
        return ce

    # 事件落停牌期(item 7):事件日 T 或首个拟交易日 T+1 停牌 → 剔除
    t_row = by_idx.get(t_idx)
    t1_row = by_idx.get(t_idx + 1)
    if (t_row and t_row.is_suspended) or (t1_row and t1_row.is_suspended):
        ce.rejected, ce.reject_reason, ce.reject_year = True, "suspension", yr
        ce.notes.append("事件落停牌期(T 或 T+1 停牌)→ 剔除(item 7)")
        return ce

    # 一字板顺延(item 8):τ=0 = 首个 T+1 起可成交(非一字板、非停牌)日
    tau0 = t_idx + 1
    postpone = 0
    while True:
        row = by_idx.get(tau0)
        if row is None:                          # 越出交易轴末端
            break
        blocked = row.is_suspended or row.limit_status == "one_word"
        if not blocked:
            break
        tau0 += 1
        postpone += 1
        if postpone > MAX_POSTPONE:
            ce.rejected, ce.reject_reason, ce.reject_year = True, "postpone", yr
            ce.notes.append(f"一字板顺延超 {MAX_POSTPONE} 日,事件不可进场 → 剔除")
            return ce
    ce.tau0_idx = tau0
    ce.postponed = postpone
    if postpone:
        ce.notes.append(f"一字板顺延 {postpone} 交易日,τ=0 移至 idx={tau0}(item 8)")
    return ce


def year_breakdown(cleaned: list[CleanedEvent]) -> dict:
    """剔除率按年份分解(item 7)。返回 {year: {total, rejected, by_reason, reject_ratio}} + 汇总。"""
    years: dict[int, dict] = {}
    for ce in cleaned:
        y = ce.reject_year if ce.reject_year is not None else ce.first_ann_date.year
        d = years.setdefault(y, {"total": 0, "rejected": 0, "by_reason": {}})
        d["total"] += 1
        if ce.rejected:
            d["rejected"] += 1
            d["by_reason"][ce.reject_reason] = d["by_reason"].get(ce.reject_reason, 0) + 1
    for y, d in years.items():
        d["reject_ratio"] = d["rejected"] / d["total"] if d["total"] else 0.0
    total = sum(d["total"] for d in years.values())
    rej = sum(d["rejected"] for d in years.values())
    return {
        "by_year": dict(sorted(years.items())),
        "total": total, "rejected": rej,
        "reject_ratio": (rej / total) if total else 0.0,
        "alert": (rej / total) > fa.SUSPENSION_ALERT_RATIO if total else False,
        "alert_threshold": fa.SUSPENSION_ALERT_RATIO,
    }
