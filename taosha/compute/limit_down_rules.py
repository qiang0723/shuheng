"""淘沙 · exp13 limit_down_open 一字跌停链开板事件识别(纯函数,零 I/O)。

口径出处 = 冻结 PAP(taosha/docs/limit-down-open-pap-final-2026-07-21.json,
digest 583c4c946078006aef6061cdc405d7255d16a7bfd9d36bdb3c3793f57f0e0c42,冻结令 2026-07-21)
event_def 原文即口径;权威漏斗实现先例 = PAP 草案单元只读对账脚本 s13recon.py
(交付包 s13_pap_delivery_2026-07-21,双跑逐字节一致,36/36 恒等断言)。
职责边界 = 只做事件识别(链检测→事件日顺延→主漏斗七档)+ B 口径 NFV 诊断镜像;
不读收益、不判显著、不碰台账。

冻结 event_def 转录:
  · 链成员唯一判据 = limit_status='one_word' AND open_limit_status='open_at_down_limit'
    (双条件缺一不可;方向由 open_limit_status 定)。
  · N_MIN=2 为明确冻结值(准入下限):长度不少于 2 的最大饱和一字跌停链进入候选;
    N 不是运行时可选参数、不保留 N 的运行时选择;每段只取唯一最大饱和链,不截取子链。
  · A 口径连续性 = 个股自身真实交易行序连续:停牌缺 bar 不计交易日、不重置链;
    行序相邻但非一字跌停的真实 bar = 链断点(禁跨拼接)。
  · 事件日 = 链后首个 limit_status != 'one_word' 的真实交易行(链后任何方向一字状态
    继续顺延;停牌日无行 → 结构上不可能成为事件日);真开板保留:事件日
    open_limit_status='open_at_down_limit' 但 limit_status!='one_word' 属合法开板事件。
  · reversal_hijack(令二):链尾与事件日之间存在 ≥1 根 one_word AND open_at_up_limit
    行 → 该链不进入主事件集,逐条入 audit(全 NOT_FOR_VERDICT,禁收益/CAR/显著性)。
  · 右删失∧hijack 重叠(补充令1)= 互斥主原因:先记 right_censored_no_event_day,
    不进 hijack 剔除数;audit 另记正交标志 reversal_hijack_observed_before_censoring。
  · 主漏斗固定顺序及互斥主原因(令七.4)= 原始最大链 → 右删失 → 研究期外 →
    listing 异常 → duplicate mapping → reversal_hijack → 最终主事件集。
  · B 口径(交易所日历连续)= 固定 NFV 诊断对照(令一.4):同一漏斗镜像,
    不得改变主事件集。
  · 研究期 2007-01-01 ≤ event_date < 2024-07-01;recent_listing = 链起点上市交易龄 ≤30
    (自身真实交易行序号,上市首 bar=第 1 行),仅 NFV 标记不改事件集。

listing 锚定 fail-closed(承 exp8 P1-2/C5 同判据):缺 listing/缺 list_date/上市日前
历史 bar/上市区间异常 → 该票候选事件全部剔除留痕,不猜不补。

依赖:仅标准库。输入行 = dict{trade_date: date, limit_status: str, open_limit_status: str,
board: str, is_st: bool};消费方(driver)负责 PriceRow → dict 映射与按票分组;
本模块单票处理,跨票聚合在调用方(merge_selections)。
"""
from __future__ import annotations

import datetime as dt

# ── 冻结 PAP 参数(digest 583c4c94…0c42;口径唯一,禁散落魔法数)────────────────────
N_MIN = 2                                      # 冻结值:准入下限(终版收口令二.2)
ONE_WORD = "one_word"                          # 视图 limit_status 一字值(不分方向)
OPEN_AT_DOWN = "open_at_down_limit"            # 视图 open_limit_status 开盘跌停位(链成员)
OPEN_AT_UP = "open_at_up_limit"                # 开盘涨停位(reversal_hijack 判据)
EVENT_DATE_START = dt.date(2007, 1, 1)         # 研究期下界(含;令四.1)
EVENT_DATE_END = dt.date(2024, 7, 1)           # 上界(不含;==holdout 焊死线)
RECENT_LISTING_MAX_AGE = 30                    # 链起点上市交易龄 ≤30 → recent_listing(令四.4)

