"""淘沙 · engine · 事件存活样本构造单一主干(硬化④,宪章第5条实质验收)。

clean_event → SIM 拟合(估计窗)→ coverage 门槛 → robust 检验窗右端越界:同序同判据的唯一实现,
事件版 runner 与策略版 drawdown_strategy 共同调用——平行链消灭(不是拆短函数,是消灭第二条实现)。
两侧原有差异以参数盖:sec_returns 预物化(pool/合成域)/惰性单键缓存(真实域)两分支、
剔除 notes 文案(事件版报告消费,策略版不落);消费端(SecurityEvent 构造/持有路径)各留各。
流式生成器:逐事件 yield、不物化 fit 全集(#4 六万存活若齐持 SimFit.abnormal 稠密列即内存灾难,
与提取前 runner 事件循环内存轮廓等价)。
"""
from __future__ import annotations

from typing import Iterator, Optional

from taosha.compute import frozen_config as fc
from taosha.compute.market_model import sim_fit
from taosha.engine import benchmark as bench
from taosha.engine.cleaning import CleanedEvent, clean_event


def iter_survivors(event_src, by_sec, all_dates, date_index, mkt, robust_len, *,
                   st_mode: str, st_policy: str = "reject", sec_returns: Optional[dict] = None,
                   reject_notes: bool = False) -> Iterator[tuple[CleanedEvent, Optional[tuple]]]:
    """逐事件产出 (ce, survivor):剔除 → (ce, None);存活 → (ce, (ev, ce, fit, est_ar_by_date, rows))。

    sec_returns: 预物化收益字典(pool/合成域);None → 惰性单键缓存(events 按 ts_code 有序,
      免同票重算、内存 O(1票),同提取前 runner/策略版)。
    reject_notes: True=剔除原因落 ce.notes(事件版既有文案逐字);False=不落(策略版既有行为)。
    st_policy: ST 处置(回修单元 C2 乙案,2026-07-17):'reject' 默认=spec §5 剔除(零回归)/
      'keep'=保留入主样本(exp8);穿线至 clean_event,本函数零判断。
    """
    n_dates = len(all_dates)
    _ret_cache: dict = {}
    for ev in event_src:
        rows = by_sec.get(ev.ts_code, [])
        ce = clean_event(rows, ev, date_index, st_mode=st_mode, st_policy=st_policy)
        if ce.rejected:
            yield ce, None
            continue
        # SIM 拟合(估计窗覆盖 = SimFit.delta)
        est_lo = ce.t_idx + fc.EST_WINDOW_OFFSET_START
        est_hi = ce.t_idx + fc.EST_WINDOW_OFFSET_END
        est_mask = [est_lo <= j <= est_hi for j in range(n_dates)]
        if sec_returns is not None:
            sret = sec_returns[ev.ts_code]           # pool/合成域:全量预物化
        else:                                        # 真实域:按票现算(单键缓存,与预物化等价)
            if ev.ts_code not in _ret_cache:
                _ret_cache.clear()
                _ret_cache[ev.ts_code] = bench.returns_by_date(rows, all_dates)
            sret = _ret_cache[ev.ts_code]
        try:
            fit = sim_fit(sret, mkt, est_mask)
        except ValueError:
            ce.rejected, ce.reject_reason, ce.reject_year = True, "coverage", ce.first_ann_date.year
            if reject_notes:
                ce.notes.append("估计样本不足,OLS 无法估计 → 剔除")
            yield ce, None
            continue
        ce.coverage_valid_days = fit.delta
        ce.coverage_ok = fc.coverage_ok(fit.delta)
        if not ce.coverage_ok:
            ce.rejected, ce.reject_reason, ce.reject_year = True, "coverage", ce.first_ann_date.year
            if reject_notes:
                ce.notes.append(f"估计窗有效交易日 {fit.delta} < {fc.COVERAGE_MIN_VALID}(70%×160)→ 剔除(item 6)")
            yield ce, None
            continue
        # 检验窗 τ=0..robust_len-1 右端越界(尾部数据不足)——同源同判据
        if ce.tau0_idx + robust_len - 1 >= n_dates:
            ce.rejected, ce.reject_reason, ce.reject_year = True, "history", ce.first_ann_date.year
            if reject_notes:
                ce.notes.append("事件窗右端越界(尾部数据不足)→ 剔除")
            yield ce, None
            continue
        est_ar_by_date = {all_dates[j]: fit.abnormal[j]
                          for j in range(est_lo, est_hi + 1) if fit.abnormal[j] is not None}
        yield ce, (ev, ce, fit, est_ar_by_date, rows)


