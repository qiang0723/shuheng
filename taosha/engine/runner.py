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
from taosha.compute.rank_test import RankSecurity, corrado_rank
from taosha.engine import benchmark as bench
from taosha.engine import drawdown_events as dde
from taosha.engine import execution as execu
from taosha.engine.cleaning import (
    CleanedEvent, layer_year_breakdown, year_breakdown,
)
from taosha.engine.survivors import iter_survivors
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


def _n_eff_rho(n: int, rho_bar: Num) -> Optional[dict]:
    """相关性折算有效样本量(存活 N 与相关性下的等效独立观测数)。标签订正 2026-07-08:
    result 顶层 n_valid=存活事件数(非相关折算);此处按现成 ρ̄(口径④行业内)两式并报——
      · Kish  N_eff = N/(1+(N-1)ρ̄)               (等相关近似,经典 Kish 有效样本)
      · KP    N_eff = N(1-ρ̄)/(1+(N-1)ρ̄)         (Kolari-Pynnönen 2010 方差膨胀一致)
    等相关假设(全体等 ρ̄)对相关性取上界 → 对 N_eff 取下界(保守)。ADJ-BMP 检验已内嵌此坍缩
    (kp_factor=√((1-ρ̄)/(1+(N-1)ρ̄)))——即 BMP_CAR 除以 √(1+(N-1)ρ̄) 得 ADJ-BMP_CAR。"""
    if not n or rho_bar is None:
        return None
    denom = 1.0 + (n - 1) * rho_bar
    if denom <= 0:
        return None
    return {"n_valid": n, "rho_bar": rho_bar,
            "kish": n / denom, "kp": n * (1.0 - rho_bar) / denom,
            "note": "相关性折算有效N:Kish=N/(1+(N-1)ρ̄);KP=N(1-ρ̄)/(1+(N-1)ρ̄);ρ̄=行业内(口径④)。"
                    "等相关假设→N_eff 下界;ADJ-BMP 已内嵌此坍缩。"}


# 三层标签(explore_reader_events 出英文 good/bad/turnaround;合成 fixture 出中文预喜/预亏)
_LAYER_LABEL = {"good": "预喜", "bad": "预亏", "turnaround": "扭亏"}
_LAYER_ORDER = {"good": 0, "预喜": 0, "bad": 1, "预亏": 1, "turnaround": 2, "扭亏": 2}


def _secondary_car(ses: list, aar: list, secondary_lens: tuple, rho_bar) -> dict:
    """预注册次级报告窗块(人裁 2026-07-15 三窗判点①:检验窗>2 时中间窗完整产出,不参与判决)。
    与 main/robust 同一 compute 原语(caar/naive_t/_car_test)→ "真实计算"而非字段占位;
    secondary_lens 为空(两窗 pap,#4/#2b/合成)→ 调用方不产出此键,既有 result 逐字节不变。"""
    return {
        "note": "预注册次级报告窗(人裁 2026-07-15):完整产出、不参与判决,不得据三窗结果择优改判。",
        "windows": [{"taus": f"[0,+{L-1}]",
                     "caar": sum(a for a in aar[:L] if a is not None),
                     "naive_t": _naive_t([se.event_abnormal for se in ses], L),
                     **_car_test(ses, L, rho_bar)} for L in secondary_lens],
    }


def _stats_for_subset(sub: list, main_len: int, robust_len: int, alpha: float,
                      secondary_lens: tuple = (), *, verdict_policy: str = "three_method",
                      nfv: bool = False) -> dict:
    """对一子集(某层)跑与 combined 同一流水线(per_tau/主稳健窗 CAR/三法/verdict/n_eff_rho)。
    复用 combined 同一 compute 原语、同一顺序 → 层内结果与"若单独喂该层"一致。纯读取,不改 pap。
    nfv(C6 二次回修,人令 2026-07-17 深夜三:改名不等于取消判决——旧"verdict 改名
    sig_state_report_only"方案作废):True → 层块**不携带任何判决或等价分类字段**
    (无 verdict/verdict_note/sig_state_report_only/sig_state_note),仅 not_for_verdict=True
    结构化标记(全文档唯一 verdict 键=顶层);False(默认)→ 键名不变,既有输出逐字节零回归。"""
    ses = [v[0] for v in sub]
    rank_secs = [v[2] for v in sub]
    cal_evs = [v[3] for v in sub]
    n = len(ses)
    sample_state = gates.sample_verdict(n)
    per_tau, car, robustness, n_eff_rho = {}, {}, {}, None
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
        if secondary_lens:
            car["secondary_windows"] = _secondary_car(ses, aar, secondary_lens, rho["rho_bar"])
        robustness = {
            "corrado_rank": corrado_rank(rank_secs, main_len, robust_len),
            "calendar_time": calendar_time(cal_evs, main_len, robust_len),
        }
        n_eff_rho = _n_eff_rho(n, rho["rho_bar"])
    out = {"n_valid": n, "sample_state": sample_state, "n_eff_rho": n_eff_rho,
           "per_tau": per_tau, "car": car, "robustness": robustness}
    if nfv:
        out["not_for_verdict"] = True     # C6 二次回修:层块零判决字段(不计算不携带,无等价改名)
    else:
        verdict, verdict_note = _verdict(sample_state, car, robustness, alpha,
                                         policy=verdict_policy)
        out.update({"verdict": verdict, "verdict_note": verdict_note})
    return out


