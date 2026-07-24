"""淘沙 · exp11 high_pullback 250日新高小幅回落事件识别(纯函数,零 I/O)。

口径出处 = 冻结 PAP(taosha/docs/high-pullback-pap-final-2026-07-24.json,
digest eaa54b3da8ede7baf27e3a387454ac0611be999ba351c376b73eadde5aacb6fc,冻结 2026-07-24)
event_def 原文即口径;权威重算先例 = PAP 草案单元只读脚本 s11_pap_scan.py
(交付包 s11_pap_delivery_2026-07-24,双跑 691d6dad…,最终事件集 42,719 只读参考)。
职责边界 = 只做事件识别(新高阶段状态机→阶段结局五分→唯一性 fail-closed→研究期);
不读收益、不判显著、不碰台账。

冻结 event_def 转录(七裁定):
  (1) 新高锚 = 后复权收盘严格 > 此前 250 根真实 bar 最高收盘;锚日不入历史窗;
      历史不足 250 根不成锚(伪新高仅计数)。
  (2) 每次更新高点立即重置锚与 10 日观察期;一段连续上行只形成一个新高阶段。
      (等价性:阶段内任何收盘高于现锚必为 250 日新高——锚为阶段运行最大值且滑窗只弃旧
      不纳旧;观察期外的新高 = 旧阶段 NO_TOUCH 期满 + 另起新阶段。)
  (3) 以最新锚收盘为基准,其后 10 个交易所交易日内(日历轴计窗,cal_rank),首个真实 bar
      收盘落入闭区间 [−5%,−3%] 成候选;首触即 <−5%(含跳空跨带)= DEEP_KILL 阶段终止,
      不得反弹复活;期满未触(含期内无 bar=停牌)= NO_TOUCH 无事件终结。
  (4) 候选日收盘 ≥ 含当日最近 20 根真实 bar 收盘均值 = 事件(条件齐备日);破线 = MA_KILL,
      阶段终结(首触即决,冻结确认清单#3)。筛选力弱也保留,不得据分布删改。
  (5) 每阶段最多一事件;事件键 (ts_code,event_date) 唯一,违背 = fail-closed 全剔留痕;
      不设冷却。阶段结局互斥恰一 = EVENT/MA_KILL/DEEP_KILL/NO_TOUCH/TRUNCATED
      (TRUNCATED = 观察窗跨出数据右界,按全局日历末序号 last_cal_rank 分类,确认清单#4)。
  (6) 研究范围 2011-01-01 ≤ event_date < 2024-07-01;期外仅计数不入事件集。

边界算术(闭区间忠实实现,冻结文本为准):触带/入带/破五/MA20 比较全部用 Decimal 精确
乘法比较,零除法零二进制舍入:触带 close ≤ C0×0.97;入带下沿 close ≥ C0×0.95(闭);
首触即深 close < C0×0.95;MA20 不破 20×close ≥ Σ(最近20收盘)。⚠float 实现(草案对账
脚本 s11_pap_scan.py)在数学恰位边界(如恰 −5%)会因二进制舍入把闭区间端点误判为
DEEP_KILL;冻结文本=闭区间,以精确算术为准;与 42,719 参考的差异按此血缘归因
(冻结令 2026-07-24 五:参考非硬断言,不追数不改规则)。

依赖:仅标准库。输入行 = dict{trade_date: date, close: Decimal|int|str, cal_rank: int,
board: str, is_st: bool};close 推荐 DB numeric 原生 Decimal(driver 保真读取),
float 输入按 str(float) 十进制化(确定性,但边界保真责任在调用方)。
消费方(driver)负责行流→dict 映射与按票分组;本模块单票处理,跨票聚合+全局唯一性/
研究期漏斗在 merge_selections/finalize_events(调用方按 ts_code 序喂入=确定性)。
"""
from __future__ import annotations

import datetime as dt
from collections import deque
from decimal import Decimal

# ── 冻结 PAP 参数(digest eaa54b3d…b6fc;口径唯一,禁散落魔法数)───────────────────
W_HIGH = 250                                   # 新高历史窗(此前真实 bar 数,锚日不入窗)
W_OBS = 10                                     # 观察窗(锚后交易所交易日数,日历轴)
W_MA = 20                                      # 均线窗(真实 bar,含当日)
BAND_TOUCH = Decimal("0.97")                   # 触带上沿:close ≤ C0×0.97 ⟺ ret ≤ −3%
BAND_FLOOR = Decimal("0.95")                   # 入带下沿(闭):close ≥ C0×0.95 ⟺ ret ≥ −5%
MA_MULT = Decimal(W_MA)                        # MA20 精确比较乘数(20×close ≥ Σ20)
EVENT_DATE_START = dt.date(2011, 1, 1)         # 研究期下界(含;裁定六)
EVENT_DATE_END = dt.date(2024, 7, 1)           # 上界(不含;==holdout 焊死线)

