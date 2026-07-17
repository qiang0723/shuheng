"""淘沙 · exp8 limit_open 一字涨停链事件识别(纯函数,零 I/O)。
口径出处 = 人冻结前裁决 2026-07-17(taosha/docs/limit-open-prefreeze-rulings-2026-07-17.md,原文即口径)。
职责边界 = 只做事件识别(链检测→事件日顺延→范围→唯一性 fail-closed);不读收益、不判显著、不碰台账。

裁决一(事件定义)转录:
  · N=2:连续至少 2 个一字涨停交易日(链成员唯一判据 = limit_status='one_word'
    AND open_limit_status='open_at_up_limit',裁决一.2 双条件;视图 'one_word' 不分方向,
    方向由 open_limit_status 定)。
  · 连续性 = 个股自身真实交易行序连续:输入行 = 该票真实交易行(prices 视图行)按
    trade_date 升序;停牌缺 bar 不出现在行序 → 天然不计交易日、不重置链;
    行序相邻但非一字涨停的真实 bar = 链断点(禁跨拼接)。
  · 每段取最大饱和链(行序上连续一字涨停的极大段),不重复截取子链。
  · 事件日 = 链后首个 limit_status != 'one_word' 的真实交易行(链后一字跌停仍属
    一字不可交易状态 → 继续顺延;停牌日无行 → 结构上不可能成为事件日);
    顺延至数据边界仍无 → 该链无事件(right_censored,剔除留痕)。
  · 每个 (ts_code, event_date) 只能有一个事件;重复映射 fail-closed:涉事链全部
    不进事件集,逐条上报(不猜、不合并;操作化待人核,见 PAP 草案复核点)。

裁决二(样本范围)转录:2007-01-01 ≤ event_date < 2024-07-01(右界与 holdout 焊死线重合,
此处再挡一道);recent_listing = 链起点上市交易龄 ≤30(草案操作化 = 链起点行在该票自身
真实交易行序中的序号,上市首个 bar = 第 1 行;仅作标记,不改事件集,待人核)。

依赖:仅标准库。输入行 = dict{trade_date: date, limit_status: str, open_limit_status: str};
消费方(driver)负责 PriceRow → dict 映射与按票分组;本模块单票处理,跨票聚合在调用方。
"""
from __future__ import annotations

import datetime as dt

# ── 冻结前裁决参数(人裁 2026-07-17;口径唯一,禁散落魔法数)────────────────────
N_MIN = 2                                      # 裁决一.1:连续至少 2 个一字涨停交易日
ONE_WORD = "one_word"                          # 视图 limit_status 一字值(不分方向)
OPEN_AT_UP = "open_at_up_limit"                # 视图 open_limit_status 开盘涨停位
EVENT_DATE_START = dt.date(2007, 1, 1)         # 裁决二.1:研究事件日下界(含)
EVENT_DATE_END = dt.date(2024, 7, 1)           # 裁决二.1:上界(不含;==holdout 焊死线)
RECENT_LISTING_MAX_AGE = 30                    # 裁决二.5:链起点上市交易龄 ≤30 → recent_listing
LIMIT_REGIME_START = dt.date(1996, 12, 16)     # 涨跌停制度起始(诊断计数用,非剔除规则)


def is_one_word_up(row: dict) -> bool:
    """链成员判据(裁决一.2,双条件缺一不可)。"""
    return (row.get("limit_status") == ONE_WORD
            and row.get("open_limit_status") == OPEN_AT_UP)


def is_one_word(row: dict) -> bool:
    """事件日顺延判据(裁决一.5):任何一字(含一字跌停/开盘位异常者)均不可为事件日。"""
    return row.get("limit_status") == ONE_WORD


def detect_chains(rows: list[dict]) -> list[dict]:
    """单票最大饱和链检测(裁决一.3/一.4)。

    rows = 该票真实交易行按 trade_date 升序(行序即自身交易行序;调用方保证排序)。
    返回链列表:{start_i, end_i, length, start_date, end_date, start_rank}
    (start_rank = 链起点行序号,首行=1,上市交易龄草案操作化);只收 length>=N_MIN,
    极大段构造 → 结构上不可能重复截取子链。
    """
    chains: list[dict] = []
    i, n = 0, len(rows)
    while i < n:
        if not is_one_word_up(rows[i]):
            i += 1
            continue
        j = i
        while j + 1 < n and is_one_word_up(rows[j + 1]):
            j += 1
        if j - i + 1 >= N_MIN:
            chains.append({"start_i": i, "end_i": j, "length": j - i + 1,
                           "start_date": rows[i]["trade_date"],
                           "end_date": rows[j]["trade_date"],
                           "start_rank": i + 1})
        i = j + 1
    return chains