def _type_strata(valid_events: list, main_len: int, robust_len: int, alpha: float,
                 secondary_lens: tuple = (), *, verdict_policy: str = "three_method",
                 nfv: bool = False) -> dict:
    """三层分解(预喜/预亏/扭亏;pap layers/event_def 冻结定义)。预喜(期望+漂移)与预亏(期望-漂移)
    方向相反,合并池化可相互抵消→合并 verdict 不可读作各层均无漂移;分层是冻结定义核心。
    层外(不确定/其他)已在 explore_reader_events 视图排除;若仍现意外层,如实上报不静默。"""
    groups: dict = {}
    for v in valid_events:
        groups.setdefault(v[1].get("event_type_layer", "unknown"), []).append(v)
    out = {"note": "预喜/预亏/扭亏三层各独立跑同一流水线(层外〔不确定/其他〕已在视图排除);"
                   "预喜+漂移 vs 预亏-漂移方向相反,合并结果可抵消,不可读作各层均无漂移。",
           "n_valid_sum": sum(len(g) for g in groups.values()), "layers": {}}
    for lay in sorted(groups, key=lambda k: (_LAYER_ORDER.get(k, 9), k)):
        blk = _stats_for_subset(groups[lay], main_len, robust_len, alpha, secondary_lens,
                                verdict_policy=verdict_policy, nfv=nfv)
        blk["layer_key"] = lay
        blk["layer_label"] = _LAYER_LABEL.get(lay, lay)
        out["layers"][lay] = blk
    return out


# ── 正交诊断维度(C6 二次回修,人令 2026-07-17 深夜三;exp8=('listing_age','st'))─────────
# 每维分别、明确、结构化输出;层块只报统计事实(事件数/存活数/逐因逐年剔除/CAAR/ADJ-BMP 等
# 预注册报告统计),**零判决字段**;零存活层输出 UNESTIMABLE_BY_FROZEN_COVERAGE(C3)且块不缺席。
_DIAG_DIM_SPECS = {
    "listing_age": {
        "layers": ("recent_listing", "seasoned"),
        "note": "上市交易龄维度:recent_listing=链起点自身真实交易行序号≤30 / seasoned=其余;"
                "两层一律同一估计窗与覆盖门槛(112/160),不预判任何层无CAR、不预限主结论适用域(C3)",
    },
    "st": {
        "layers": ("ST", "non_ST"),
        "note": "ST/非ST 维度:is_st=事件日行判定(st_mode 辖);明确正交诊断维度,不藏于板块计数(C6)",
    },
}


def _diag_dim_key(dim: str, obj) -> str:
    """取事件在某诊断维度上的层键。obj=CleanedEvent 或 se_meta dict(两者均有所需属性)。"""
    if dim == "st":
        is_st = obj.get("is_st") if isinstance(obj, dict) else obj.is_st
        return "ST" if is_st else "non_ST"
    lay = (obj.get("event_type_layer") if isinstance(obj, dict) else obj.event_type_layer)
    return lay or "unknown"


def _diag_layer_stats(sub_valid: list, main_len: int, robust_len: int,
                      secondary_lens: tuple) -> Optional[dict]:
    """诊断层预注册报告统计(CAAR/朴素t/BMP/ADJ-BMP;与 combined 同一 compute 原语)。
    零存活 → None(层块由调用方置 UNESTIMABLE_BY_FROZEN_COVERAGE)。无任何判决字段。"""
    ses = [v[0] for v in sub_valid]
    if not ses:
        return None
    rho = adj_bmp_by_tau(ses)["rho"]
    aar = [_mean([se.event_abnormal[t] for se in ses]) for t in range(robust_len)]

    def _w(L):
        return {"taus": f"[0,+{L-1}]",
                "caar": sum(a for a in aar[:L] if a is not None),
                "naive_t": _naive_t([se.event_abnormal for se in ses], L),
                **_car_test(ses, L, rho["rho_bar"])}

    out = {"rho_bar": rho["rho_bar"], "main_window": _w(main_len),
           "robust_window": _w(robust_len)}
    if secondary_lens:
        out["secondary_windows"] = [_w(L) for L in secondary_lens]
    return out


