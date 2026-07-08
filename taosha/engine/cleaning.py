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


def _norm_industry(x):
    """industry 缺失(None/''/'nan'/'none'/'null')→ 显式 'unknown' 残余组(人批 2026-07-08:
    不猜不补)。ρ̄ 口径④按此分组、'unknown' 单独成组;报告附占比、>5% 事件升级上报(见 runner/report)。"""
    if x is None:
        return "unknown"
    s = str(x).strip()
    return "unknown" if s.lower() in ("", "nan", "none", "null") else s


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
    event_type_layer: str = "unknown"         # 三层(预喜/预亏/扭亏);供剔除分布的层维度分解(停牌回炉议题)
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
    yr = event.first_ann_date.year
    layer = getattr(event, "event_type_layer", "unknown")   # 层维度(合成自检 _Ev 无此属性 → unknown)

    # 无价行前置剔除(人批 2026-07-08):事件票在价视图无 bar(真实域可能:退市/无holdout前史)。
    #   数据残缺样本 → 剔除 no_price(计入年份剔除报告 + 偏差声明保守方向),不以残缺样本充数。
    if not rows:
        ce = CleanedEvent(
            ts_code=event.ts_code, event_id=event.event_id,
            first_ann_date=event.first_ann_date, board="unknown", is_st=False,
            industry="unknown", regime_segment=fa.regime_segment(event.first_ann_date), t_idx=-1,
            event_type_layer=layer)
        ce.rejected, ce.reject_reason, ce.reject_year = True, "no_price", yr
        ce.notes.append("无价行(事件票在价视图无 bar)→ 剔除(no_price;数据残缺,保守偏差)")
        return ce

    t_idx = date_index.get(event.first_ann_date)
    r0 = rows[0]
    ce = CleanedEvent(
        ts_code=event.ts_code, event_id=event.event_id,
        first_ann_date=event.first_ann_date, board=r0.board, is_st=r0.is_st,
        industry=_norm_industry(r0.industry), regime_segment=fa.regime_segment(event.first_ann_date),
        t_idx=t_idx if t_idx is not None else -1, event_type_layer=layer,
    )

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
    n_dates = len(date_index)

    # 停牌判据(约束② 2026-07-07,原文即口径):停牌 = 轴内缺行(calendar 断档,真实数据)
    #   OR is_suspended flag(合成 fixture 兼容);与一字板(有 bar + limit_status='one_word')
    #   **物理判据不同**(一字板必有 bar、停牌必无 bar 或 flag)。轴外(idx<0 或 >=n)非停牌(数据边界)。
    def _suspended(idx: int) -> bool:
        if idx < 0 or idx >= n_dates:
            return False
        row = by_idx.get(idx)
        if row is None:
            return True                # 缺行 = 停牌(calendar 断档;真实数据)
        return row.is_suspended        # flag(合成 fixture 停牌行)

    # ST 剔除(spec §5);板块分层里作"ST 已剔除层"留痕(item 8 调和)
    if ce.is_st:
        ce.rejected, ce.reject_reason, ce.reject_year = True, "st", yr
        ce.notes.append("ST 剔除(spec §5);板块分层计入 ST 已剔除层")
        return ce

    # 事件落停牌期(item 7):事件日 T 或首个拟交易日 T+1 停牌 → 剔除
    if _suspended(t_idx) or _suspended(t_idx + 1):
        ce.rejected, ce.reject_reason, ce.reject_year = True, "suspension", yr
        ce.notes.append("事件落停牌期(T 或 T+1 停牌;缺行或 flag)→ 剔除(item 7)")
        return ce

    # 一字板顺延(item 8):τ=0 = 首个 T+1 起可成交(非一字板、非停牌)日。
    #   停牌(缺行/flag)与一字板(有 bar + one_word)判据**分离**(约束②);两者皆不可成交 → 顺延。
    tau0 = t_idx + 1
    postpone = 0
    while True:
        if tau0 >= n_dates:                      # 越出交易轴末端(数据边界,非停牌)
            break
        row = by_idx.get(tau0)
        suspended = _suspended(tau0)             # 缺行 OR flag
        one_word = (row is not None and row.limit_status == "one_word")  # 有 bar + 触板
        # 杂交检测(约束②):同位置既含停牌信号又是一字板 → 如实上报、不自行归类(保守仍视不可成交)
        if row is not None and one_word and (row.is_suspended or row.close is None):
            ce.notes.append(
                f"⚠ 一字板×停牌信号杂交(idx={tau0}:limit_status='one_word' 且 "
                f"is_suspended={row.is_suspended}/close={'None' if row.close is None else '有'})"
                f"→ 如实标注、不自行归类,保守视为不可成交顺延")
        blocked = suspended or one_word
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


