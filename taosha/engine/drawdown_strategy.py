"""淘沙 · engine · 策略版执行器(附录B B1/B2 + 附录G 决策判据;独立于 runner)。

修法#1 窄补(外审第二轮,2026-07-13):本模块**必须消费校验通过的 pap.strategy_execution**并据此
选执行路径(resolve_execution 单一执行门,驱动层共用)——close_to_next_open=收盘确认决策+次日
后复权 open 成交(holding_path fill_mode='next_open');未实现 profile(preclose_to_tail,日内数据
不足)fail-closed 拒运行,不得静默走旧"同刻成交"口径兜底。~~同刻收盘成交~~=legacy 域专属
(策略驱动对 legacy 一律拒,修法#1 层③),生产不可达。

策略版 = 单事件持有路径模拟(附录B B1):事件版同源进场(τ=0 建仓 bar)→ compute.holding_path
(附录G 离场决策:成本×0.8 强平 或 收盘破 ma20 先到先出;G1-G6 操作化;成交按执行 profile)
→ execution 成本乘式净收益
→ ADJ-BMP 四件套检验(人给框架,随附录G 执行指令 2026-07-11):
  ① 超额 = 路径净收益 − b1 池同跨度买入持有(BHAR;基准=reader.pool_return 预计算 PIT 活基准,
    跨度=日历轴 [τ=0, exit] 含两端——与事件版 CAR 自 τ=0 当日收益起算同法,对数累和取 exp−1);
  ② 标准化 = 估计窗日波动(SIM est_ar_sd,与事件版同一拟合口径)× √持有日数(H=日历交易日数,
    与①跨度同轴)→ SBHAR 截面 BMP 式 z × KP2010(ρ̄ 行业内口径④,与事件版同函数);
  ③ BHAR 右偏 → 附 skewness-adjusted t 稳健项(Hall 1992/LBT 1999,compute.bhar_tests);
  ④ **判决权归事件版**:本模块统计量为体检对照(附录B B2 互为体检),不产/不改台账 verdict。
+ DSR 常设报告项(compute.dsr,v_mode='proxy' 人裁 2026-07-10;N=族内 trial 计数;不进 verdict)。

同源一致性(步④验收硬项;硬化④升级):存活样本构造=engine/survivors.iter_survivors **单一主干**
(与事件版 runner 同一实现,平行链已消灭,宪章第5条)→ 存活集 == 事件版 N_valid 同构造;
策略版自身不可消费项(建仓 open 缺/基准缺)单列差集逐项归因(consumed ⊆ N_valid)。

已知口径特征(附录G 登记,报告须显式、不藏):G1 收盘确认=盘中硬止损频率被低估、方向保守
(决策判据,两执行口径同);G3 同刻收盘成交=legacy 域专属诊断口径(addendum_id=1 定性:冻结
口径下的不可执行诊断值、同刻成交前视与倾向乐观偏置,~~轻微前视/最早可执行价~~ 作废),
close_to_next_open 下同刻前视已消除;基准端点粒度=池基准仅有 close-to-close 日收益,跨度
[τ=0,成交日]两端按全日收益计(进场实为 τ=0 open、离场实为成交日 open)——预置框架内读法,登记不改口径。

红线:一个数不改 pap(铁律④);报告只陈述统计事实(铁律⑤);单文件 ≤500 行。
"""
from __future__ import annotations

import math
from statistics import NormalDist
from typing import Optional

from taosha.compute import bhar_tests as bt
from taosha.compute import frozen_ashare as fa
from taosha.compute import frozen_config as fc
from taosha.compute.abnormal_tests import SecurityEvent, kp2010_factor, rho_bar_within_industry
from taosha.compute.dsr import deflated_sharpe
from taosha.compute.holding_path import POSTPONE_EXTREME_DAYS, simulate_holding_path
from taosha.engine import execution as execu
from taosha.engine.cleaning import year_breakdown
from taosha.engine.survivors import iter_survivors
from taosha.experiment import gates
from taosha.experiment.pap import parse_test_windows, validate_strategy_execution

Num = Optional[float]