def _diagnostic_dimensions(cleaned: list, valid_events: list, main_len: int, robust_len: int,
                           secondary_lens: tuple, dims: tuple) -> dict:
    """两条独立诊断轴(C6;禁四格交叉统计)+ 零存活按真实原因命名(人令调整五)。
    层集合=预注册必出层 ∪ 实际观测层(意外层如实上报不静默);必出层零事件也出块。
    状态命名(仅零存活层;n_valid>0 出统计块、不产生任何状态判决):
      n_events=0 → NO_EVENTS_IN_LAYER;
      n_events>0 且剔因全 ⊆ {coverage,history}(冻结覆盖/历史门槛)→ UNESTIMABLE_BY_FROZEN_COVERAGE;
      其余(listing 异常/停牌/顺延超限/多因混合)→ UNESTIMABLE_AFTER_FROZEN_CLEANING。
    本路径**不调用 _verdict()**、不产生 SIG/NOT_SIG/AMBIGUOUS/INSUFFICIENT 分类(人令调整三)。"""
    out_dims: dict = {}
    for dim in dims:
        spec = _DIAG_DIM_SPECS[dim]
        keys = list(spec["layers"])
        observed = {_diag_dim_key(dim, ce) for ce in cleaned}
        for k in sorted(observed - set(keys)):
            keys.append(k)                      # 意外层如实上报
        layers: dict = {}
        for key in keys:
            sub_cleaned = [ce for ce in cleaned if _diag_dim_key(dim, ce) == key]
            sub_valid = [v for v in valid_events if _diag_dim_key(dim, v[1]) == key]
            stats = _diag_layer_stats(sub_valid, main_len, robust_len, secondary_lens)
            rej = year_breakdown(sub_cleaned)              # 逐年(by_year 内含逐因)剔除分解(C3)
            by_reason_total: dict = {}
            for d_ in rej["by_year"].values():
                for r_, c_ in d_["by_reason"].items():
                    by_reason_total[r_] = by_reason_total.get(r_, 0) + c_
            blk = {
                "not_for_verdict": True,
                "n_events": len(sub_cleaned),
                "n_valid": len(sub_valid),
                "n_rejected": sum(1 for ce in sub_cleaned if ce.rejected),
                "rejections": rej,
                "rejections_by_reason_total": by_reason_total,
                "stats": stats,
            }
            if stats is None:                  # 零存活层:状态按真实原因命名(调整五);块不缺席
                if not sub_cleaned:
                    blk["status"] = "NO_EVENTS_IN_LAYER"
                elif set(by_reason_total) <= {"coverage", "history"}:
                    blk["status"] = "UNESTIMABLE_BY_FROZEN_COVERAGE"
                else:
                    blk["status"] = "UNESTIMABLE_AFTER_FROZEN_CLEANING"
            layers[key] = blk
        out_dims[dim] = {"not_for_verdict": True, "note": spec["note"], "layers": layers}
    out = {
        "not_for_verdict": True,
        "label": "正交诊断维度(C6 二次回修):两条独立轴分别结构化输出(禁四格交叉统计);"
                 "层块零判决字段,不产生独立判决、不改变顶层判决;零存活层状态按真实原因命名"
                 "(NO_EVENTS_IN_LAYER / UNESTIMABLE_BY_FROZEN_COVERAGE / "
                 "UNESTIMABLE_AFTER_FROZEN_CLEANING)且块不缺席。",
        "dims": out_dims,
    }
    # 二维计数矩阵(人令调整四:仅计数核对供审计,不计算 CAR/显著性/判决)
    if {"listing_age", "st"} <= set(dims):
        cells: dict = {}
        for ce in cleaned:
            k = f"{_diag_dim_key('listing_age', ce)}×{_diag_dim_key('st', ce)}"
            cells.setdefault(k, {"n_events": 0, "n_valid": 0})["n_events"] += 1
        for v in valid_events:
            k = f"{_diag_dim_key('listing_age', v[1])}×{_diag_dim_key('st', v[1])}"
            cells.setdefault(k, {"n_events": 0, "n_valid": 0})["n_valid"] += 1
        out["cross_counts"] = {
            "note": "二维计数矩阵:仅计数核对(审计用),不计算 CAR/显著性/判决(人令调整四)",
            "cells": dict(sorted(cells.items()))}
    return out


# 字段级角色元数据(C6 二次回修+人令调整六:主窗唯一判决权=adj_bmp_car;非权威统计=
# NOT_FOR_VERDICT;taus/n 等上下文=CONTEXT。仅 nfv_structured=True 注入,默认输出零改变)
_MAIN_WINDOW_FIELD_ROLES = {
    "adj_bmp_car": "VERDICT_AUTHORITY",
    "bmp_car": "NOT_FOR_VERDICT",
    "naive_t": "NOT_FOR_VERDICT",
    "caar": "NOT_FOR_VERDICT",
    "csar_mean": "NOT_FOR_VERDICT",
    "csar_sd": "NOT_FOR_VERDICT",
    "kp_factor": "NOT_FOR_VERDICT",
    "taus": "CONTEXT",
    "n": "CONTEXT",
}


def _main_window_field_roles(mw: dict) -> dict:
    """主窗字段角色映射,与实际字段集合逐项对账(人令调整六):出现未分类的新统计字段
    → fail-closed raise(不静默漏标)。"""
    roles = {}
    for k in mw:
        if k == "field_roles":
            continue
        r = _MAIN_WINDOW_FIELD_ROLES.get(k)
        if r is None:
            raise ValueError(f"car.main_window 出现未分类统计字段 {k!r}:field_roles 须与实际"
                             f"字段集合逐项对账,fail-closed(人令调整六)")
        roles[k] = r
    return roles


