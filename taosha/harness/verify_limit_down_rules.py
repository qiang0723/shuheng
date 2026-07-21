"""exp13 limit_down_open 事件规则攻击 fixture 自检(冻结令 2026-07-21;零 DB、零真实数据、零收益)。

覆盖交付档(limit-down-open-pap-draft-delivery-2026-07-21.md §6)预注册 18 组攻击 fixture
F1~F18(输入几何→预期行为→攻击点逐组转录);另证:确定性双跑/跨票聚合/空输入退化/
一字开盘位异常行顺延分计(deferred_anom)。
冻结口径 = PAP digest 583c4c94…0c42 event_def(令七.4 主漏斗固定顺序:原始最大链→右删失→
研究期外→listing异常→duplicate→reversal_hijack→主事件集;互斥主原因)。
用法: python taosha/harness/verify_limit_down_rules.py
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.compute.limit_down_rules import (  # noqa: E402
    N_MIN, merge_selections, select_limit_down_events)
from taosha.harness.run_limit_down_study import selection_audit  # noqa: E402(纯函数,零 DB)

FAIL = 0
N = 0


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    if not ok:
        FAIL += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


_BASE = dt.date(2015, 3, 2)   # 研究期内基准日;fixture 日期仅需升序(行序=自身交易行序)

# 形态字典:D=一字跌停(链成员)/ U=一字涨停(hijack 判据)/ ow_none=一字开盘位异常 /
# none=普通 / open_down=触跌停开盘在跌停位但非一字(真开板,F6)/ limit_down=触跌停未一字
_KIND = {
    "D":          ("one_word", "open_at_down_limit"),
    "U":          ("one_word", "open_at_up_limit"),
    "ow_none":    ("one_word", "none"),
    "none":       ("none", "none"),
    "open_down":  ("limit_down", "open_at_down_limit"),
    "limit_down": ("limit_down", "none"),
    "limit_up":   ("limit_up", "none"),
}


def _rows(spec, base=_BASE):
    """spec = [(日偏移, 形态)] 或 [(日偏移, 形态, board, is_st)];日偏移跳号即停牌缺 bar。"""
    out = []
    for item in spec:
        off, k = item[0], item[1]
        board = item[2] if len(item) > 2 else "main"
        is_st = item[3] if len(item) > 3 else False
        ls, ols = _KIND[k]
        out.append({"trade_date": base + dt.timedelta(days=off),
                    "limit_status": ls, "open_limit_status": ols,
                    "board": board, "is_st": is_st})
    return out


def sel(spec, ts="000001.SZ", base=_BASE, listing="auto", cal_days=None):
    """listing='auto' → 健康上市窗;cal_days=日历轴日偏移列表(B 口径镜像开关)。"""
    rows = _rows(spec, base)
    if listing == "auto":
        listing = {"list_date": rows[0]["trade_date"] if rows else base, "delist_date": None}
    cal_index = None
    if cal_days is not None:
        cal_index = {base + dt.timedelta(days=off): i for i, off in enumerate(cal_days)}
    return select_limit_down_events(ts, rows, listing=listing, cal_index=cal_index)


def ev_dates(s):
    return [e["event_date"] for e in s["events"]]


def d(off, base=_BASE):
    return (base + dt.timedelta(days=off)).isoformat()


check("冻结值 N_MIN=2(准入下限,非运行时可选)", N_MIN, 2)

# ── F1:N=1 不成链 / N=2 成链 ─────────────────────────────────────────────────────
s = sel([(0, "D")])
check("F1 单根D̄:零链(len1 run 计数)、零事件",
      (s["counters"]["chains_total"], s["counters"]["runs_len1_not_chain"], len(s["events"])),
      (0, 1, 0))
s = sel([(0, "D"), (1, "D"), (2, "none")])
check("F1 两根D̄D̄:恰1链len2,事件日=链后首个非一字行",
      (s["counters"]["chains_total"], s["events"][0]["chain_len"], ev_dates(s)), (1, 2, [d(2)]))

# ── F2:最大饱和链禁截子链 ─────────────────────────────────────────────────────────
s = sel([(0, "D"), (1, "D"), (2, "D"), (3, "D"), (4, "D"), (5, "none")])
check("F2 D̄×5:恰1链len5恰1事件;len2/3/4子链计数=0",
      (s["counters"]["chains_total"], s["events"][0]["chain_len"], len(s["events"])), (1, 5, 1))
s2 = sel([(0, "D"), (1, "D"), (2, "D"), (3, "D"), (4, "D"), (5, "none")])
check("F2 确定性:同输入双跑逐项相等", s == s2, True)

# ── F3:停牌缺 bar 不重置 A 链(B 口径镜像拆段仅诊断)──────────────────────────────
_F3 = [(0, "D"), (1, "D"), (5, "D"), (6, "none")]
_F3_CAL = list(range(0, 7))                      # 日历轴覆盖 0..6(2/3/4 日历在轴、票缺 bar)
s = sel(_F3, cal_days=_F3_CAL)
check("F3 A口径:行序连续恰1链len3(缺bar不重置)",
      (s["counters"]["chains_total"], s["events"][0]["chain_len"], ev_dates(s)), (1, 3, [d(6)]))
check("F3 B口径镜像:日历断档拆2段=1链len2+1个len1段(仅诊断)",
      (s["b_control"]["counters"]["chains_total"],
       s["b_control"]["counters"]["runs_len1_not_chain"]), (1, 1))

# ── F4:真实非一字 bar 必须断链 ────────────────────────────────────────────────────
s = sel([(0, "D"), (1, "D"), (2, "none"), (3, "D"), (4, "D"), (5, "none")])
check("F4 D̄D̄,none,D̄D̄:恰2链各len2,两事件日",
      (s["counters"]["chains_total"], [e["chain_len"] for e in s["events"]], ev_dates(s)),
      (2, [2, 2], [d(2), d(5)]))
s = sel([(0, "D"), (1, "limit_down"), (2, "D"), (3, "D"), (4, "none")])
check("F4 触跌停未一字真实bar断链(禁跨拼接;前段单板不成链)",
      (s["counters"]["chains_total"], s["counters"]["runs_len1_not_chain"],
       s["events"][0]["chain_start_date"]), (1, 1, d(2)))
s = sel([(0, "ow_none"), (1, "D"), (2, "D"), (3, "none")])
check("F4 双条件判据:one_word但开盘位非down不入链",
      (s["events"][0]["chain_start_date"], s["events"][0]["chain_len"]), (d(1), 2))

# ── F5:反向一字涨停触发 hijack 并排除 ─────────────────────────────────────────────
s = sel([(0, "D"), (1, "D"), (2, "U"), (3, "none")])
check("F5 D̄D̄,Ū,none:链存在但主集=0,hijack=1",
      (s["counters"]["chains_total"], s["counters"]["reversal_hijack"],
       s["counters"]["final_main_events"]), (1, 1, 0))
hj = [r for r in s["rejects"] if r["reason"] == "reversal_hijack"]
check("F5 audit含该链(顺延结构up=1;none日不成为主集事件)",
      (len(hj), hj[0]["deferred_up"], hj[0]["event_date"], len(s["events"])), (1, 1, d(3), 0))

# ── F6:真开板保留(open_at_down_limit ∧ 非 one_word)──────────────────────────────
s = sel([(0, "D"), (1, "D"), (2, "open_down"), (3, "none")])
check("F6 X=open_at_down_limit∧limit_down≠one_word:合法事件日保留主集,不触发hijack",
      (ev_dates(s), s["events"][0]["evday_open_status"], s["counters"]["reversal_hijack"]),
      ([d(2)], "open_at_down_limit", 0))

# ── F7:重复映射全剔(duplicate 优先于 hijack,互斥主原因)─────────────────────────
s = sel([(0, "D"), (1, "D"), (2, "U"), (3, "D"), (4, "D"), (5, "none")])
check("F7 链1顺延穿Ū与链2达同一none日:duplicate两链全剔,主集=0,不合并不择一",
      (s["counters"]["duplicate_event_days"], s["counters"]["duplicate_chains_dropped"],
       s["counters"]["final_main_events"], s["counters"]["reversal_hijack"]), (1, 2, 0, 0))
dups = [r for r in s["rejects"] if r["reason"] == "duplicate_event_date_mapping"]
check("F7 逐条留痕(reason+碰撞链数;含 deferred_up=1 的链1同以 duplicate 为互斥主原因)",
      (sorted((r["n_chains_colliding"], r["deferred_up"]) for r in dups)), [(2, 0), (2, 1)])

# ── F8:listing 三类异常 fail-closed ──────────────────────────────────────────────
_ok = [(0, "D"), (1, "D"), (2, "none")]
s = sel(_ok, listing=None)
check("F8① 缺listing:该票候选全剔计入listing档,按类留痕",
      ([r["reason"] for r in s["rejects"]], s["counters"]["listing_anomaly"],
       s["counters"].get("listing_anomaly_listing_missing_fail_closed", 0)),
      (["listing_missing_fail_closed"], 1, 1))
s = sel(_ok, listing={"list_date": _BASE + dt.timedelta(days=1), "delist_date": None})
check("F8② 上市日前历史bar", [r["reason"] for r in s["rejects"]], ["pre_listing_bar_fail_closed"])
s = sel(_ok, listing={"list_date": _BASE, "delist_date": _BASE})
check("F8③ 上市区间异常(delist≤list)", [r["reason"] for r in s["rejects"]],
      ["listing_window_anomaly_fail_closed"])
s = sel(_ok, listing={"list_date": _BASE, "delist_date": _BASE + dt.timedelta(days=2)})
check("F8③ bar落在退市日当日及之后", [r["reason"] for r in s["rejects"]],
      ["listing_window_anomaly_fail_closed"])
s = sel(_ok, listing={"list_date": _BASE, "delist_date": _BASE + dt.timedelta(days=3)})
check("F8 健康退市窗(末bar<delist):事件照收",
      (ev_dates(s), s["counters"]["listing_anomaly"]), ([d(2)], 0))

# ── F9:ST 切换按事件日归层(令三.3)────────────────────────────────────────────────
s = sel([(0, "D", "main", False), (1, "D", "main", False), (2, "none", "main", True)])
check("F9 链起点非ST/事件日ST:入主集且is_st_event=True(事件日PIT归层)",
      (len(s["events"]), s["events"][0]["is_st_event"], s["events"][0]["is_st_chain"]),
      (1, True, False))
check("F9 st_flag_chain_vs_eventday_diff计数+逐条留痕,主判决面不变(事件仍在主集)",
      (s["counters"]["st_flag_chain_vs_eventday_diff"],
       s["events"][0].get("st_flag_chain_vs_eventday_diff")), (1, True))

# ── F10:研究期上下界 ─────────────────────────────────────────────────────────────
_b06 = dt.date(2006, 12, 27)
s = sel([(0, "D"), (1, "D"), (2, "none")], base=_b06)   # 事件日 2006-12-29
check("F10 事件日=2006-12-29:剔out_of_period_pre2007",
      ([r["reason"] for r in s["rejects"]], len(s["events"])),
      (["out_of_period_pre2007"], 0))
s = sel([(3, "D"), (4, "D"), (5, "none")], base=_b06)   # 链2006末,事件日2007-01-01
check("F10 事件日=2007-01-01:保留(按event_date判)", ev_dates(s), ["2007-01-01"])
_b24 = dt.date(2024, 6, 26)
s = sel([(0, "D"), (1, "D"), (2, "none")], base=_b24)   # 事件日 2024-06-28
check("F10 事件日=2024-06-28:保留", ev_dates(s), ["2024-06-28"])
s = sel([(0, "D"), (1, "D"), (5, "none")], base=_b24)   # 事件日 2024-07-01
check("F10 事件日≥2024-07-01:剔out_of_period_post(结构上holdout视图焊死+此处再挡一道)",
      ([r["reason"] for r in s["rejects"]], len(s["events"])), (["out_of_period_post"], 0))

# ── F11:科创板单行不成链 ─────────────────────────────────────────────────────────
s = sel([(0, "D", "star")])
check("F11 star板单根D̄:len1 run不成链,零事件(star层零事件由诊断层如实报告)",
      (s["counters"]["runs_len1_not_chain"], s["counters"]["chains_total"], len(s["events"])),
      (1, 0, 0))

# ── F13:右删失∧hijack 互斥主原因(补充令1)────────────────────────────────────────
s = sel([(0, "D"), (1, "D"), (2, "U")])   # 数据终止于 Ū
check("F13 D̄D̄,Ū,〔终止〕:主漏斗记right_censored=1,hijack档=0",
      (s["counters"]["right_censored_no_event_day"], s["counters"]["reversal_hijack"]),
      (1, 0))
rc = [r for r in s["rejects"] if r["reason"] == "right_censored_no_event_day"]
check("F13 audit正交标志reversal_hijack_observed_before_censoring=True,重叠计数=1",
      (rc[0].get("reversal_hijack_observed_before_censoring"),
       s["counters"]["reversal_hijack_observed_before_censoring"]), (True, 1))

# ── F14:纯右删失 ─────────────────────────────────────────────────────────────────
s = sel([(0, "D"), (1, "D")])
check("F14 D̄D̄〔终止〕:right_censored=1,正交标志缺省/False,hijack=0",
      (s["counters"]["right_censored_no_event_day"],
       s["counters"]["reversal_hijack_observed_before_censoring"],
       s["counters"]["reversal_hijack"],
       [r.get("reversal_hijack_observed_before_censoring") for r in s["rejects"]]),
      (1, 0, 0, [None]))

# ── F15:链后停牌跨档开板保留 ─────────────────────────────────────────────────────
s = sel([(0, "D"), (1, "D"), (4, "none")])   # 2/3 日缺 bar=停牌
check("F15 D̄D̄〔缺bar×2〕none:事件日=none行保留;停牌缺bar不误入顺延计数(deferred全0)",
      (ev_dates(s), s["events"][0]["deferred_up"], s["events"][0]["deferred_down"],
       s["events"][0]["deferred_anom"]), ([d(4)], 0, 0, 0))
check("F15 停牌跨档诊断可观测=chain_end_date与event_date留痕(几何字段自证间隔)",
      (s["events"][0]["chain_end_date"], s["events"][0]["event_date"]), (d(1), d(4)))

# ── F16:混合一字顺延结构 ─────────────────────────────────────────────────────────
s = sel([(0, "D"), (1, "D"), (2, "U"), (3, "D"), (4, "none")])
check("F16 D̄D̄,Ū,D̄,none:链1顺延up=1,down=1→hijack剔除;len1段不成链;主集=0",
      (s["counters"]["chains_total"], s["counters"]["runs_len1_not_chain"],
       s["counters"]["reversal_hijack"], s["counters"]["final_main_events"]), (1, 1, 1, 0))
hj = [r for r in s["rejects"] if r["reason"] == "reversal_hijack"]
check("F16 hijack链顺延结构分计(up=1/down=1/anom=0)",
      (hj[0]["deferred_up"], hj[0]["deferred_down"], hj[0]["deferred_anom"]), (1, 1, 0))
s = sel([(0, "D"), (1, "D"), (2, "ow_none"), (3, "none")])
check("F16补 一字开盘位异常行:顺延分计入anom,不触发hijack",
      (s["counters"]["reversal_hijack"], ev_dates(s), s["events"][0]["deferred_anom"]),
      (0, [d(3)], 1))

# ── F17:创业板改革边界(300216 实案镜像;PIT 制度价位=视图责任,规则唯一判据=旗标双条件)──
_b20 = dt.date(2020, 8, 21)   # 改革日 2020-08-24 前最后交易日
s = sel([(0, "D", "chinext"), (3, "D", "chinext"), (4, "none", "chinext")], base=_b20)
check("F17 chinext链跨2020-08-24(两侧均按当日制度价位判为一字):恰1链len2,事件保留",
      (s["counters"]["chains_total"], s["events"][0]["chain_len"],
       s["events"][0]["board_event"], ev_dates(s)), (1, 2, "chinext", [d(4, _b20)]))
s = sel([(0, "D", "chinext"), (3, "limit_down", "chinext"), (4, "D", "chinext"),
         (5, "D", "chinext"), (6, "none", "chinext")], base=_b20)
check("F17 改革日后按20%不再判一字(视图PIT旗标)→真实bar断链,前段len1不成链",
      (s["counters"]["chains_total"], s["counters"]["runs_len1_not_chain"],
       s["events"][0]["chain_start_date"]), (1, 1, d(4, _b20)))

# ── F18:B 口径 NFV 不改主集(F3 同几何)───────────────────────────────────────────
s_nocal = sel(_F3)                       # 不开 B 镜像
s_cal = sel(_F3, cal_days=_F3_CAL)       # 开 B 镜像
check("F18 A=1链入主漏斗;B仅入对照块;主事件集只认A(开关B前后主集逐项相等)",
      (s_cal["events"] == s_nocal["events"], s_nocal["b_control"] is None,
       s_cal["b_control"] is not None), (True, True, True))
check("F18 B碰撞计数不影响主集(B档计数独立,A最终主集=1)",
      (s_cal["counters"]["final_main_events"], s_cal["b_control"]["counters"]["final_main_events"],
       s_cal["b_control"]["not_for_verdict"]), (1, 1, True))

# ── F12:诊断层递归零 verdict(构造含 ST/listing_age/B对照/hijack audit 的完整 result)──
_cal_all = list(range(0, 12))
per_sec = [
    sel([(0, "D"), (1, "D"), (2, "none", "main", True)], ts="000010.SZ", cal_days=_cal_all),  # ST事件日
    sel([(0, "D"), (1, "D"), (2, "U"), (3, "none")], ts="000011.SZ", cal_days=_cal_all),      # hijack
    sel([(0, "D"), (1, "D"), (2, "none")], ts="000012.SZ", listing=None, cal_days=_cal_all),  # listing剔
    sel([(0, "D"), (1, "D"), (5, "D"), (6, "none")], ts="000013.SZ", cal_days=_cal_all),      # B拆段
]
m = merge_selections(per_sec)
aud = selection_audit(m)
result = {"verdict": "NOT_SIG", "audit": {"limit_down_selection": aud,
                                          "study_snapshot": {"snapshot_id": 0, "digest": "synthetic"}}}


def _scan_key(obj, key):
    n = 0
    if isinstance(obj, dict):
        for k, v in obj.items():
            n += (1 if k == key else 0) + _scan_key(v, key)
    elif isinstance(obj, list):
        for v in obj:
            n += _scan_key(v, key)
    return n


def _scan_values(obj, targets):
    n = 0
    if isinstance(obj, dict):
        for v in obj.values():
            n += _scan_values(v, targets)
    elif isinstance(obj, list):
        for v in obj:
            n += _scan_values(v, targets)
    elif isinstance(obj, str) and obj in targets:
        n += 1
    return n


check("F12 诊断块零判决字段:audit子树verdict/verdict_note=0,顶层verdict唯一",
      (_scan_key(result["audit"], "verdict"), _scan_key(result["audit"], "verdict_note"),
       _scan_key(result, "verdict")), (0, 0, 1))
check("F12 audit子树无显著性分类值(SIG/NOT_SIG/AMBIGUOUS/INSUFFICIENT)",
      _scan_values(result["audit"], {"SIG", "NOT_SIG", "AMBIGUOUS", "INSUFFICIENT"}), 0)
check("F12 NFV标记在场(st轴/hijack审计/B对照三块)",
      (aud["st_axis"]["not_for_verdict"], aud["reversal_hijack_audit"]["not_for_verdict"],
       aud["b_axis_control"]["not_for_verdict"]), (True, True, True))
check("F12 主漏斗七档总恒等(令七.4)", aud["funnel"]["identity_ok"], True)
check("F12 各档计数(链4=hijack1+listing1+主集2;ST轴1/1;B恒等同过)",
      (aud["funnel"]["原始最大链"], aud["funnel"]["reversal_hijack"],
       aud["funnel"]["listing_anomaly"], aud["funnel"]["final_main_events"],
       aud["st_axis"]["counts"], aud["b_axis_control"]["funnel"]["identity_ok"]),
      (4, 1, 1, 2, {"ST": 1, "non_ST": 1}, True))
check("F12 hijack审计份额分母显式(令五.4:hijack+主集=3为存活候选分母)",
      (aud["reversal_hijack_audit"]["share"]["numerator"],
       aud["reversal_hijack_audit"]["share"]["denominator_surviving_candidates"],
       aud["reversal_hijack_audit"]["share"]["denominator_raw_chains"]), (1, 3, 4))

# ── 跨票聚合/空输入退化(通用面)───────────────────────────────────────────────────
check("聚合:events/rejects/counters求和+reject_reasons计数",
      (len(m["events"]), m["counters"]["chains_total"],
       m["reject_reasons"]["reversal_hijack"], m["reject_reasons"]["listing_missing_fail_closed"]),
      (2, 4, 1, 1))
s = sel([])
check("空输入:零链零事件零剔除",
      (s["counters"]["input_rows"], len(s["events"]), len(s["rejects"])), (0, 0, 0))
s = sel([(0, "none"), (1, "limit_down"), (2, "U")])
check("无链票:单日一字涨停/触板行不成链", (s["counters"]["chains_total"], len(s["events"])), (0, 0))

print(f"\n{'='*60}\nverify_limit_down_rules: {N - FAIL}/{N} PASS"
      + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