# 主漏斗互斥主原因(令七.4 固定顺序;reason 值同为 rejects 留痕键)
REASON_RIGHT_CENSORED = "right_censored_no_event_day"
REASON_PRE2007 = "out_of_period_pre2007"
REASON_POST = "out_of_period_post"
REASON_DUPLICATE = "duplicate_event_date_mapping"
REASON_HIJACK = "reversal_hijack"
LISTING_REASONS = ("listing_missing_fail_closed", "pre_listing_bar_fail_closed",
                   "listing_window_anomaly_fail_closed")


def is_one_word_down(row: dict) -> bool:
    """链成员判据(冻结 event_def,双条件缺一不可)。"""
    return (row.get("limit_status") == ONE_WORD
            and row.get("open_limit_status") == OPEN_AT_DOWN)


def is_one_word(row: dict) -> bool:
    """事件日顺延判据:任何一字(含反向一字涨停/开盘位异常者)均不可为事件日。"""
    return row.get("limit_status") == ONE_WORD


def detect_member_runs(rows: list[dict]) -> list[tuple[int, int]]:
    """单票成员行极大连续段 [(i,j)](行序;含 len1 段,N_MIN 过滤在漏斗内)。

    极大段构造 → 结构上不可能重复截取子链(冻结值 N_MIN=2 在 run_funnel 处唯一把关)。
    """
    runs: list[tuple[int, int]] = []
    i, n = 0, len(rows)
    while i < n:
        if not is_one_word_down(rows[i]):
            i += 1
            continue
        j = i
        while j + 1 < n and is_one_word_down(rows[j + 1]):
            j += 1
        runs.append((i, j))
        i = j + 1
    return runs


def split_runs_by_calendar(rows: list[dict], runs: list[tuple[int, int]],
                           cal_index: dict) -> list[tuple[int, int]]:
    """B 口径(交易所日历连续,令一.4;仅 NFV 诊断):A 成员段按日历相邻切分。

    cal_index = {trade_date: 日历轴序号};段内相邻两行若非日历相邻(缺号/不在轴)则断开。
    """
    out: list[tuple[int, int]] = []
    for (i, j) in runs:
        s = i
        for k in range(i, j):
            i1 = cal_index.get(rows[k]["trade_date"])
            i2 = cal_index.get(rows[k + 1]["trade_date"])
            if i1 is None or i2 is None or i2 - i1 != 1:
                out.append((s, k))
                s = k + 1
        out.append((s, j))
    return out


def resolve_event_day(rows: list[dict], end_i: int) -> tuple[int | None, int, int, int]:
    """链尾后顺延扫描:返回 (事件行索引|None, 顺延一字涨停行数, 一字跌停行数, 开盘位异常行数)。

    从 end_i+1 起找首个 limit_status != 'one_word' 的真实交易行;中途一字行按
    open_limit_status 分计(up 计数 ≥1 即构成 reversal_hijack 判据);到数据边界仍无
    → (None, …)=右删失。
    """
    k, n = end_i + 1, len(rows)
    up = down = anom = 0
    while k < n and is_one_word(rows[k]):
        ols = rows[k].get("open_limit_status")
        if ols == OPEN_AT_UP:
            up += 1
        elif ols == OPEN_AT_DOWN:
            down += 1
        else:
            anom += 1
        k += 1
    return (None if k >= n else k), up, down, anom


def _listing_anomaly(rows: list[dict], listing: dict | None) -> str | None:
    """listing 锚定核验(fail-closed,承 exp8 P1-2/C5 同判据):异常 → 剔除 reason,健康 → None。
    三类:①缺 listing/缺 list_date ②上市日前历史 bar ③上市区间异常(delist≤list 或
    bar 落在退市日当日及之后)。"""
    if listing is None or listing.get("list_date") is None:
        return "listing_missing_fail_closed"
    ld, dd = listing["list_date"], listing.get("delist_date")
    if rows and rows[0]["trade_date"] < ld:
        return "pre_listing_bar_fail_closed"
    if dd is not None and (dd <= ld or (rows and rows[-1]["trade_date"] >= dd)):
        return "listing_window_anomaly_fail_closed"
    return None


