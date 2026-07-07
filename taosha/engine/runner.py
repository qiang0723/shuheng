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
from taosha.compute.calendar_pf import CalEvent, calendar_time
from taosha.compute.market_model import sim_fit
from taosha.compute.rank_test import RankSecurity, corrado_rank
from taosha.engine import benchmark as bench
from taosha.engine.cleaning import CleanedEvent, clean_event, year_breakdown
from taosha.experiment import gates
from taosha.experiment.pap import parse_test_windows

Num = Optional[float]
# 检验窗从 pap 读取(裁定 2026-07-07:事件窗属事件定义、台账为唯一事实源),运行时解析,
# 不再取 frozen_ashare.EVENT_WINDOW(那两值已降格为删失诊断窗,见 frozen_ashare 注释)。
# 删失诊断窗(frozen 诊断窗)点数——强制并行输出、与检验窗互不替代(R5 本义):
DIAG_MAIN_LEN = fa.EVENT_WINDOW_MAIN[1] + 1      # 删失诊断窗 τ=0..2 → 3 点
DIAG_ROBUST_LEN = fa.EVENT_WINDOW_ROBUST[1] + 1  # 删失诊断窗 τ=0..5 → 6 点


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
    # ── 检验窗从 pap 读(裁定 2026-07-07):main/robust = 首/末检验窗点数(#4=(20,60))──
    test_win = parse_test_windows(pap)
    main_len, robust_len = test_win[0], test_win[-1]

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
        # 事件窗 τ=0..robust_len-1(检验窗,τ=0=tau0_idx=T+1,含一字板顺延)
        w_idx = [ce.tau0_idx + k for k in range(robust_len)]
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
        # 删失诊断窗(步3b,R5):诊断窗 τ=0..DIAG_ROBUST_LEN-1 各日删失类型(不进 verdict,报告项)
        ev_by_idx = {date_index[r.trade_date]: r for r in rows}

        def _censor_at(idx, _bi=ev_by_idx):
            if idx >= n_dates:
                return "none"
            row = _bi.get(idx)
            if row is None or row.is_suspended:   # 缺行 OR flag = 停牌(约束②)
                return "suspend"
            if row.limit_status == "one_word":
                return "one_word"
            if row.limit_status in ("limit_up", "limit_down"):
                return row.limit_status
            return "none"

        diag_censor = [_censor_at(ce.tau0_idx + k) for k in range(DIAG_ROBUST_LEN)]
        se_meta = {"ts_code": ev.ts_code, "event_id": ev.event_id, "board": ce.board,
                   "regime_segment": ce.regime_segment, "industry": ce.industry,
                   "postponed": ce.postponed, "is_st": ce.is_st, "diag_censor": diag_censor}
        # 秩检验输入:估计窗 AR(相对位置 -250..-91)+ 事件窗 AR;日历法输入:窗内日期+AR
        est_ar_seq = [fit.abnormal[j] for j in range(est_lo, est_hi + 1)]
        w_dates = [all_dates[j] for j in w_idx]
        rank_sec = RankSecurity(est_ar_seq, se.event_abnormal)
        cal_ev = CalEvent(w_dates, se.event_abnormal)
        valid_events.append((se, se_meta, rank_sec, cal_ev))
        cleaned.append(ce)

    return _assemble(pap, cleaned, valid_events, benchmark_mode, main_len, robust_len)