# 阶段结局(互斥恰一;counters 键=OUTCOME_ 前缀)
OUTCOME_EVENT = "EVENT"
OUTCOME_MA_KILL = "MA_KILL"
OUTCOME_DEEP_KILL = "DEEP_KILL"
OUTCOME_NO_TOUCH = "NO_TOUCH"
OUTCOME_TRUNCATED = "TRUNCATED"
OUTCOMES = (OUTCOME_EVENT, OUTCOME_MA_KILL, OUTCOME_DEEP_KILL,
            OUTCOME_NO_TOUCH, OUTCOME_TRUNCATED)

# 全局漏斗剔除原因(finalize_events;reason 值同为 rejects 留痕键)
REASON_PRE2011 = "out_of_period_pre2011"
REASON_POST = "out_of_period_post"
REASON_DUPLICATE = "event_key_duplicate_fail_closed"


def _dec(v) -> Decimal:
    """输入价 → Decimal(DB numeric 原生 Decimal 直通=精确;float 经 str 十进制化=确定性)。"""
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def select_high_pullback_events(ts_code: str, rows: list[dict],
                                last_cal_rank: int) -> dict:
    """单票新高阶段状态机(冻结 event_def (1)-(5) 阶段面;纯函数,双跑同)。

    rows = 该票真实交易行按 trade_date 升序(调用方保证);cal_rank 严格递增否则 fail-closed。
    last_cal_rank = 全局日历末序号(数据右界;TRUNCATED/NO_TOUCH 分类唯一依据,确认清单#4)。
    返回 {"events": [...], "counters": {...}}——events 为全年份阶段事件(研究期/唯一性
    漏斗在 finalize_events 全局施加);counters 含阶段结局五分+新高恒等式件+首触偏移分布。
    """
    n = len(rows)
    closes = [_dec(r["close"]) for r in rows]
    ranks = [r["cal_rank"] for r in rows]
    for k in range(1, n):
        if ranks[k] <= ranks[k - 1]:
            raise ValueError(f"{ts_code}: cal_rank 非严格递增(行{k})——fail-closed,不猜不补")
    pref = [Decimal(0)] * (n + 1)              # Decimal 前缀和(MA20 精确比较)
    for i, c in enumerate(closes):
        pref[i + 1] = pref[i] + c
    g = {"input_rows": n, "newhigh_days": 0, "pseudo_newhigh_hist_insufficient": 0,
         "stages": 0, "resets_within_stage": 0}
    for o in OUTCOMES:
        g["outcome_" + o] = 0
    for k in range(1, W_OBS + 1):
        g[f"offset_{k}"] = 0                   # 首触偏移(交易所交易日)分布
    events: list[dict] = []
    dq: deque = deque()                        # 递减 (idx, close);窗=[i-250, i-1]
    runmax = Decimal("-1")
    anc = None                                 # (a_i, a_close, a_rank, resets_in_stage)

    def _close_stage(outcome: str) -> None:
        g["outcome_" + outcome] += 1

    for i in range(n):
        c, r = closes[i], ranks[i]
        if i >= W_HIGH:
            while dq and dq[0][0] < i - W_HIGH:
                dq.popleft()
            newhigh = bool(dq) and c > dq[0][1]
        else:
            newhigh = False
            if i >= 1 and c > runmax:
                g["pseudo_newhigh_hist_insufficient"] += 1   # 伪新高:不成锚仅计数(裁定一)
        if anc is not None:
            a_i, a_c, a_r, a_resets = anc
            if newhigh:
                g["newhigh_days"] += 1
                if r <= a_r + W_OBS:           # 观察期内更新高点=重置锚与观察期(同一阶段)
                    g["resets_within_stage"] += 1
                    anc = (i, c, r, a_resets + 1)
                else:                          # 旧阶段期满未触=NO_TOUCH;本新高另起新阶段
                    _close_stage(OUTCOME_NO_TOUCH)
                    g["stages"] += 1
                    anc = (i, c, r, 0)
            elif r > a_r + W_OBS:              # 期满(含长停牌后恢复首 bar 才观测到)
                _close_stage(OUTCOME_NO_TOUCH)
                anc = None
            else:
                if c <= a_c * BAND_TOUCH:      # 首触 ≤−3%(精确算术;首触即决)
                    g[f"offset_{r - a_r}"] += 1
                    if c >= a_c * BAND_FLOOR:  # 闭区间 [−5%,−3%] 入带=候选
                        if MA_MULT * c >= pref[i + 1] - pref[i + 1 - W_MA]:
                            _close_stage(OUTCOME_EVENT)
                            events.append({
                                "ts_code": ts_code,
                                "anchor_date": rows[a_i]["trade_date"].isoformat(),
                                "event_date": rows[i]["trade_date"].isoformat(),
                                "offset_days": r - a_r,
                                "resets_in_stage": a_resets,
                                "anchor_close": str(a_c), "event_close": str(c),
                                "pullback_pct": float(
                                    ((c / a_c - 1) * 100).quantize(Decimal("0.0001"))),
                                "board_event": rows[i].get("board"),
                                "is_st_event": rows[i].get("is_st")})
                        else:
                            _close_stage(OUTCOME_MA_KILL)   # 破线=阶段无事件终结(首触即决)
                    else:
                        _close_stage(OUTCOME_DEEP_KILL)     # 首触即深(含跳空)=终止不复活
                    anc = None
        else:
            if newhigh:
                g["newhigh_days"] += 1
                g["stages"] += 1
                anc = (i, c, r, 0)
        while dq and dq[-1][1] <= c:
            dq.pop()
        dq.append((i, c))
        if c > runmax:
            runmax = c
    if anc is not None:                        # 数据尽头未决:按全局日历右界分类(确认清单#4)
        _close_stage(OUTCOME_NO_TOUCH if anc[2] + W_OBS <= last_cal_rank
                     else OUTCOME_TRUNCATED)
    return {"events": events, "counters": g}