def run_funnel(ts_code: str, rows: list[dict], runs: list[tuple[int, int]],
               listing_reason: str | None) -> dict:
    """一条口径的完整主漏斗(令七.4 固定顺序,互斥主原因)。

    runs = 成员极大段(含 len1;此处唯一施加 N_MIN 冻结值)。
    返回 {"events": [...], "rejects": [...], "counters": {...}}:
    events/rejects 记录携带链全量几何(chain_*/start_rank/recent_listing/deferred_*/
    board·is_st 链起点与事件日双值);确定性 = 输入行序唯一决定输出(纯函数,双跑同)。
    """
    g = {"runs_len1_not_chain": 0, "chains_total": 0,
         "deferred_rows_up": 0, "deferred_rows_down": 0, "deferred_rows_anom": 0,
         REASON_RIGHT_CENSORED: 0, "reversal_hijack_observed_before_censoring": 0,
         REASON_PRE2007: 0, REASON_POST: 0,
         "listing_anomaly": 0,
         "duplicate_event_days": 0, "duplicate_chains_dropped": 0,
         REASON_HIJACK: 0, "final_main_events": 0,
         "st_flag_chain_vs_eventday_diff": 0}
    events: list[dict] = []
    rejects: list[dict] = []
    survivors: list[dict] = []
    for (i, j) in runs:
        if j - i + 1 < N_MIN:
            g["runs_len1_not_chain"] += 1          # len1 段不成链(N_MIN=2 冻结值)
            continue
        g["chains_total"] += 1
        ev_i, up, down, anom = resolve_event_day(rows, j)
        g["deferred_rows_up"] += up
        g["deferred_rows_down"] += down
        g["deferred_rows_anom"] += anom
        rec = {"ts_code": ts_code,
               "chain_start_date": rows[i]["trade_date"].isoformat(),
               "chain_end_date": rows[j]["trade_date"].isoformat(),
               "chain_len": j - i + 1, "chain_start_rank": i + 1,
               "recent_listing": (i + 1) <= RECENT_LISTING_MAX_AGE,
               "deferred_up": up, "deferred_down": down, "deferred_anom": anom,
               "board_chain": rows[i].get("board"), "is_st_chain": rows[i].get("is_st")}
        # ① 右删失(互斥主原因第一档;补充令1:hijack 观察仅正交 audit 标志,不进 hijack 数)
        if ev_i is None:
            g[REASON_RIGHT_CENSORED] += 1
            if up >= 1:
                g["reversal_hijack_observed_before_censoring"] += 1
                rejects.append(dict(rec, reason=REASON_RIGHT_CENSORED,
                                    reversal_hijack_observed_before_censoring=True))
            else:
                rejects.append(dict(rec, reason=REASON_RIGHT_CENSORED))
            continue
        ev = rows[ev_i]
        rec.update(event_date=ev["trade_date"].isoformat(),
                   evday_status=ev.get("limit_status"),
                   evday_open_status=ev.get("open_limit_status"),
                   board_event=ev.get("board"), is_st_event=ev.get("is_st"))
        # ② 研究期外
        if ev["trade_date"] < EVENT_DATE_START:
            g[REASON_PRE2007] += 1
            rejects.append(dict(rec, reason=REASON_PRE2007))
            continue
        if ev["trade_date"] >= EVENT_DATE_END:
            g[REASON_POST] += 1
            rejects.append(dict(rec, reason=REASON_POST))
            continue
        # ③ listing 异常(票级三类 fail-closed,不猜不补)
        if listing_reason is not None:
            g["listing_anomaly"] += 1
            g["listing_anomaly_" + listing_reason] = \
                g.get("listing_anomaly_" + listing_reason, 0) + 1
            rejects.append(dict(rec, reason=listing_reason))
            continue
        survivors.append(rec)
    # ④ duplicate mapping((ts_code,event_date) 全剔逐条留痕,不合并不择一;令一.5)
    by_date: dict[str, list[dict]] = {}
    for rec in survivors:
        by_date.setdefault(rec["event_date"], []).append(rec)
    for date_key in sorted(by_date):
        grp = by_date[date_key]
        if len(grp) > 1:
            g["duplicate_event_days"] += 1
            g["duplicate_chains_dropped"] += len(grp)
            for rec in grp:
                rejects.append(dict(rec, reason=REASON_DUPLICATE,
                                    n_chains_colliding=len(grp)))
            continue
        rec = grp[0]
        # ⑤ reversal_hijack(令二:不入主事件集,逐条 audit,全 NFV)
        if rec["deferred_up"] >= 1:
            g[REASON_HIJACK] += 1
            rejects.append(dict(rec, reason=REASON_HIJACK))
            continue
        # ⑥ 最终主事件集(真开板保留:evday_open_status 不作剔除条件,令二.5)
        g["final_main_events"] += 1
        if rec["is_st_event"] != rec["is_st_chain"]:
            g["st_flag_chain_vs_eventday_diff"] += 1     # 令三.3:单独计数,记录留痕
            rec = dict(rec, st_flag_chain_vs_eventday_diff=True)
        events.append(rec)
    return {"events": events, "rejects": rejects, "counters": g}