if __name__ == "__main__":
    # 自检(硬化④随件回归):R1 预物化/惰性两分支逐值等价;R2 reject_notes 只影响 notes
    # 不影响判定;R3 coverage 门槛剔除;R4 robust 窗右端越界=history(同判据)。
    import datetime as dt
    import math

    from taosha.reader.contract import PriceRow

    base = dt.date(2019, 1, 1)
    N = 400
    dates = [base + dt.timedelta(days=i) for i in range(N)]
    di = {d: i for i, d in enumerate(dates)}
    mkt = [None] + [(0.002 if i % 2 else -0.001) for i in range(1, N)]

    def _rows(ts, skip=()):
        return [PriceRow(ts, dates[i], 100.0 + 0.5 * math.sin(i), False, "none", "main", False, "I")
                for i in range(N) if i not in skip]

    class _Ev:
        def __init__(self, ts, d):
            self.ts_code, self.event_id, self.first_ann_date = ts, f"{ts}:e", d

    T_OK, T_END = 300, 395
    gap60 = set(range(T_OK - 250, T_OK - 190))       # 估计窗挖 60 日 → delta≈100 < 112(门槛)
    by_sec = {"S1": _rows("S1"), "S2": _rows("S2", skip=gap60), "S3": _rows("S3")}
    evs = [_Ev("S1", dates[T_OK]), _Ev("S2", dates[T_OK]), _Ev("S3", dates[T_END])]

    def _run(**kw):
        return list(iter_survivors(evs, by_sec, dates, di, mkt, 20, st_mode="event_day", **kw))

    lazy = _run()
    # R1 预物化 == 惰性(fit 逐值)
    pre = {ts: bench.returns_by_date(rows, dates) for ts, rows in by_sec.items()}
    mat = _run(sec_returns=pre)
    assert [(c.rejected, c.reject_reason) for c, _ in lazy] == [(c.rejected, c.reject_reason) for c, _ in mat]
    f_l, f_m = lazy[0][1][2], mat[0][1][2]
    assert (f_l.est_ar_sd, f_l.delta, f_l.x_bar, f_l.sxx) == (f_m.est_ar_sd, f_m.delta, f_m.x_bar, f_m.sxx)
    assert lazy[0][1][3] == mat[0][1][3]             # est_ar_by_date 逐值
    # R2 reject_notes 只加文案不改判定
    noted = _run(reject_notes=True)
    assert [(c.rejected, c.reject_reason) for c, _ in noted] == [(c.rejected, c.reject_reason) for c, _ in lazy]
    assert noted[1][0].notes != [] and lazy[1][0].notes == []
    # R3 S2=coverage 门槛剔除(sim 可估但 delta<112);R4 S3=robust 越界 history
    assert lazy[0][1] is not None and not lazy[0][0].rejected
    assert lazy[1][1] is None and lazy[1][0].reject_reason == "coverage"
    assert lazy[2][1] is None and lazy[2][0].reject_reason == "history"
    assert "70%×160" in noted[1][0].notes[-1] and "右端越界" in noted[2][0].notes[-1]
    print(f"survivors.py 自检 OK:预物化/惰性等价(delta={f_l.delta})/notes只加文案/"
          f"coverage门槛/robust越界history 同判据(单一主干,硬化④)")