# ── 修法#1 窄补(外审第二轮,2026-07-13): 引擎必须真正消费 strategy_execution ──────────
# 已实现真实执行模拟的 profile → holding_path fill_mode 映射(单一来源;驱动层与引擎共用,
# 单一调用点=resolve_execution)。白名单内但未实现者(preclose_to_tail: 日内数据不足以支撑
# 真实执行)fail-closed 拒运行——不得校验通过后静默走旧"同刻成交"口径兜底,在日内数据足以
# 支撑前不得宣称该模式"已可执行"。
IMPLEMENTED_EXECUTION_PROFILES = {"close_to_next_open": "next_open"}


def resolve_execution(pap: dict) -> tuple[str, str]:
    """修法#1 窄补: 读取并校验 pap.strategy_execution,返回 (execution_profile, fill_mode)。

    fail-closed 三连:缺/非法 strategy_execution → validate raise;白名单外 → validate raise;
    白名单内但未实现 → SystemExit(显式拒,不兜底)。驱动层先于取数调用,引擎 run_strategy
    再调用(双闸同一实现)。"""
    se = pap.get("strategy_execution")
    validate_strategy_execution(se)
    prof = se.get("execution_profile")
    fill_mode = IMPLEMENTED_EXECUTION_PROFILES.get(prof)
    if fill_mode is None:
        raise SystemExit(
            f"修法#1(窄补): execution_profile {prof!r} 校验通过但真实执行模拟未实现"
            f"(已实现={sorted(IMPLEMENTED_EXECUTION_PROFILES)}),fail-closed 拒运行——"
            "不得静默走旧同刻成交口径兜底;preclose_to_tail 待日内数据足以支撑真实执行后另立施工")
    return prof, fill_mode


def _dist(xs: list) -> Optional[dict]:
    """整数/实数分布五数(min/mean/median/max/n)。空 → None。"""
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    med = s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2
    return {"n": n, "min": s[0], "max": s[-1], "mean": sum(s) / n, "median": med}