def select_limit_down_events(ts_code: str, rows: list[dict],
                             listing: dict | None = None,
                             cal_index: dict | None = None) -> dict:
    """单票事件识别全流水线:listing 锚定核验 → 成员段检测 → A 主漏斗(令七.4)
    → B 口径 NFV 镜像(cal_index 提供时)。

    rows = 该票真实交易行按 trade_date 升序(调用方保证排序);
    listing = {"list_date": date|None, "delist_date": date|None};
    cal_index = {trade_date: 日历轴序号}(None → 不产 b_control,零新键)。
    返回 {"events","rejects","counters","b_control"};b_control 全块 NOT_FOR_VERDICT,
    不改变主事件集(令一.4)。确定性 = 输入唯一决定输出(纯函数,双跑同)。
    """
    listing_reason = _listing_anomaly(rows, listing)
    runs = detect_member_runs(rows)
    sel = run_funnel(ts_code, rows, runs, listing_reason)
    sel["counters"]["input_rows"] = len(rows)
    sel["counters"]["member_rows"] = sum(1 for r in rows if is_one_word_down(r))
    sel["counters"]["listing_anomaly_securities"] = (
        1 if (listing_reason is not None and rows) else 0)
    if cal_index is not None:
        b = run_funnel(ts_code, rows, split_runs_by_calendar(rows, runs, cal_index),
                       listing_reason)
        b["not_for_verdict"] = True
        sel["b_control"] = b
    else:
        sel["b_control"] = None
    return sel


def merge_selections(per_security: list[dict]) -> dict:
    """跨票聚合(调用方逐票流式喂 select_limit_down_events 结果):
    events/rejects 全量拼接(票内已按事件日序,票间按调用方喂入序=ts_code 序);
    counters 逐键求和 + reject_reasons 计数;b_control 同构聚合(全部票须同开同关)。
    纯函数,不排序不改行。"""
    events, rejects = [], []
    counters: dict = {}
    b_events, b_rejects = [], []
    b_counters: dict = {}
    has_b = None
    for sel in per_security:
        events.extend(sel["events"])
        rejects.extend(sel["rejects"])
        for k, v in sel["counters"].items():
            counters[k] = counters.get(k, 0) + v
        b = sel.get("b_control")
        if has_b is None:
            has_b = b is not None
        elif has_b != (b is not None):
            raise ValueError("b_control 开关跨票不一致(cal_index 必须全体同传或全体不传)")
        if b is not None:
            b_events.extend(b["events"])
            b_rejects.extend(b["rejects"])
            for k, v in b["counters"].items():
                b_counters[k] = b_counters.get(k, 0) + v
    reasons: dict = {}
    for r in rejects:
        reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    out = {"events": events, "rejects": rejects, "counters": counters,
           "reject_reasons": reasons}
    out["b_control"] = ({"not_for_verdict": True, "events": b_events,
                         "rejects": b_rejects, "counters": b_counters}
                        if has_b else None)
    return out