def _assemble(pap, cleaned, valid_events, benchmark_mode, main_len, robust_len) -> dict:
    ses = [v[0] for v in valid_events]
    rank_secs = [v[2] for v in valid_events]
    cal_evs = [v[3] for v in valid_events]
    n = len(ses)
    family_trial = int(pap.get("_family_trial", 1))
    alpha = gates.family_alpha(family_trial)
    sample_state = gates.sample_verdict(n)

    # 逐日 AR 标准输出(item 8)+ 主/稳健窗 BMP/ADJ-BMP + 三法(ADJ-BMP/秩/日历)
    per_tau, car, robustness = {}, {}, {}
    if n >= 1:
        adj = adj_bmp_by_tau(ses)
        rho = adj["rho"]
        rows = adj["rows"]
        aar = [_mean([se.event_abnormal[t] for se in ses]) for t in range(robust_len)]
        per_tau = {
            "tau_axis": "τ=0:=T+1(首个可交易日,S2-DEC3)",
            "rho_bar": rho["rho_bar"], "rho_n_pairs": rho["n_pairs"], "rho_note": rho["note"],
            "by_tau": [{"tau": r["tau"], "n": r["n"], "aar": aar[r["tau"]],
                        "bmp": r["bmp"], "adj_bmp": r["adj_bmp"]} for r in rows],
        }
        car = {
            "main_window": {"taus": f"[0,+{main_len-1}]",
                            "caar": sum(a for a in aar[:main_len] if a is not None),
                            "naive_t": _naive_t([se.event_abnormal for se in ses], main_len),
                            **_car_test(ses, main_len, rho["rho_bar"])},
            "robust_window": {"taus": f"[0,+{robust_len-1}]",
                              "caar": sum(a for a in aar[:robust_len] if a is not None),
                              "naive_t": _naive_t([se.event_abnormal for se in ses], robust_len),
                              **_car_test(ses, robust_len, rho["rho_bar"])},
        }
        # 稳健性两道(spec §6):Corrado 秩 + 日历时间组合法
        robustness = {
            "corrado_rank": corrado_rank(rank_secs, main_len, robust_len),
            "calendar_time": calendar_time(cal_evs, main_len, robust_len),
        }

    # 板块分层(item 8):有效事件按 board 计数 + 主窗 CAAR;ST 层为已剔除层
    strata = _board_strata(cleaned, valid_events)

    # 删失诊断窗(步3b,R5;报告项不进 verdict)
    censor_diag = _censor_diagnostic(valid_events) if n >= 1 else {}

    # 剔除率按年份(item 7)
    rej = year_breakdown(cleaned)

    # verdict(spec §6 三法一致:ADJ-BMP 截面 + Corrado 秩 + 日历时间组合)
    verdict, verdict_note = _verdict(sample_state, car, robustness, alpha)

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
        "robustness": robustness,            # 稳健性两道(Corrado 秩 + 日历时间组合,spec §6)
        "board_strata": strata,
        "censor_diagnostic": censor_diag,     # 步3b 删失诊断窗(R5;报告项、不进 verdict)
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
    for v in valid_events:
        m = v[1]
        if m["board"] == "chinext":
            cx_seg[m["regime_segment"]] += 1
    strata["_chinext_regime"] = {"boundary": fa.CHINEXT_REGIME_DATE.isoformat(), **cx_seg}
    strata["_st_note"] = "ST 为已剔除层(spec §5 ST 剔除);不进池化检验,分层仅计数留痕(item 8 调和)"
    return strata


def _censor_diagnostic(valid_events) -> dict:
    """删失诊断窗(步3b,R5 本义;frozen 诊断窗 [0,+2]/[0,+5];**报告项、不进 verdict**)。三件套:
      ① 各 τ 逐日 AR(截面 AAR + BMP/ADJ-BMP,看反应时间形状与延迟价格发现);
      ② 各 τ 一字板/触板/停牌 计数占比;
      ③ ①② 按板块四层(main/chinext/star/ST)分拆(强制;ST 为已剔除层→有效 0)。"""
    ses = [v[0] for v in valid_events]
    metas = [v[1] for v in valid_events]
    dl = DIAG_ROBUST_LEN

    def _panel(sub_ses, sub_metas):
        ar_rows = []
        if len(sub_ses) >= 1:
            by = {r["tau"]: r for r in adj_bmp_by_tau(sub_ses)["rows"]}
            aar = [_mean([se.event_abnormal[t] for se in sub_ses]) for t in range(dl)]
            for tau in range(dl):
                r = by.get(tau, {})
                ar_rows.append({"tau": tau, "n": r.get("n"), "aar": aar[tau],
                                "bmp": r.get("bmp"), "adj_bmp": r.get("adj_bmp")})
        cen_rows = []
        n = len(sub_metas)
        for tau in range(dl):
            cnt = {"one_word": 0, "limit_up": 0, "limit_down": 0, "suspend": 0, "none": 0}
            for m in sub_metas:
                c = m["diag_censor"][tau] if tau < len(m["diag_censor"]) else "none"
                cnt[c] = cnt.get(c, 0) + 1
            cen_rows.append({"tau": tau, "n": n, **cnt,
                             "censored_pct": ((n - cnt["none"]) / n) if n else None})
        return {"by_tau_ar": ar_rows, "by_tau_censor": cen_rows}

    out = {
        "window": f"删失诊断窗 主[0,+{DIAG_MAIN_LEN-1}]/稳健[0,+{DIAG_ROBUST_LEN-1}]"
                  f"(frozen,R5;报告项不进 verdict;检验窗见 car)",
        "diag_main_len": DIAG_MAIN_LEN, "diag_robust_len": DIAG_ROBUST_LEN,
        "all": _panel(ses, metas), "by_board": {},
    }
    for board in ("main", "chinext", "star", "ST"):     # 板块四层分拆(强制;③)
        idx = [i for i, m in enumerate(metas)
               if (board == "ST" and m.get("is_st"))
               or (board != "ST" and not m.get("is_st") and m["board"] == board)]
        out["by_board"][board] = _panel([ses[i] for i in idx], [metas[i] for i in idx])
    return out


