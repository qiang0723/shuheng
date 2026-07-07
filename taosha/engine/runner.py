"""淘沙 · engine · 执行器(切片2 spec §5 流程)。

exp_id(须 frozen)→ pap → explore_reader 拉数 → A股清洗 → compute → gates → result_json。
本模块只接**已冻结** pap(引擎拒 status≠frozen,铁律③;DB 绑定见 persist.py / ledger)。
合成验收:pap 由调用方以冻结字典传入(SYNTH 冒烟登记行的 pap_json),reader=SyntheticReader。

红线:一个数不改 pap;剔除是保守处置(偏差声明 report.py);报告只陈述统计事实。
"""
from __future__ import annotations

import datetime as dt
from statistics import NormalDist
from typing import Optional

from taosha.compute import frozen_ashare as fa
from taosha.compute import frozen_config as fc
from taosha.compute.abnormal_tests import (
    SecurityEvent, adj_bmp_by_tau, kp2010_factor, standardized_ar,
)
from taosha.compute.market_model import sim_fit
from taosha.engine import benchmark as bench
from taosha.engine.cleaning import CleanedEvent, clean_event, year_breakdown
from taosha.experiment import gates

Num = Optional[float]
ROBUST_LEN = fa.EVENT_WINDOW_ROBUST[1] + 1     # τ=0..5 → 6 点
MAIN_LEN = fa.EVENT_WINDOW_MAIN[1] + 1          # τ=0..2 → 3 点


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _sd(xs):
    xs = [x for x in xs if x is not None]
    n = len(xs)
    if n < 2:
        return None
    m = sum(xs) / n
    return (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5


def _car_test(events: list[SecurityEvent], window_len: int, rho_bar: float) -> dict:
    """窗口累计检验:CSAR_i=Σ_τ SAR_iτ,BMP_CAR=mean/sd·√N,ADJ=BMP_CAR·KP因子。

    逐日 SAR 复用 compute.standardized_ar;任一 τ 缺则该证券不进 CAR 截面(禁零填充)。
    """
    csars = []
    for ev in events:
        sar = standardized_ar(ev)[:window_len]
        if any(s is None for s in sar):
            continue
        csars.append(sum(sar))
    n = len(csars)
    if n < 2:
        return {"n": n, "bmp_car": None, "adj_bmp_car": None}
    m, s = sum(csars) / n, _sd(csars)
    bmp_car = (m / s * n ** 0.5) if s else None
    kp = kp2010_factor(rho_bar, n) if bmp_car is not None else None
    return {"n": n, "csar_mean": m, "csar_sd": s, "bmp_car": bmp_car,
            "kp_factor": kp, "adj_bmp_car": (bmp_car * kp) if bmp_car is not None else None}


def run_study(reader, pap: dict, *, benchmark_mode: str = "market",
              pool: Optional[set] = None) -> dict:
    """跑一条已冻结假设的事件研究,返回 result 字典(供 report + 落库)。

    benchmark_mode: 'market'(全市场等权)/'pool'(池内等权)——口径②冻结基准二选一。
    pool: benchmark_mode='pool' 时的池成员 ts_code 集合。
    """
    # ── 拉数 + date 轴 ────────────────────────────────────────────────────────
    by_sec = reader.prices_by_security()
    all_dates = sorted({r.trade_date for rows in by_sec.values() for r in rows})
    date_index = {d: j for j, d in enumerate(all_dates)}
    n_dates = len(all_dates)

    # ── 收益 + 等权基准(口径②)──────────────────────────────────────────────
    sec_returns = {ts: bench.returns_by_date(rows, all_dates) for ts, rows in by_sec.items()}
    if benchmark_mode == "pool":
        mkt = bench.pool_equal_weight_market(sec_returns, pool or set(by_sec), n_dates)
    else:
        mkt = bench.equal_weight_market(sec_returns, n_dates)

    # ── 逐事件清洗 + compute ──────────────────────────────────────────────────
    cleaned: list[CleanedEvent] = []
    valid_events: list[SecurityEvent] = []
    for ev in reader.events():
        rows = by_sec.get(ev.ts_code, [])
        ce = clean_event(rows, ev, date_index)
        if ce.rejected:
            cleaned.append(ce)
            continue
        # SIM 拟合(估计窗覆盖 = SimFit.delta)
        est_lo = ce.t_idx + fc.EST_WINDOW_OFFSET_START
        est_hi = ce.t_idx + fc.EST_WINDOW_OFFSET_END
        est_mask = [est_lo <= j <= est_hi for j in range(n_dates)]
        sret = sec_returns[ev.ts_code]
        try:
            fit = sim_fit(sret, mkt, est_mask)
        except ValueError:
            ce.rejected, ce.reject_reason, ce.reject_year = True, "coverage", ce.first_ann_date.year
            ce.notes.append("估计样本不足,OLS 无法估计 → 剔除")
            cleaned.append(ce)
            continue
        ce.coverage_valid_days = fit.delta
        ce.coverage_ok = fc.coverage_ok(fit.delta)
        if not ce.coverage_ok:
            ce.rejected, ce.reject_reason, ce.reject_year = True, "coverage", ce.first_ann_date.year
            ce.notes.append(f"估计窗有效交易日 {fit.delta} < {fc.COVERAGE_MIN_VALID}(70%×160)→ 剔除(item 6)")
            cleaned.append(ce)
            continue
        # 事件窗 τ=0..ROBUST(τ=0=tau0_idx=T+1,含一字板顺延)
        w_idx = [ce.tau0_idx + k for k in range(ROBUST_LEN)]
        if w_idx[-1] >= n_dates:
            ce.rejected, ce.reject_reason, ce.reject_year = True, "history", ce.first_ann_date.year
            ce.notes.append("事件窗右端越界(尾部数据不足)→ 剔除")
            cleaned.append(ce)
            continue
        est_ar_by_date = {all_dates[j]: fit.abnormal[j]
                          for j in range(est_lo, est_hi + 1) if fit.abnormal[j] is not None}
        se = SecurityEvent(
            est_ar_sd=fit.est_ar_sd, L=fit.delta, x_bar=fit.x_bar, sxx=fit.sxx,
            event_market=[mkt[j] for j in w_idx],
            event_abnormal=[fit.abnormal[j] for j in w_idx],
            industry=ce.industry, est_ar_by_date=est_ar_by_date,
        )
        se_meta = {"ts_code": ev.ts_code, "event_id": ev.event_id, "board": ce.board,
                   "regime_segment": ce.regime_segment, "industry": ce.industry,
                   "postponed": ce.postponed}
        valid_events.append((se, se_meta))
        cleaned.append(ce)

    return _assemble(pap, cleaned, valid_events, benchmark_mode)


def _assemble(pap, cleaned, valid_events, benchmark_mode) -> dict:
    ses = [se for se, _ in valid_events]
    n = len(ses)
    family_trial = int(pap.get("_family_trial", 1))
    alpha = gates.family_alpha(family_trial)
    sample_state = gates.sample_verdict(n)

    # 逐日 AR 标准输出(item 8)+ 主/稳健窗 BMP/ADJ-BMP
    per_tau, car = {}, {}
    if n >= 1:
        adj = adj_bmp_by_tau(ses)
        rho = adj["rho"]
        rows = adj["rows"]
        aar = [_mean([se.event_abnormal[t] for se in ses]) for t in range(ROBUST_LEN)]
        per_tau = {
            "tau_axis": "τ=0:=T+1(首个可交易日,S2-DEC3)",
            "rho_bar": rho["rho_bar"], "rho_n_pairs": rho["n_pairs"], "rho_note": rho["note"],
            "by_tau": [{"tau": r["tau"], "n": r["n"], "aar": aar[r["tau"]],
                        "bmp": r["bmp"], "adj_bmp": r["adj_bmp"]} for r in rows],
        }
        car = {
            "main_window": {"taus": f"[0,+{fa.EVENT_WINDOW_MAIN[1]}]",
                            "caar": sum(a for a in aar[:MAIN_LEN] if a is not None),
                            **_car_test(ses, MAIN_LEN, rho["rho_bar"])},
            "robust_window": {"taus": f"[0,+{fa.EVENT_WINDOW_ROBUST[1]}]",
                              "caar": sum(a for a in aar[:ROBUST_LEN] if a is not None),
                              **_car_test(ses, ROBUST_LEN, rho["rho_bar"])},
        }

    # 板块分层(item 8):有效事件按 board 计数 + 主窗 CAAR;ST 层为已剔除层
    strata = _board_strata(cleaned, valid_events)

    # 剔除率按年份(item 7)
    rej = year_breakdown(cleaned)

    # verdict(切片2 主检验=ADJ-BMP;稳健性 秩/日历 待范围确认,robustness_pending)
    verdict, verdict_note = _verdict(sample_state, car, alpha)

    # 覆盖统计(item 6):有效事件估计窗有效交易日分布(分母 160,门槛 112)
    cov_days = [ce.coverage_valid_days for ce in cleaned
                if not ce.rejected and ce.coverage_valid_days is not None]
    coverage = {"denominator": fc.EST_WINDOW_LEN, "min_valid": fc.COVERAGE_MIN_VALID,
                "n_valid_events": len(cov_days),
                "valid_days_min": min(cov_days) if cov_days else None,
                "valid_days_max": max(cov_days) if cov_days else None,
                "valid_days_mean": (sum(cov_days) / len(cov_days)) if cov_days else None}

    return {
        "audit": {
            "frozen_config_digest": fc.audit_digest(),
            "frozen_ashare_digest": fa.audit_digest(),
            "benchmark_mode": benchmark_mode,
            "family_trial": family_trial, "family_alpha": alpha,
        },
        "n_events_valid": n, "n_events_total": rej["total"],
        "sample_gate": {"gate": gates.SAMPLE_GATE, "state": sample_state},
        "coverage": coverage,
        "rejections": rej,
        "n_eff": n,                          # N_eff = 有效事件数(与剔除率同报,item 11)
        "per_tau": per_tau, "car": car,
        "board_strata": strata,
        "verdict": verdict, "verdict_note": verdict_note,
        "snapshot_batch": pap.get("snapshot_batch_req", "SYNTH"),
    }


def _board_strata(cleaned, valid_events) -> dict:
    """板块分层报告(item 8):main/chinext/star/ST。ST=已剔除层(spec §5 剔除,分层留痕)。
    创业板另报 regime 分段(2020-08-24 前/后)计数。"""
    strata: dict = {}
    for ce in cleaned:
        key = "ST" if ce.is_st else ce.board
        s = strata.setdefault(key, {"total": 0, "valid": 0, "rejected": 0})
        s["total"] += 1
        if ce.rejected:
            s["rejected"] += 1
        else:
            s["valid"] += 1
    # 创业板 regime 边界(item 8):有效创业板事件按分段计数
    cx_seg: dict = {"pre_10pct": 0, "post_20pct": 0}
    for se, m in valid_events:
        if m["board"] == "chinext":
            cx_seg[m["regime_segment"]] += 1
    strata["_chinext_regime"] = {"boundary": fa.CHINEXT_REGIME_DATE.isoformat(), **cx_seg}
    strata["_st_note"] = "ST 为已剔除层(spec §5 ST 剔除);不进池化检验,分层仅计数留痕(item 8 调和)"
    return strata


def _verdict(sample_state, car, alpha) -> tuple[str, str]:
    if sample_state == "INSUFFICIENT":
        return "INSUFFICIENT", f"有效事件 < {gates.SAMPLE_GATE}(样本量闸;合法终态,非报错)"
    if not car or car["main_window"].get("adj_bmp_car") is None:
        return "AMBIGUOUS", "主窗 ADJ-BMP 不可得(截面不足)"
    z_crit = NormalDist().inv_cdf(1 - alpha / 2)
    adj = car["main_window"]["adj_bmp_car"]
    sig = abs(adj) > z_crit
    note = (f"主窗 ADJ-BMP_CAR={adj:.3f} vs 双侧临界 ±{z_crit:.3f}(α={alpha});"
            "⚠ 稳健性两道(Corrado 秩/日历时间组合)待范围确认,未纳入 verdict;"
            "spec §6 三法一致规则在补齐后方生效(robustness_pending)。")
    return ("SIG" if sig else "NOT_SIG"), note