def _tradeable(valid_events: list, cost: Optional[dict], main_len: int, robust_len: int) -> dict:
    """可交易口径净收益汇总(选项2;pap `cost` 冻结定义)。合并 + 三层各出主/稳健窗净/毛额 + 出场诊断。

    pap 无 cost 块 → available=False(不适用,不静默造数)。纯读 se_meta['tradeable'](进出场价),
    不碰统计路径(CAR/AR 用 close,可交易用 open 进/close 出)→ 既有键零回归。零调参、零新设计。"""
    if not cost:
        return {"available": False, "note": "pap 无 cost 块 → 可交易口径不适用(进出场成本未定义)"}
    buy_fee, sell_fee = execu.cost_fractions(cost)
    main_label, rob_label = f"[0,+{main_len-1}]", f"[0,+{robust_len-1}]"

    def _blocks(trs):
        return {"main": execu.window_block(trs, buy_fee, sell_fee, "main", main_label),
                "robust": execu.window_block(trs, buy_fee, sell_fee, "robust", rob_label)}

    all_tr = [v[1]["tradeable"] for v in valid_events]
    groups: dict = {}
    for v in valid_events:
        lay = v[1].get("event_type_layer")
        if lay is None:          # #2b 单信号事件:无 layer 维度 → 不出层分解(合并即全体,免 None(None) 行)
            continue
        groups.setdefault(lay, []).append(v[1]["tradeable"])
    layers = {}
    for lay in sorted(groups, key=lambda k: (_LAYER_ORDER.get(k, 9), k)):
        layers[lay] = {"layer_key": lay, "layer_label": _LAYER_LABEL.get(lay, lay),
                       **_blocks(groups[lay])}
    return {
        "available": True,
        "note": "pap 既定可交易口径(cost 冻结):进场=τ=0 后复权 open、出场=窗尾后复权 close、"
                "成本乘式净额(买费=佣金+滑点/卖费=佣金+印花+滑点);一字涨停不可成交由 cleaning 顺延/"
                "放弃处置进场侧;窗尾不可成交按字面'收盘出'计、单列诊断。报告与锚对照用途,不改统计判决。",
        "cost": {"commission": cost.get("commission"), "stamp_tax_sell": cost.get("stamp_tax_sell"),
                 "slippage_oneway": cost.get("slippage_oneway"),
                 "limit_up_board_untradeable": cost.get("limit_up_board_untradeable"),
                 "buy_fee": buy_fee, "sell_fee": sell_fee,
                 "net_formula": "close_exit*(1-卖费)/(open_entry*(1+买费))-1"},
        "combined": _blocks(all_tr),
        "layers": layers,
    }