def _naive_t(abn_by_sec: list, win_len: int):
    """朴素 t 检验(未校正截面相关):CAR_i=Σ_τ AR_iτ,t=mean/(sd/√N)。供聚集假阳性判据。"""
    cars = []
    for ar in abn_by_sec:
        w = ar[:win_len]
        if any(x is None for x in w):
            continue
        cars.append(sum(w))
    n = len(cars)
    if n < 2:
        return None
    m, s = sum(cars) / n, _sd(cars)
    return (m / (s / n ** 0.5)) if s else None


def _sig_dir(stat, z_crit):
    """(显著?, 方向 sign)。stat=None → (False, 0)。"""
    if stat is None:
        return False, 0
    return abs(stat) > z_crit, (1 if stat > 0 else (-1 if stat < 0 else 0))


def _verdict(sample_state, car, robustness, alpha) -> tuple[str, str]:
    """spec §6 三法一致裁决(写死):
      · 三法(ADJ-BMP 截面 / Corrado 秩 / 日历时间组合)方向一致才确认效应;
      · 朴素 t 显著而 ADJ-BMP 不显著 → 聚集假阳性,以 ADJ-BMP 为准(NOT_SIG);
      · 日历时间法与截面法方向相反 → 事件密集期,verdict=AMBIGUOUS(报告应补事件加权,Loughran-Ritter);
      · 三法方向不一致 → AMBIGUOUS,报告分歧,不许挑有利的。
    显著性取自主检验 ADJ-BMP(双侧 α=family_alpha);终态 ∈ {SIG,NOT_SIG,INSUFFICIENT,AMBIGUOUS}。"""
    if sample_state == "INSUFFICIENT":
        return "INSUFFICIENT", f"有效事件 < {gates.SAMPLE_GATE}(样本量闸;合法终态,非报错)"
    if not car or car["main_window"].get("adj_bmp_car") is None:
        return "AMBIGUOUS", "主窗 ADJ-BMP 不可得(截面不足)"
    z = NormalDist().inv_cdf(1 - alpha / 2)
    mw = car["main_window"]
    adj_sig, adj_dir = _sig_dir(mw.get("adj_bmp_car"), z)
    naive_sig, _ = _sig_dir(mw.get("naive_t"), z)
    rk = (robustness.get("corrado_rank") or {}).get("main") or {}
    cal = (robustness.get("calendar_time") or {}).get("main") or {}
    rank_sig, rank_dir = _sig_dir(rk.get("t_rank"), z)
    cal_sig, cal_dir = _sig_dir(cal.get("t_cal"), z)
    base = (f"主窗(双侧 α={alpha:.4f},临界±{z:.3f}):ADJ-BMP_CAR={_fnum(mw.get('adj_bmp_car'))}"
            f"[{'显著' if adj_sig else '不显著'}] / 朴素t={_fnum(mw.get('naive_t'))} / "
            f"Corrado秩t={_fnum(rk.get('t_rank'))}[dir{rank_dir}] / "
            f"日历t={_fnum(cal.get('t_cal'))}[dir{cal_dir}]。")

    # 聚集假阳性:朴素 t 显著而 ADJ-BMP 不显著 → 以 ADJ-BMP 为准
    if naive_sig and not adj_sig:
        return "NOT_SIG", base + "朴素 t 显著而 ADJ-BMP 不显著 → 聚集假阳性,以 ADJ-BMP 为准。"
    # 日历时间法与截面法方向相反 → 事件密集期
    if cal_dir != 0 and adj_dir != 0 and cal_dir != adj_dir:
        return "AMBIGUOUS", base + "日历时间法与截面法方向相反 → 疑事件密集期;报告应补事件加权(Loughran-Ritter),不下确认。"
    # 三法方向一致性(ADJ-BMP / 秩 / 日历)
    dirs = [adj_dir, rank_dir, cal_dir]
    if adj_dir != 0 and all(d == adj_dir for d in dirs):
        return ("SIG" if adj_sig else "NOT_SIG"), base + (
            "三法方向一致 → " + ("确认效应(ADJ-BMP 显著)。" if adj_sig else "方向一致但 ADJ-BMP 不显著,未达确认。"))
    return "AMBIGUOUS", base + "三法方向不一致 → 报告分歧,不挑有利的(spec §6)。"


def _fnum(x):
    return "NA" if x is None else f"{x:.3f}"
