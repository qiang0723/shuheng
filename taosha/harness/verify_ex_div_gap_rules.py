"""exp14 A1/B1/C1/D1 冻结前数据对账规则攻击 fixture；纯函数、零 I/O。"""
from __future__ import annotations

import datetime as dt
import random
import sys

from taosha.compute.ex_div_gap_rules import (
    prepare_events, required_factor_keys, select_events,
)


FAIL = 0
N = 0
D = dt.date
EX = D(2021, 4, 20)
PREV = D(2021, 4, 19)
OPEN_DATES = [PREV, EX, D(2021, 4, 21), D(2021, 4, 22),
              D(2021, 4, 23), D(2021, 4, 26), D(2021, 4, 27)]


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    FAIL += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


def row(code, total="0.5", *, end=D(2020, 12, 31), bonus="0.2", capital="0.3",
        record=D(2021, 4, 19), imp=D(2021, 4, 1), stage="实施"):
    return {"ts_code": code, "end_date": end, "ann_date": imp, "div_proc": stage,
            "stk_div": total, "stk_bo_rate": bonus, "stk_co_rate": capital,
            "record_date": record, "ex_date": EX, "imp_ann_date": imp,
            "update_flag": "0", "snapshot_batch": "batch17"}


rows = [
    row("GOOD.SZ"), row("POST.SZ", "0.6", bonus="0.1", capital="0.5"),
    row("NOBAR.SZ", "0.7", bonus=None, capital="0.7"),
    row("SINGLENULL.SZ", record=None), row("STATIC.SZ"), row("MISSFACTOR.SZ"),
    row("BELOW.SZ", "0.4", bonus="0.1", capital="0.3"),
    row("TIMING.SZ", imp=EX), row("BADCOMP.SZ", "0.5", bonus="0.1", capital="0.3"),
    row("REQUIRED.SZ", total=None), row("NONIMPL.SZ", stage="预案"),
]
rows.extend([row("MULTIOK.SZ"), row("MULTIOK.SZ")])
rows.extend([row("MULTINULL.SZ", record=None), row("MULTINULL.SZ", record=None)])
rows.extend([row("MULTICONFLICT.SZ"),
             row("MULTICONFLICT.SZ", "0.6", bonus="0.3", capital="0.3")])
rows.extend([row("DUP.SZ", end=D(2020, 6, 30)), row("DUP.SZ", end=D(2020, 9, 30))])

factor_rows = []
for code in ("GOOD.SZ", "POST.SZ", "NOBAR.SZ", "SINGLENULL.SZ", "MULTIOK.SZ"):
    factor_rows.extend([
        {"ts_code": code, "trade_date": PREV, "adj_factor": "1"},
        {"ts_code": code, "trade_date": EX, "adj_factor": "2"},
    ])
factor_rows.extend([
    {"ts_code": "STATIC.SZ", "trade_date": PREV, "adj_factor": "1"},
    {"ts_code": "STATIC.SZ", "trade_date": EX, "adj_factor": "1"},
    {"ts_code": "MISSFACTOR.SZ", "trade_date": PREV, "adj_factor": "1"},
])

s = select_events(rows, factor_rows, OPEN_DATES)
c = s["counters"]
codes = {event["ts_code"] for event in s["events"]}

check("F1 研究窗实施行与组数", (c["implementation_rows"], c["implementation_groups"]),
      (18, 15))
check("F2 单行NULL record_date不触B1折叠门", "SINGLENULL.SZ" in codes, True)
check("F3 B1六字段全非NULL且一致才折叠", c["group_qualified"], 10)
check("F4 B1多行NULL整组拒", c["group_multi_null"], 1)
check("F5 B1多行冲突整组拒", c["group_multi_conflict"], 1)
check("F6 时序/分项/必需字段三类分计",
      (c["group_timing_invalid"], c["group_component_invalid"],
       c["group_required_invalid"]), (1, 1, 1))
check("F7 Decimal恰等入选且低于阈值单列",
      (c["threshold_groups"], c["threshold_exact_boundary_groups"],
       c["below_threshold_groups"]), (9, 7, 1))
check("F8 重复事件键整键剔除",
      (c["event_key_duplicate_groups"], c["event_key_duplicate_rows_dropped"],
       c["pre_factor_candidates"]), (1, 2, 7))
check("F9 A1因子变化/静态/缺失互斥",
      (c["factor_factor_changed"], c["factor_factor_static"],
       c["factor_current_missing"]), (5, 1, 1))
check("F10 A1最终事件与恰等", (c["final_events"], c["final_exact_boundary"]), (5, 3))
check("F11 逐年与监管组成守恒", (s["events_yearly"], s["regulatory_composition"]),
      ({"2021": 5}, {"exchange_rule_period": 5}))
check("F12 全部漏斗恒等式", set(s["identities"].values()), {True})

prepared = prepare_events(rows)
wanted = required_factor_keys(prepared, OPEN_DATES)
check("F13 因子最小请求键", len(wanted), 14)

shuffled_rows, shuffled_factors = list(rows), list(factor_rows)
random.Random(14).shuffle(shuffled_rows)
random.Random(15).shuffle(shuffled_factors)
s2 = select_events(shuffled_rows, shuffled_factors, list(reversed(OPEN_DATES)))
check("F14 输入乱序不改变事件与selection SHA",
      (s2["events"], s2["selection_sha256"]), (s["events"], s["selection_sha256"]))

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