def merge_selections(per_security: list[dict]) -> dict:
    """跨票聚合(调用方按 ts_code 序逐票喂入):events 拼接(票内事件日序),
    counters 逐键求和。纯函数,不排序不改行。"""
    events: list[dict] = []
    counters: dict = {}
    for sel in per_security:
        events.extend(sel["events"])
        for k, v in sel["counters"].items():
            counters[k] = counters.get(k, 0) + v
    return {"events": events, "counters": counters}


def finalize_events(merged: dict) -> dict:
    """全局漏斗尾档(冻结 event_def (5)(6);纯函数):
    ① 事件键 (ts_code,event_date) 唯一性 fail-closed——违背键的全部事件剔除逐条留痕,
       不合并不择一(阶段语义下结构性预期 0,断言面交 fixture);
    ② 研究期 2011-01-01 ≤ event_date < 2024-07-01,期外仅计数(逐年留痕)不入事件集。
    返回 {"events"(最终事件集), "rejects", "counters", "reject_reasons"}。"""
    events = merged["events"]
    counters = dict(merged["counters"])
    by_key: dict = {}
    for e in events:
        by_key.setdefault((e["ts_code"], e["event_date"]), []).append(e)
    rejects: list[dict] = []
    survivors: list[dict] = []
    dup_keys = 0
    for e in events:                            # 保序遍历(确定性)
        grp = by_key[(e["ts_code"], e["event_date"])]
        if len(grp) > 1:
            rejects.append(dict(e, reason=REASON_DUPLICATE, n_colliding=len(grp)))
            continue
        survivors.append(e)
    dup_keys = sum(1 for grp in by_key.values() if len(grp) > 1)
    final: list[dict] = []
    for e in survivors:
        d = dt.date.fromisoformat(e["event_date"])
        if d < EVENT_DATE_START:
            rejects.append(dict(e, reason=REASON_PRE2011))
        elif d >= EVENT_DATE_END:
            rejects.append(dict(e, reason=REASON_POST))
        else:
            final.append(e)
    reasons: dict = {}
    for r in rejects:
        reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    counters["events_all_years"] = len(events)
    counters["event_key_uniqueness_violations"] = dup_keys
    counters["uniqueness_dropped_events"] = reasons.get(REASON_DUPLICATE, 0)
    counters[REASON_PRE2011] = reasons.get(REASON_PRE2011, 0)
    counters[REASON_POST] = reasons.get(REASON_POST, 0)
    counters["final_events"] = len(final)
    return {"events": final, "rejects": rejects, "counters": counters,
            "reject_reasons": reasons}