def run_strategy(reader, pap: dict, events: list, *, st_mode: str = "event_day") -> dict:
    """跑 #2b 策略版(附录B B1+G)。events=事件版同源事件行(DrawdownEventRow,价格模式生成)。

    返回 result 字典(策略版块;判决权归事件版,不产 verdict 终态)。"""
    cost = pap.get("cost")
    if not cost:
        raise SystemExit("pap 无 cost 块:策略版净收益成本口径未冻结(不默认不猜)")
    # 修法#1 窄补: 引擎消费 strategy_execution 并据此选执行路径(未实现 profile fail-closed 拒)
    exec_profile, fill_mode = resolve_execution(pap)
    buy_fee, sell_fee = execu.cost_fractions(cost)
    robust_len = parse_test_windows(pap)[-1]      # 同源过滤用(事件版 robust 窗越界剔除,同判据)
    family_trial = int(pap.get("_family_trial", 1))
    alpha = gates.family_alpha(family_trial)

    # ── 拉数 + 日历轴 + 池基准(与事件版 runner benchmark_mode='pool_pit' 同源)────────
    by_sec = reader.prices_by_security()
    all_dates = [c.trade_date for c in reader.calendar()]
    date_index = {d: j for j, d in enumerate(all_dates)}
    mkt = reader.pool_return(all_dates)           # b1 池等权 PIT 活基准(对数日收益;004 预计算)

    # ── 同源清洗(硬化④:存活样本构造=survivors.iter_survivors 单一主干,与事件版同一实现)──
    cleaned = []
    survivors = []          # 与事件版 N_valid 同构造的存活事件
    for ce, sv in iter_survivors(events, by_sec, all_dates, date_index, mkt, robust_len,
                                 st_mode=st_mode):
        cleaned.append(ce)
        if sv is not None:
            survivors.append(sv)

    # ── 逐存活事件跑持有路径(附录G)+ BHAR(四件套①②)────────────────────────────
    paths = []              # (ev, ce, path, net, gross, bench_bh, bhar, sbh, h_days)
    excluded = {"no_entry_open": [], "bench_gap": [], "sbhar_none": []}   # 同源差集逐项归因
    rho_inputs = []
    for ev, ce, fit, est_ar_by_date, rows in survivors:
        present = [r for r in rows if r.close is not None]                # present-bar 序列(同信号侧口径)
        p_dates = [r.trade_date for r in present]
        p_pos = {d: i for i, d in enumerate(p_dates)}
        entry_date = all_dates[ce.tau0_idx]
        entry_pidx = p_pos.get(entry_date)
        if entry_pidx is None:      # 不应发生(cleaning 保证 τ=0 日有 bar 可成交);如实归因不静默
            excluded["no_entry_open"].append(ev.event_id)
            continue
        path = simulate_holding_path(
            closes=[r.close for r in present],
            opens=[r.open for r in present],
            limit_status=[r.limit_status for r in present],
            entry_idx=entry_pidx,
            trade_day_idx=[date_index[d] for d in p_dates],   # G4 顺延>20 交易日口径(日历轴序号)
            fill_mode=fill_mode,        # 修法#1 窄补: 执行路径由 strategy_execution 白名单决定
        )
        if path is None:            # 建仓价缺(open None/≤0)→ 不可建仓(策略版自身差集)
            excluded["no_entry_open"].append(ev.event_id)
            continue
        net = execu.net_return(path.entry_price, path.exit_price, buy_fee, sell_fee)
        gross = execu.gross_return(path.entry_price, path.exit_price)
        if net is None:
            excluded["no_entry_open"].append(ev.event_id)
            continue
        # 四件套①:基准同跨度买入持有(日历轴 [τ=0, exit] 含两端;对数累和 → exp−1;缺日不补)
        exit_cal = date_index[p_dates[path.exit_idx]]
        seg = mkt[ce.tau0_idx: exit_cal + 1]
        if any(x is None for x in seg) or not seg:
            excluded["bench_gap"].append(ev.event_id)
            continue
        bench_bh = math.exp(sum(seg)) - 1.0
        bhar = net - bench_bh                      # 净超额(净额并报行)
        bhar_gross = gross - bench_bh              # 毛超额(主检验行;人批补正 2026-07-11,框架口径)
        h_days = exit_cal - ce.tau0_idx + 1        # 持有日历交易日数(与①跨度同轴)
        sbh = bt.sbhar(bhar, fit.est_ar_sd, h_days)
        sbh_gross = bt.sbhar(bhar_gross, fit.est_ar_sd, h_days)
        if sbh is None or sbh_gross is None:       # est_ar_sd≤0 极端(如实归因,不静默;毛/净同分母)
            excluded["sbhar_none"].append(ev.event_id)
            continue
        rho_inputs.append(SecurityEvent(
            est_ar_sd=fit.est_ar_sd, L=fit.delta, x_bar=fit.x_bar, sxx=fit.sxx,
            event_market=[], event_abnormal=[], industry=ce.industry,
            est_ar_by_date=est_ar_by_date))
        paths.append((ev, ce, path, net, gross, bench_bh, bhar, sbh, h_days,
                      bhar_gross, sbh_gross))

    # ── 截面检验(四件套②③)+ 闸/门槛(附录B B2)──────────────────────────────────
    n = len(paths)
    sample_state = gates.sample_verdict(n)
    nets = [p[3] for p in paths]
    grosses = [p[4] for p in paths]
    bhars = [p[6] for p in paths]
    sbhars = [p[7] for p in paths]
    bhars_gross = [p[9] for p in paths]
    sbhars_gross = [p[10] for p in paths]
    rho = rho_bar_within_industry(rho_inputs) if rho_inputs else {"rho_bar": 0.0, "n_pairs": 0,
                                                                  "n_securities": 0, "note": "空截面"}
    # 主检验 = 毛超额(人批补正 2026-07-11:检验挂毛超额、净额并报;首跑挂净=偏离,留痕见输出)
    ct_gross = bt.cross_test(sbhars_gross, rho["rho_bar"], kp2010_factor)
    sat_gross = bt.skew_adjusted_t(bhars_gross)
    # 净额并报行(首跑口径保留为对照)
    ct = bt.cross_test(sbhars, rho["rho_bar"], kp2010_factor)
    sat = bt.skew_adjusted_t(bhars)
    z_crit = NormalDist().inv_cdf(1 - alpha / 2)
    adj_sig = (ct_gross["adj_z"] is not None and abs(ct_gross["adj_z"]) > z_crit)
    if sample_state == "INSUFFICIENT":
        sig_state = "INSUFFICIENT"
    else:
        sig_state = "SIG" if adj_sig else "NOT_SIG"

    # ── DSR 常设报告项(施工令①;v_mode='proxy' 人裁;N=族内 trial 计数;不进 verdict)────
    dsr = deflated_sharpe(nets, N=family_trial, v_mode="proxy") if nets else None

    # ── 附录G 诊断块(G2/G4/G5;报告项)────────────────────────────────────────────
    reasons: dict = {}
    for _, _, p, *_ in paths:
        reasons[p.exit_reason] = reasons.get(p.exit_reason, 0) + 1
    dual = sum(1 for _, _, p, *_ in paths if p.trigger_stop and p.trigger_ma20)
    postponed = [(ev.event_id, p.postpone_bars, p.postpone_days)
                 for ev, _, p, *_ in paths if p.postpone_bars > 0]
    extreme = [{"event_id": ev.event_id, "postpone_days": p.postpone_days,
                "postpone_bars": p.postpone_bars, "right_censored": p.right_censored}
               for ev, _, p, *_ in paths if p.postpone_extreme]      # G4 上限:单列不静默
    censored = [(ev, p, net) for ev, _, p, net, *_ in paths if p.right_censored]
    diagnostics = {
        "exit_reasons": reasons,
        "dual_trigger": {"n": dual, "note": "G2:同日双触发双 flag 均记账,主因归强平;仅归因标签不影响数值"},
        "postpone": {
            "n_postponed": len(postponed),
            "days_dist": _dist([d for _, _, d in postponed]),
            "bars_dist": _dist([b for _, b, _ in postponed]),
            "extreme_cases": extreme,
            "note": f"顺延(修法#1 窄补 next_open 口径):名义成交 bar(触发次日)不可成交→顺延至"
                    f"首个可成交 bar 的后复权 open 出(跳空真实成本如实吃进);顺延>{POSTPONE_EXTREME_DAYS}"
                    f"交易日=极端案例单列标注(G4 上限条款同式,不静默);天数按日历交易日轴计"},
        "right_censored": {
            "n": len(censored), "pct": (len(censored) / n) if n else None,
            "unrealized_net": execu.aggregate([c[2] for c in censored]),
            "note": "G5:样本末端未离场=右删失+末端收盘 mark-to-market,不剔除(剔除=幸存偏差);"
                    "此子集净收益为未实现成分(open_position)"},
        "holding_bars_dist": _dist([p.holding_bars for _, _, p, *_ in paths]),
        "holding_days_dist": _dist([t[8] for t in paths]),   # t[8]=h_days(元组扩长后忌尾位解包)
    }

    rej = year_breakdown(cleaned)
    return {
        "strategy_version": {
            "definition": "附录B B1 单事件持有路径模拟;离场决策判据=附录G(人批冻结 2026-07-10);"
                          "离场成交=strategy_execution 白名单(修法#1 窄补 2026-07-13: 引擎消费执行 schema)",
            "execution": {
                "profile": exec_profile,
                "fill_mode": fill_mode,
                "decision": "close_confirmed(附录G 判据: 成本×0.8 强平/收盘破 ma20,先到先出,收盘确认)",
                "fill": "next_adjusted_open(次一 present-bar 后复权 open;不可成交顺延至首个可成交 bar 的 open)",
                "note": "修法#1 窄补: 引擎据校验通过的 strategy_execution 选执行路径;"
                        "同刻成交口径生产不可达(legacy 域专属且策略驱动对 legacy 一律拒)",
            },
            "verdict_authority": "event_version",
            "authority_note": "判决权归事件版(四件套④):本块统计量为体检对照(附录B B2 互为体检),"
                              "不产/不改台账 verdict;事件版 verdict 为准。",
            "n_events_input": len(events),
            "n_survivors_sourced": len(survivors),
            "n_consumed": n,
            "sample_gate": {"gate": gates.SAMPLE_GATE, "state": sample_state},
            "source_consistency": {
                "note": "同源一致性(步④):清洗流水线与事件版逐步同构 → survivors==事件版 N_valid 同构造;"
                        "consumed ⊆ survivors,差集逐项归因如下",
                "excluded_no_entry_open": {"n": len(excluded["no_entry_open"]),
                                           "event_ids": excluded["no_entry_open"]},
                "excluded_bench_gap": {"n": len(excluded["bench_gap"]),
                                       "event_ids": excluded["bench_gap"]},
                "excluded_sbhar_none": {"n": len(excluded["sbhar_none"]),
                                        "event_ids": excluded["sbhar_none"]},
            },
            "cost": {"buy_fee": buy_fee, "sell_fee": sell_fee,
                     "net_formula": "exit_fill*(1-卖费)/(entry_open*(1+买费))-1(execution 单一来源;"
                                    "exit_fill=执行 profile 决定的成交价,close_to_next_open=次日后复权 open)"},
            "net": execu.aggregate(nets),
            "gross": execu.aggregate(grosses),
            "benchmark_bh": execu.aggregate([p[5] for p in paths]),
            "bhar": execu.aggregate(bhars),
            "bhar_gross": execu.aggregate(bhars_gross),
            "test_object_note": "人批补正(2026-07-11):检验挂毛超额(毛路径收益−池同跨度BH)、净额并报;"
                                "首跑实现挂净超额=偏离(方向保守:净扣成本使超额更负),人批补正留痕。",
            "adj_bmp_bhar_gross": {
                "framework": "四件套②主检验(毛超额):SBHAR_i=BHAR_gross_i/(est_ar_sd_i·√H_i);"
                             "截面 z=mean/sd·√N × KP2010",
                "rho_bar": rho["rho_bar"], "rho_n_pairs": rho["n_pairs"], "rho_note": rho["note"],
                **ct_gross,
                "alpha": alpha, "z_crit": z_crit, "family_trial": family_trial,
                "sig_state": sig_state,
                "sig_note": "统计事实标注(判决权归事件版,不改台账 verdict)",
            },
            "adj_bmp_bhar": {
                "framework": "净额并报行(净超额=净路径收益−池同跨度BH;首跑口径保留为对照,非主检验)",
                "rho_bar": rho["rho_bar"], "rho_n_pairs": rho["n_pairs"], "rho_note": rho["note"],
                **ct,
                "alpha": alpha, "z_crit": z_crit, "family_trial": family_trial,
            },
            "skew_adjusted_t_gross": {
                "framework": "四件套③主检验(毛超额右偏稳健项,Hall 1992/LBT 1999)",
                **sat_gross,
            },
            "skew_adjusted_t": {
                "framework": "净额并报行(净超额右偏稳健项,对照)",
                **sat,
            },
            "anchor_menu": {
                "note": "开卡对照菜单(人指 2026-07-11;量纲:①②③=事件级简单收益均值〔小数〕,④=净收益>0 占比)",
                "gross_bhar_mean": (execu.aggregate(bhars_gross) or {}).get("mean"),
                "net_raw_mean": (execu.aggregate(nets) or {}).get("mean"),
                "net_bhar_mean": (execu.aggregate(bhars) or {}).get("mean"),
                "win_rate_net": (execu.aggregate(nets) or {}).get("pos_frac"),
            },
            "dsr": dsr,
            "dsr_note": "DSR 常设报告项(施工令①;BLdP 精确公式;V 口径=proxy 人裁 2026-07-10;"
                        "N=族内 trial 计数;不进 verdict)",
            "diagnostics": diagnostics,
            "known_caliber_features": [
                "G1:−20% 强平收盘确认 → 盘中硬止损频率被低估,对策略版收益方向保守(附录G1 登记;"
                "离场决策判据不变,两执行口径同)",
                "执行(修法#1 窄补 2026-07-13):决策=收盘确认(触发 bar close),成交=次一 present-bar "
                "后复权 open(close_to_next_open 白名单)——同刻成交前视已消除;~~G3 同刻收盘成交口径~~"
                "为 legacy 域专属诊断值(addendum_id=1 定性),生产不可达(策略驱动对 legacy 一律拒)",
                "基准端点粒度:池基准为 close-to-close 日收益,跨度[τ=0,成交日]两端均按全日收益计"
                "(进场实为 τ=0 open、离场实为成交日 open)——ADJ-BMP 预置框架内读法,与事件版 CAR "
                "自 τ=0 当日收益起算同法(登记,非新口径)",
            ],
            "rejections_sourced": rej,
        },
        "audit": {
            "frozen_config_digest": fc.audit_digest(),
            "frozen_ashare_digest": fa.audit_digest(),
            "benchmark_mode": "pool_pit",
            "family_trial": family_trial, "family_alpha": alpha,
        },
    }