def run_study(reader, pap: dict, *, benchmark_mode: str = "market",
              pool: Optional[set] = None, events: Optional[list] = None,
              strata_enabled: bool = True, st_mode: str = "event_day",
              st_policy: str = "reject", verdict_policy: str = "three_method",
              nfv_structured: bool = False, postpone_policy: str = "legacy",
              diagnostic_dims: tuple = (),
              bias_statement_assert: Optional[str] = None) -> dict:
    """跑一条已冻结假设的事件研究,返回 result 字典(供 report + 落库)。

    benchmark_mode: 'market'(全市场等权)/'pool'(静态池等权)/'pool_pit'(#2b b1池等权PIT活基准,
      读预计算表 reader.pool_return,基准成分逐日=当日池快照)——口径②冻结基准。
    pool: benchmark_mode='pool' 时的静态池成员 ts_code 集合。
    events: 显式事件源(#2b=价格模式生成的 DrawdownEventRow 列表);None → reader.events()(#4 台账事件)。
    strata_enabled: 三层(预喜/预亏/扭亏)分解开关;#2b 单信号事件 → False(三层不适用)。
    st_mode: ST 判定源(硬化③;'event_day' 生产默认 / 'legacy_row0' 仅只读诊断 diff)。
    ── 回修单元三参数(人裁 2026-07-17 深夜二;全部显式参数化,默认值=既有行为逐字节零回归)──
    st_policy: ST 处置(C2 乙案):'reject' 默认=spec §5 剔除 / 'keep'=保留入主样本(exp8 冻结值)。
    verdict_policy: 判决口径:'three_method' 默认=spec §6 三法一致裁决 /
      'adj_bmp_main_only'=唯一判据=主窗 ADJ-BMP,辅助方法(朴素t/秩/日历)反向只报告分歧不得改判(exp8)。
    nfv_structured: True → 全部非权威结果块结构化 NOT_FOR_VERDICT 标记+主窗字段级角色元数据
      (C6 二次回修:分层块**零判决字段**,旧"verdict 改名 sig_state_report_only"方案作废;
      全文档唯一 verdict 键=顶层);False 默认=不加键,既有 result 逐字节不变。
    ── C1/C3/C6/P1-4 二次回修参数(人令 2026-07-17 深夜三;默认值=既有行为逐字节零回归)──
    postpone_policy: 'legacy' 默认=T/T+1 停牌 item7 前置剔除(既有)/'unified'=T+1 起停牌与
      一字板统一顺延计数≤5、T 停牌 fail-closed 'event_day_anomaly'(exp8,C1)。
    diagnostic_dims: 正交诊断维度元组(exp8=('listing_age','st'),C6);空默认=不产出、零新键。
    bias_statement_assert: **仅作逐字相等断言,非第二来源**(人令调整二):偏差声明唯一权威
      =pap['bias_statement'],runner 直接从 pap 读取原样携带、report 直接消费;本参数提供时
      与 pap 不逐字相等 → fail-closed 拒。回修新策略启用(unified/diagnostic_dims/nfv)而
      pap 缺 bias_statement → 拒绝运行。默认旧路径(pap 无此键)零新键,报告固定段不变。
    """
    if st_policy not in ("reject", "keep"):
        raise ValueError(f"st_policy 非法: {st_policy}(合法={{'reject','keep'}})")
    if verdict_policy not in ("three_method", "adj_bmp_main_only"):
        raise ValueError(f"verdict_policy 非法: {verdict_policy}"
                         "(合法={'three_method','adj_bmp_main_only'})")
    if postpone_policy not in ("legacy", "unified"):
        raise ValueError(f"postpone_policy 非法: {postpone_policy}(合法={{'legacy','unified'}})")
    for d in diagnostic_dims:
        if d not in _DIAG_DIM_SPECS:
            raise ValueError(f"diagnostic_dims 非法维度: {d}(合法={sorted(_DIAG_DIM_SPECS)})")
    # P1-4(人令调整二):偏差声明唯一权威=pap['bias_statement']——不接受任何调用方替代文本。
    pap_bias = pap.get("bias_statement")
    new_strategy = (postpone_policy != "legacy") or bool(diagnostic_dims) or nfv_structured
    if new_strategy and not pap_bias:
        raise ValueError("回修新策略已启用(unified/diagnostic_dims/nfv_structured)但 pap 缺 "
                         "'bias_statement' → 拒绝运行(P1-4:权威来源唯一=冻结 PAP)")
    if bias_statement_assert is not None and bias_statement_assert != pap_bias:
        raise ValueError("bias_statement_assert 与 pap['bias_statement'] 不逐字相等 → fail-closed"
                         "(P1-4:本参数仅作断言,不得作为第二来源覆盖 PAP)")
    # ── 检验窗从 pap 读(裁定 2026-07-07):main/robust = 首/末检验窗点数(#4/#2b=(20,60))──
    test_win = parse_test_windows(pap)
    main_len, robust_len = test_win[0], test_win[-1]
    # 三窗判点①(人裁 2026-07-15):首=主检验(唯一进 verdict)、末=稳健、中间=预注册次级报告窗
    #   完整产出不判决;两窗 pap(#4/#2b/合成)→ 空元组 → result 无新键,逐字节零回归。
    secondary_lens = test_win[1:-1]

    # 事件源:#2b 显式传入生成事件(价格模式 PIT);#4 走 reader.events()(台账)。
    event_src = list(events) if events is not None else list(reader.events())
    # #2b drawdown 事件带 D1/D2/D3 诊断属性(报告项,不进 verdict)——据此启用诊断聚合与 se_meta 带出。
    is_drawdown = bool(event_src) and hasattr(event_src[0], "d1_never_broke_ma10")

    # ── 拉数 + date 轴 ────────────────────────────────────────────────────────
    by_sec = reader.prices_by_security()
    # 轴=reader.calendar()(约束②日历轴):真实域=explore_reader_calendar(8187 日历日,缺行=停牌判据
    #   须在完整日历轴上数);合成域 SyntheticReader.calendar()=全证券 trade_date 并集=原 by_sec union
    #   → all_dates 与旧 `sorted({...})` 逐一致(约束③ 合成域零回归)。
    all_dates = [c.trade_date for c in reader.calendar()]
    date_index = {d: j for j, d in enumerate(all_dates)}
    n_dates = len(all_dates)

    # ── 收益 + 等权基准(口径②)──────────────────────────────────────────────
    # sec_returns=每票在 all_dates 上稠密展开。pool/合成域需全量(算等权基准);真实 market 域
    # 基准读预计算表(不需全量 sec_returns)→ 惰性化(事件循环内按票现算)避 5356×8187 稠密全物化
    # OOM(实测全量 anon-rss 6.9G/2c7.2G 机 OOM)。合成/pool 走本 if/else 全物化分支不变→约束③零回归。
    if benchmark_mode == "pool_pit":
        # #2b:b1 池等权 PIT 活基准——读预计算表 reader.pool_return(基准成分逐日=当日池快照,
        #   append-only+batch,类比 market_return;引擎读表不现算)。sec_returns 惰性(同 market,内存)。
        mkt = reader.pool_return(all_dates)
        sec_returns = None
    elif benchmark_mode == "pool":
        sec_returns = {ts: bench.returns_by_date(rows, all_dates) for ts, rows in by_sec.items()}
        mkt = bench.pool_equal_weight_market(sec_returns, pool or set(by_sec), n_dates)
    elif hasattr(reader, "market_return"):
        mkt = reader.market_return(all_dates)          # 真实域:读步3预计算全市场等权(引擎读表不现算)
        sec_returns = None                             # 真实域:sec_returns 事件循环内按票现算(内存优化)
    else:
        sec_returns = {ts: bench.returns_by_date(rows, all_dates) for ts, rows in by_sec.items()}
        mkt = bench.equal_weight_market(sec_returns, n_dates)   # 合成域:现算(路径不变,约束③零回归)

    # ── 逐事件清洗 + compute(存活样本构造=survivors.iter_survivors 单一主干,硬化④)──────
    cleaned: list[CleanedEvent] = []
    valid_events: list[SecurityEvent] = []
    for ce, sv in iter_survivors(event_src, by_sec, all_dates, date_index, mkt, robust_len,
                                 st_mode=st_mode, st_policy=st_policy,
                                 postpone_policy=postpone_policy,
                                 sec_returns=sec_returns, reject_notes=True):
        cleaned.append(ce)
        if sv is None:
            continue
        ev, ce, fit, est_ar_by_date, rows = sv
        est_lo = ce.t_idx + fc.EST_WINDOW_OFFSET_START
        est_hi = ce.t_idx + fc.EST_WINDOW_OFFSET_END
        # 事件窗 τ=0..robust_len-1(检验窗,τ=0=tau0_idx=T+1,含一字板顺延)
        w_idx = [ce.tau0_idx + k for k in range(robust_len)]
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

        # 可交易口径进/出场价捕获(选项2;pap cost 冻结):进场=τ=0(w_idx[0]=tau0_idx)后复权 open,
        #   出场=窗尾(主 w_idx[main_len-1]/稳健 w_idx[robust_len-1])后复权 close。窗尾缺行→exit_status
        #   记 suspend_or_missing、close=None(execution 排除,不以不可成交价充数)。纯读价,不碰统计路径。
        def _exit_status(idx, _bi=ev_by_idx):
            row = _bi.get(idx)
            if row is None:
                return "suspend_or_missing"
            if row.limit_status in ("one_word", "limit_up", "limit_down"):
                return row.limit_status
            return "none"

        _entry_row = ev_by_idx.get(w_idx[0])
        _exit_main = ev_by_idx.get(w_idx[main_len - 1])
        _exit_rob = ev_by_idx.get(w_idx[robust_len - 1])
        tradeable = {
            "entry_open": _entry_row.open if _entry_row is not None else None,
            "exit_close_main": _exit_main.close if _exit_main is not None else None,
            "exit_close_robust": _exit_rob.close if _exit_rob is not None else None,
            "exit_status_main": _exit_status(w_idx[main_len - 1]),
            "exit_status_robust": _exit_status(w_idx[robust_len - 1]),
        }

        se_meta = {"ts_code": ev.ts_code, "event_id": ev.event_id, "board": ce.board,
                   "regime_segment": ce.regime_segment, "industry": ce.industry,
                   "postponed": ce.postponed, "is_st": ce.is_st, "diag_censor": diag_censor,
                   "event_type_layer": ev.event_type_layer,   # 三层分解(pap layers/event_def)
                   "tradeable": tradeable}                     # 可交易口径进/出场价(选项2)
        if is_drawdown:   # #2b:D1/D2/D3 诊断带入(报告项聚合;#4 台账事件无此属性 → se_meta 不变,约束③)
            se_meta["drawdown"] = (ev.d1_never_broke_ma10, ev.d2_episode_to_entry_days,
                                   ev.d3_broke_ma20_before_entry)
        # 秩检验输入:估计窗 AR(相对位置 -250..-91)+ 事件窗 AR;日历法输入:窗内日期+AR
        est_ar_seq = [fit.abnormal[j] for j in range(est_lo, est_hi + 1)]
        w_dates = [all_dates[j] for j in w_idx]
        rank_sec = RankSecurity(est_ar_seq, se.event_abnormal)
        cal_ev = CalEvent(w_dates, se.event_abnormal)
        valid_events.append((se, se_meta, rank_sec, cal_ev))

    return _assemble(pap, cleaned, valid_events, benchmark_mode, main_len, robust_len,
                     strata_enabled=strata_enabled,
                     drawdown_events=(event_src if is_drawdown else None),
                     secondary_lens=secondary_lens, st_policy=st_policy,
                     verdict_policy=verdict_policy, nfv_structured=nfv_structured,
                     postpone_policy=postpone_policy, diagnostic_dims=diagnostic_dims)