def resolve_event_day(rows: list[dict], end_i: int) -> tuple[int | None, int]:
    """链后事件日顺延(裁决一.5):返回 (事件行索引 | None, 顺延跳过的一字行数)。

    从 end_i+1 起找首个 limit_status != 'one_word' 的真实交易行;中途一字行
    (含一字跌停、后续一字涨停)全部顺延;到数据边界仍无 → (None, 跳过数)。
    """
    k, skipped = end_i + 1, 0
    n = len(rows)
    while k < n:
        if not is_one_word(rows[k]):
            return k, skipped
        skipped += 1
        k += 1
    return None, skipped


def select_limit_open_events(ts_code: str, rows: list[dict]) -> dict:
    """单票事件识别全流水线:链检测 → 事件日顺延 → 范围过滤 → 唯一性 fail-closed。

    返回 {"events": [...], "rejects": [...], "counters": {...}}——全量留痕供 audit;
    events 已按 event_date 升序;确定性 = 输入行序唯一决定输出(纯函数,双跑同)。
    事件字段含 chain_* 全量几何 + recent_listing 草案标记(不改事件集,裁决二.5)。
    """
    counters = {"input_rows": len(rows),
                "one_word_up_rows": sum(1 for r in rows if is_one_word_up(r)),
                "chains_ge_n": 0, "events": 0,
                "deferred_rows_total": 0,
                "chains_pre_regime": 0}
    chains = detect_chains(rows)
    counters["chains_ge_n"] = len(chains)
    counters["chains_pre_regime"] = sum(
        1 for c in chains if c["start_date"] < LIMIT_REGIME_START)

    candidates, rejects = [], []
    for c in chains:
        ev_i, skipped = resolve_event_day(rows, c["end_i"])
        counters["deferred_rows_total"] += skipped
        base = {"ts_code": ts_code, "chain_start_date": c["start_date"].isoformat(),
                "chain_end_date": c["end_date"].isoformat(), "chain_len": c["length"],
                "chain_start_rank": c["start_rank"],
                "recent_listing": c["start_rank"] <= RECENT_LISTING_MAX_AGE,
                "deferred_one_word_rows": skipped}
        if ev_i is None:
            rejects.append(dict(base, reason="right_censored_no_event_day"))
            continue
        ev_date = rows[ev_i]["trade_date"]
        if not (EVENT_DATE_START <= ev_date < EVENT_DATE_END):
            rejects.append(dict(base, reason="event_date_out_of_study_range",
                                event_date=ev_date.isoformat()))
            continue
        candidates.append(dict(base, event_date=ev_date.isoformat()))

    # 唯一性(裁决一.6):同 (ts_code,event_date) 多链 → 全部 fail-closed 剔除并上报
    by_date: dict[str, list[dict]] = {}
    for e in candidates:
        by_date.setdefault(e["event_date"], []).append(e)
    events = []
    for date_key in sorted(by_date):
        group = by_date[date_key]
        if len(group) == 1:
            events.append(group[0])
        else:
            for e in group:
                rejects.append(dict(e, reason="duplicate_event_date_mapping",
                                    n_chains_colliding=len(group)))
    counters["events"] = len(events)
    return {"events": events, "rejects": rejects, "counters": counters}


def merge_selections(per_security: list[dict]) -> dict:
    """跨票聚合(调用方逐票流式喂 select_limit_open_events 结果):
    events 全量拼接(票内已升序,票间按 ts_code 序=调用方喂入序);rejects 同;
    counters 逐键求和 + reject_reasons 计数。纯函数,不排序不改行。"""
    events, rejects = [], []
    counters: dict = {}
    for sel in per_security:
        events.extend(sel["events"])
        rejects.extend(sel["rejects"])
        for k, v in sel["counters"].items():
            counters[k] = counters.get(k, 0) + v
    reasons: dict = {}
    for r in rejects:
        reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    return {"events": events, "rejects": rejects, "counters": counters,
            "reject_reasons": reasons}