def layer_year_breakdown(cleaned: list[CleanedEvent]) -> dict:
    """剔除分布**分层×年份×原因**分解(停牌回炉议题层维度,2026-07-08 议毕补数据)。

    top-level year_breakdown 为合并口径;本函数按三层(good/bad/turnaround)各出 by_year(含
    by_reason),供复核"停牌剔除年份偏斜是否另有层维度偏斜"。纯计数、不下结论(报告项)。
    返回 {layer: {by_year:{...}, total, rejected, reject_ratio,
                  by_reason_total:{reason:count}}}。"""
    out: dict = {}
    for ce in cleaned:
        lay = ce.event_type_layer or "unknown"
        y = ce.reject_year if ce.reject_year is not None else ce.first_ann_date.year
        L = out.setdefault(lay, {"by_year": {}, "by_reason_total": {}})
        d = L["by_year"].setdefault(y, {"total": 0, "rejected": 0, "by_reason": {}})
        d["total"] += 1
        if ce.rejected:
            d["rejected"] += 1
            d["by_reason"][ce.reject_reason] = d["by_reason"].get(ce.reject_reason, 0) + 1
            L["by_reason_total"][ce.reject_reason] = L["by_reason_total"].get(ce.reject_reason, 0) + 1
    for lay, L in out.items():
        for y, d in L["by_year"].items():
            d["reject_ratio"] = d["rejected"] / d["total"] if d["total"] else 0.0
        L["by_year"] = dict(sorted(L["by_year"].items()))
        L["total"] = sum(d["total"] for d in L["by_year"].values())
        L["rejected"] = sum(d["rejected"] for d in L["by_year"].values())
        L["reject_ratio"] = (L["rejected"] / L["total"]) if L["total"] else 0.0
    return dict(sorted(out.items()))


if __name__ == "__main__":
    # 约束②(2026-07-07)自检:停牌=缺行 OR flag、一字板=有bar+触板、判据分离、杂交上报。
    def _mk(d, one_word=False, susp=False):
        return PriceRow("A", d, (None if susp else 10.0), susp,
                        ("one_word" if one_word else "none"), "main", False, "I")

    class _Ev:
        ts_code = "A"; event_id = "A:e"
        def __init__(self, d): self.first_ann_date = d

    _b = dt.date(2020, 1, 1)
    _ds = [_b + dt.timedelta(days=i) for i in range(320)]
    _di = {d: i for i, d in enumerate(_ds)}
    _t = 260
    _ev = _Ev(_ds[_t])
    # 1) 缺行 T+1 → 停牌剔除(真实路径:轴内缺行=停牌)
    _c = clean_event([_mk(_ds[i]) for i in range(320) if i != _t + 1], _ev, _di)
    assert _c.rejected and _c.reject_reason == "suspension", "缺行停牌"
    # 2) flag 停牌 T+1 → 剔除(合成兼容)
    _c = clean_event([_mk(_ds[i], susp=(i == _t + 1)) for i in range(320)], _ev, _di)
    assert _c.rejected and _c.reject_reason == "suspension", "flag 停牌"
    # 3) 一字板(T+1)+缺行停牌(T+2)顺延 → τ0=T+3、postpone=2(判据分离,缺行也顺延)
    _c = clean_event([_mk(_ds[i], one_word=(i == _t + 1)) for i in range(320) if i != _t + 2], _ev, _di)
    assert not _c.rejected and _c.tau0_idx == _t + 3 and _c.postponed == 2, "顺延跨缺行"
    # 4) 杂交(one_word 且 is_suspended)→ 如实标注、不归类
    _r = [_mk(_ds[i], one_word=(i == _t + 1)) for i in range(320)]
    _r[_t + 2] = PriceRow("A", _ds[_t + 2], None, True, "one_word", "main", False, "I")
    _c = clean_event(_r, _ev, _di)
    assert any("杂交" in n for n in _c.notes), "杂交检测"
    # 5) 无价行 → no_price 剔除(人批 2026-07-08;board/industry=unknown,入年份剔除报告)
    _c = clean_event([], _ev, _di)
    assert _c.rejected and _c.reject_reason == "no_price" and _c.industry == "unknown", "无价行剔除"
    assert year_breakdown([_c])["by_year"][_c.first_ann_date.year]["by_reason"].get("no_price") == 1
    # 6) industry 归一:缺失变体 → 'unknown' 残余组;正常值保留(人批 2026-07-08)
    assert _norm_industry("nan") == "unknown" and _norm_industry(None) == "unknown"
    assert _norm_industry("") == "unknown" and _norm_industry(" NaN ") == "unknown" and _norm_industry("null") == "unknown"
    assert _norm_industry("银行") == "银行"
    print("cleaning.py 自检 OK:缺行=停牌 / flag兼容 / 判据分离顺延跨缺行 / 杂交上报(约束②) / "
          "无价行=no_price剔除 / industry缺失→unknown(人批2026-07-08)")