if __name__ == "__main__":
    # 合成冒烟(无 DB):桩 reader + 单票单事件,验流水线端到端与关键量手算。
    import datetime as dt
    from taosha.reader.contract import CalendarRow, PriceRow

    base = dt.date(2020, 1, 6)
    N_DAYS = 400
    dates = [base + dt.timedelta(days=i) for i in range(N_DAYS)]

    # 单票:估计窗段正弦扰动(SIM 残差方差>0),事件 T=idx330;τ=0=331(open=102,持有段稳在 ma20 上
    # 不触发);idx345 跳水 90(>81.6 强平线不强平、<ma20 → break_ma20 收盘确认决策)→ 修法#1 窄补:
    # close_to_next_open 成交=idx346 后复权 open=95.0(≠同刻 close 90.0,反向测试①引擎侧断言)。
    closes = ([100.0 + 0.5 * math.sin(i) for i in range(330)]
              + [102.0] * 15                 # idx330..344(τ=0=331 起持有,close==ma20 不破)
              + [90.0] + [95.0] * (N_DAYS - 346))
    T_IDX = 330

    def _rows(ts):
        return [PriceRow(ts_code=ts, trade_date=dates[i], close=closes[i],
                         is_suspended=False, limit_status="none", board="main",
                         is_st=False, industry="I", open=closes[i]) for i in range(N_DAYS)]

    class _Ev:
        ts_code = "A01"; event_id = "A01:E1"; snapshot_batch = "SYNTH"
        first_ann_date = dates[T_IDX]; event_type_layer = None
        d1_never_broke_ma10 = False; d2_episode_to_entry_days = 3; d3_broke_ma20_before_entry = False

    class _Rd:
        def prices_by_security(self):
            return {"A01": _rows("A01")}
        def calendar(self):
            return [CalendarRow(trade_date=d, pretrade_date=None) for d in dates]
        def pool_return(self, ds):
            # 池基准交替 ±0.1%(首日 None;须有方差,SIM OLS 要求 regressor sxx>0)
            return [None] + [(0.001 if i % 2 == 0 else -0.001) for i in range(1, len(ds))]

    from taosha.experiment.pap import CLOSE_TO_NEXT_OPEN_FROZEN
    _se = dict(CLOSE_TO_NEXT_OPEN_FROZEN, execution_profile="close_to_next_open")
    pap = {"window": "事件版20/60日;策略版按离场", "_family_trial": 2,
           "pap_schema_version": 2, "analysis_type": "strategy", "strategy_execution": _se,
           "cost": {"commission": 0.00025, "stamp_tax_sell": 0.001, "slippage_oneway": 0.001,
                    "limit_up_board_untradeable": True}}
    res = run_strategy(_Rd(), pap, [_Ev()])
    sv = res["strategy_version"]
    assert sv["n_consumed"] == 1 and sv["verdict_authority"] == "event_version", sv["n_consumed"]
    assert sv["sample_gate"]["state"] == "INSUFFICIENT"        # n=1 < 30(合法结果非报错)
    assert sv["execution"]["profile"] == "close_to_next_open"  # 修法#1 窄补: 执行 schema 被真实消费
    # 路径:τ=0=idx331 建仓 open=102;idx345 close=90 破 ma20 收盘确认(90>81.6 不强平)
    # → 修法#1 窄补: 成交=idx346 后复权 open=95.0(次日开盘),**非**旧同刻 close 90.0
    assert sv["diagnostics"]["exit_reasons"].get("break_ma20") == 1, sv["diagnostics"]["exit_reasons"]
    exp_net = 95.0 * (1 - 0.00225) / (102.0 * (1 + 0.00125)) - 1      # 次日 open 成交
    old_same_close_net = 90.0 * (1 - 0.00225) / (102.0 * (1 + 0.00125)) - 1
    assert abs(sv["net"]["mean"] - exp_net) < 1e-12, (sv["net"], exp_net)
    assert abs(sv["net"]["mean"] - old_same_close_net) > 1e-6, "成交仍在同刻收盘=旧口径未消灭"
    # 基准同跨度买入持有手算:seg=mkt[τ0..exit]=[331..346](H=16 日,exit=成交日 idx346),bench=exp(Σ)−1
    _mkt = _Rd().pool_return(dates)
    exp_bench = math.exp(sum(_mkt[331:347])) - 1.0
    assert abs(sv["benchmark_bh"]["mean"] - exp_bench) < 1e-12, (sv["benchmark_bh"], exp_bench)
    assert abs(sv["bhar"]["mean"] - (exp_net - exp_bench)) < 1e-12
    # 毛超额(主检验,人批补正 2026-07-11):gross=95/102−1(次日 open 成交);bhar_gross=gross−bench
    exp_gross = 95.0 / 102.0 - 1
    assert abs(sv["gross"]["mean"] - exp_gross) < 1e-12
    assert abs(sv["bhar_gross"]["mean"] - (exp_gross - exp_bench)) < 1e-12
    am = sv["anchor_menu"]
    assert abs(am["gross_bhar_mean"] - (exp_gross - exp_bench)) < 1e-12
    assert abs(am["net_raw_mean"] - exp_net) < 1e-12
    assert abs(am["net_bhar_mean"] - (exp_net - exp_bench)) < 1e-12
    assert am["win_rate_net"] == 0.0                      # 单事件亏损 → 胜率 0
    assert "adj_bmp_bhar_gross" in sv and sv["adj_bmp_bhar_gross"]["sig_state"] == "INSUFFICIENT"
    assert "sig_state" not in sv["adj_bmp_bhar"]          # 净行=并报,不挂 sig_state
    assert sv["diagnostics"]["holding_days_dist"]["max"] == 16   # 含成交日(次日 open)
    # 同源差集为空(单事件全消费)
    sc = sv["source_consistency"]
    assert sc["excluded_no_entry_open"]["n"] == 0 and sc["excluded_bench_gap"]["n"] == 0
    # DSR 报告项存在(n≥2 才有 dsr 值;n=1 → 退化 None 但键在)
    assert "dsr" in sv

    # ── 修法#1 窄补 fail-closed 三断言 ────────────────────────────────────────────
    # a) 缺 strategy_execution → 校验 raise(不静默兜底)
    try:
        run_strategy(_Rd(), {k: v for k, v in pap.items() if k != "strategy_execution"}, [_Ev()])
        raise SystemExit("缺 strategy_execution 未拒")
    except ValueError:
        pass
    # b) preclose_to_tail 结构合法(可冻结)但执行未实现 → 显式拒运行,不得旧口径兜底
    _pct = {"execution_profile": "preclose_to_tail", "decision_cutoff": "14:50",
            "decision_price_source": "人定占位", "fill_window": {"start": "14:55", "end": "15:00"},
            "fill_price_rule": "人定占位", "slippage_rule": "frozen_cost"}
    try:
        run_strategy(_Rd(), dict(pap, strategy_execution=_pct), [_Ev()])
        raise SystemExit("preclose_to_tail 未实现却放行=静默兜底")
    except SystemExit as e:
        assert "未实现" in str(e), e
    # c) 白名单外 profile → 校验 raise
    try:
        run_strategy(_Rd(), dict(pap, strategy_execution={"execution_profile": "same_close_exec"}), [_Ev()])
        raise SystemExit("白名单外 profile 未拒")
    except ValueError:
        pass

    print(f"drawdown_strategy.py 冒烟 OK:n_consumed=1/INSUFFICIENT(合法)/break_ma20 收盘确认决策/"
          f"成交=次日后复权open 95.0(≠同刻close 90.0,修法#1窄补)/净收益手算一致({sv['net']['mean']:.6f})/"
          f"BHAR=net−基准BH手算一致/H=16/同源差集空/判决权=event_version/"
          f"缺execution·未实现profile·白名单外 全拒(fail-closed)")