def _assemble(pap, cleaned, valid_events, benchmark_mode, main_len, robust_len,
              *, strata_enabled: bool = True, drawdown_events=None,
              secondary_lens: tuple = (), st_policy: str = "reject",
              verdict_policy: str = "three_method", nfv_structured: bool = False,
              postpone_policy: str = "legacy", diagnostic_dims: tuple = ()) -> dict:
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
        if secondary_lens:
            car["secondary_windows"] = _secondary_car(ses, aar, secondary_lens, rho["rho_bar"])
        # 稳健性两道(spec §6):Corrado 秩 + 日历时间组合法
        robustness = {
            "corrado_rank": corrado_rank(rank_secs, main_len, robust_len),
            "calendar_time": calendar_time(cal_evs, main_len, robust_len),
        }
    rho_bar_combined = per_tau.get("rho_bar") if per_tau else None

    # 三层分解(预喜/预亏/扭亏;pap layers/event_def 冻结定义;层外已在视图排除)——纯增量,
    # 各层独立跑同一流水线(不碰上面 combined 计算路径 → combined 既有键逐字节不变,约束③)。
    # #2b(strata_enabled=False):单信号事件、pap event_def 无 layers → 三层不适用,不误入 'unknown' 层。
    if strata_enabled:
        type_strata = _type_strata(valid_events, main_len, robust_len, alpha,
                                   secondary_lens, verdict_policy=verdict_policy,
                                   nfv=nfv_structured) if n >= 1 else {}
    elif diagnostic_dims:
        # C6 二次回修(人令调整四):exp8 关闭 forecast 专属 type_strata 消费;注记中性、
        # 参数驱动(diagnostic_dims,非按实验编号分支),不复用 forecast 文案。
        type_strata = {"applicable": False,
                       "note": "type_strata 不适用(非 forecast 分层事件);"
                               "分层诊断走 diagnostic_dimensions 两条独立轴(C6 二次回修)"}
    else:
        type_strata = {"applicable": False,
                       "note": "#2b 单信号事件:三层(预喜/预亏/扭亏)不适用(pap event_def 无 layers 维度)"}

    # 可交易口径(选项2;pap cost 冻结;新增键,不碰统计路径 → 既有键零回归)
    tradeable = _tradeable(valid_events, pap.get("cost"), main_len, robust_len) if n >= 1 else {}

    # 板块分层(item 8):有效事件按 board 计数 + 主窗 CAAR;ST 层处置随 st_policy(C2)
    strata = _board_strata(cleaned, valid_events, st_policy=st_policy)

    # 删失诊断窗(步3b,R5;报告项不进 verdict)
    censor_diag = _censor_diagnostic(valid_events) if n >= 1 else {}

    # 行业覆盖(口径④携带,人批 2026-07-08):'unknown' 残余组占比;>5% 升级上报(报告项)
    industry_cov = _industry_coverage(valid_events)

    # 剔除率按年份(item 7)
    rej = year_breakdown(cleaned)

    # verdict(policy 辖:spec §6 三法一致 默认 / adj_bmp_main_only=回修单元 P1-1)
    verdict, verdict_note = _verdict(sample_state, car, robustness, alpha,
                                     policy=verdict_policy)

    # 覆盖统计(item 6):有效事件估计窗有效交易日分布(分母 160,门槛 112)
    cov_days = [ce.coverage_valid_days for ce in cleaned
                if not ce.rejected and ce.coverage_valid_days is not None]
    coverage = {"denominator": fc.EST_WINDOW_LEN, "min_valid": fc.COVERAGE_MIN_VALID,
                "n_valid_events": len(cov_days),
                "valid_days_min": min(cov_days) if cov_days else None,
                "valid_days_max": max(cov_days) if cov_days else None,
                "valid_days_mean": (sum(cov_days) / len(cov_days)) if cov_days else None}

    # #2b D1/D2/D3 诊断(F2;报告项·不进 verdict):generated=池内全部生成事件、valid=过清洗存活子集。
    #   #4(drawdown_events=None)→ 不计、result 不含此键(约束③:#4 result 逐字节不变)。
    drawdown_diag = None
    if drawdown_events is not None:
        gen_triples = [(e.d1_never_broke_ma10, e.d2_episode_to_entry_days,
                        e.d3_broke_ma20_before_entry) for e in drawdown_events]
        val_triples = [v[1]["drawdown"] for v in valid_events if "drawdown" in v[1]]
        drawdown_diag = {
            "note": "F2 事件生成诊断(附录F-rev1;报告项·不进 verdict)。D1=进场前从未破ma10占比、"
                    "D2=回撤触发→进场交易日数分布、D3=进场前曾破ma20占比。generated=池内全部生成事件、"
                    "valid=过A股清洗存活子集(剔停牌/ST/覆盖不足等)。",
            "generated": dde.diagnostic_summary(gen_triples),
            "valid": dde.diagnostic_summary(val_triples),
        }

    result = {
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
        "n_valid": n,                        # 存活事件数(标签订正 2026-07-08:~~n_eff~~ 系存活数非相关折算有效N)
        "n_eff_rho": _n_eff_rho(n, rho_bar_combined),  # 相关性折算有效 N(Kish/KP 两式;ρ̄ 现成,口径④)
        "per_tau": per_tau, "car": car,
        "robustness": robustness,            # 稳健性两道(Corrado 秩 + 日历时间组合,spec §6)
        "type_strata": type_strata,          # 三层分解(预喜/预亏/扭亏;pap 冻结 layers/event_def)
        "tradeable": tradeable,              # 可交易口径(选项2;pap cost 冻结;报告/锚对照,不改判决)
        "rejections_by_layer": layer_year_breakdown(cleaned),  # 剔除分层×年份×原因(停牌回炉议题层维度)
        "board_strata": strata,
        "industry_coverage": industry_cov,    # 口径④携带:'unknown' 残余组占比(报告项;>5% 升级)
        "censor_diagnostic": censor_diag,     # 步3b 删失诊断窗(R5;报告项、不进 verdict)
        "verdict": verdict, "verdict_note": verdict_note,
        "snapshot_batch": pap.get("snapshot_batch_req", "SYNTH"),
    }
    if drawdown_diag is not None:      # #2b 专属键(#4 不含 → 约束③ result 逐字节不变)
        result["drawdown_diagnostic"] = drawdown_diag

    # C6 二次回修:两条独立诊断轴(exp8=('listing_age','st'));参数空默认 → 零新键零回归。
    # 本块由独立 report-only 路径构建(结构上不调用 _verdict,人令调整三)。
    if diagnostic_dims:
        result["diagnostic_dimensions"] = _diagnostic_dimensions(
            cleaned, valid_events, main_len, robust_len, secondary_lens, diagnostic_dims)

    # P1-4(人令调整二):偏差声明唯一权威=pap['bias_statement'],原样携带+来源锚;
    # 既有冻结 pap 均无此键 → 默认路径零新键、报告固定段不变。
    if pap.get("bias_statement"):
        result["bias_statement"] = {
            "text": pap["bias_statement"],
            "source_anchor": "pap['bias_statement'](冻结 PAP 唯一权威来源,P1-4;"
                             "runner 原样携带,report 直接消费)"}

    # 回修单元 C6(2026-07-17,nfv_structured=True 才生效;默认 False → 零新键零回归):
    # 全部非权威结果块注入结构化 not_for_verdict 标记;审计记三参数;唯一 verdict 键=顶层
    # (分层块内已由 _stats_for_subset nfv 改名 sig_state_report_only)。
    if nfv_structured:
        marked = []
        for key in ("per_tau", "n_eff_rho", "robustness", "type_strata", "tradeable",
                    "board_strata", "censor_diagnostic", "industry_coverage",
                    "diagnostic_dimensions"):
            blk = result.get(key)
            if isinstance(blk, dict) and blk:
                blk["not_for_verdict"] = True
                marked.append(key)
        for wkey in ("robust_window", "secondary_windows"):
            blk = result["car"].get(wkey) if result.get("car") else None
            if isinstance(blk, dict) and blk:
                blk["not_for_verdict"] = True
                marked.append(f"car.{wkey}")
        # 字段级角色元数据(人令调整六):主窗内字段逐项对账(未分类新字段 fail-closed);
        # 唯一判决权字段=adj_bmp_car,非权威统计结构化可识别,不靠块名清单。
        mw = (result.get("car") or {}).get("main_window")
        if isinstance(mw, dict) and mw:
            mw["field_roles"] = _main_window_field_roles(mw)
        result["not_for_verdict_policy"] = {
            "enabled": True, "marked_blocks": marked,
            "label": "NOT_FOR_VERDICT · 非权威结果:报告项,不判决、不参与判决、不得择优改判"
                     "(人裁 2026-07-17 回修单元 C6);唯一判决=顶层 verdict(主窗 ADJ-BMP)。"}
    if (st_policy != "reject" or verdict_policy != "three_method" or nfv_structured
            or postpone_policy != "legacy" or diagnostic_dims):
        result["audit"]["premend_params"] = {           # 非默认参数如实入审计(默认跑零新键);
            "st_policy": st_policy, "verdict_policy": verdict_policy,   # 含实际 postpone_policy
            "nfv_structured": nfv_structured, "postpone_policy": postpone_policy,
            "diagnostic_dims": list(diagnostic_dims)}   # (人令调整一:audit 记 postpone_policy)
    return result


def _board_strata(cleaned, valid_events, st_policy: str = "reject") -> dict:
    """板块分层报告(item 8):main/chinext/star/ST。ST 层语义随 st_policy(回修单元 C2):
    'reject' 默认=已剔除层(spec §5,分层留痕,注记原文不变)/'keep'=保留层(计数含 valid)。
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
    if st_policy == "keep":
        strata["_st_note"] = ("ST 为保留层(st_policy='keep',人裁 2026-07-17 回修单元 C2 乙案):"
                              "入主样本与主判决;ST/非ST 分层报告,不分别产生判决")
    else:
        strata["_st_note"] = "ST 为已剔除层(spec §5 ST 剔除);不进池化检验,分层仅计数留痕(item 8 调和)"
    return strata


def _industry_coverage(valid_events) -> dict:
    """行业覆盖(口径④携带,人批 2026-07-08):有效事件中 industry='unknown' 残余组占比。
    'unknown' = industry 缺失(cleaning._norm_industry 归一;不猜不补);>5% 升级上报(escalate)。"""
    inds = [v[0].industry for v in valid_events]
    n = len(inds)
    unk = sum(1 for x in inds if x == "unknown")
    pct = (unk / n) if n else 0.0
    return {"n_valid": n, "unknown_n": unk, "unknown_pct": pct, "escalate": pct > 0.05,
            "note": "industry 缺失归 'unknown' 残余组(口径④;不猜不补);占比>5% 升级上报(人批 2026-07-08)"}


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


def _verdict(sample_state, car, robustness, alpha,
             policy: str = "three_method") -> tuple[str, str]:
    """判决裁决(policy 辖,回修单元 2026-07-17 显式参数化):
    policy='three_method'(默认,spec §6 三法一致裁决,原行为逐字保留):
      · 三法(ADJ-BMP 截面 / Corrado 秩 / 日历时间组合)方向一致才确认效应;
      · 朴素 t 显著而 ADJ-BMP 不显著 → 聚集假阳性,以 ADJ-BMP 为准(NOT_SIG);
      · 日历时间法与截面法方向相反 → 事件密集期,verdict=AMBIGUOUS(报告应补事件加权,Loughran-Ritter);
      · 三法方向不一致 → AMBIGUOUS,报告分歧,不许挑有利的。
    policy='adj_bmp_main_only'(exp8,人裁 2026-07-17 冻结前裁决三.4+回修 P1-1):
      · 唯一判据=主窗 ADJ-BMP 显著性;辅助方法(朴素 t/Corrado 秩/日历时间)反向或反显著
        **不得改变判决**,分歧只入 verdict_note 如实报告;
      · INSUFFICIENT 样本量闸与主窗不可得(AMBIGUOUS)两个前置门不变(非辅助法之改判)。
    显著性取自主检验 ADJ-BMP(双侧 α=family_alpha);终态 ∈ {SIG,NOT_SIG,INSUFFICIENT,AMBIGUOUS}。"""
    if policy not in ("three_method", "adj_bmp_main_only"):
        raise ValueError(f"verdict policy 非法: {policy}")
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

    if policy == "adj_bmp_main_only":
        v = "SIG" if adj_sig else "NOT_SIG"
        note = base + ("判决口径=adj_bmp_main_only(人裁 2026-07-17):唯一判据=主窗 ADJ-BMP;"
                       "辅助方法仅报告、不得改判。")
        divergent = [lab for lab, d in (("Corrado秩", rank_dir), ("日历时间", cal_dir))
                     if d != 0 and adj_dir != 0 and d != adj_dir]
        if divergent:
            note += f"⚠辅助方法方向分歧如实报告(不改判):{'/'.join(divergent)}与 ADJ-BMP 反向。"
        if naive_sig and not adj_sig:
            note += "朴素 t 显著而 ADJ-BMP 不显著 → 疑聚集假阳性(判决已以 ADJ-BMP 为准)。"
        return v, note

    # ── policy='three_method'(spec §6 原行为,逐字保留)──────────────────────────
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
