"""exp17 A1/B1/C1 冻结事件规则攻击 fixture；纯函数、零 I/O。"""
from __future__ import annotations

import datetime as dt
import random
import sys

from taosha.compute.earnings_flash_gap_rules import select_events


FAIL = 0
N = 0
D = dt.date
END = D(2020, 12, 31)
EVENT = D(2021, 4, 20)
PRIOR = D(2021, 4, 1)


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    FAIL += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


def express(code, income, *, ann=EVENT, end=END, flag="0"):
    return {"ts_code": code, "ann_date": ann, "end_date": end,
            "n_income": income, "update_flag": flag}


def forecast(code, lower, upper, *, ann=PRIOR, end=END):
    return {"ts_code": code, "ann_date": ann, "end_date": end,
            "net_profit_min": lower, "net_profit_max": upper}


express_rows = [
    express("UP.SZ", 1_200_000),
    express("DOWN.SZ", -1_200_000),
    express("INSIDE.SZ", 900_000),
    express("BOUNDARY.SZ", 1_000_000),
    express("LATEST.SZ", 1_200_000),
    express("SAME.SZ", 1_200_000),
    express("ORPHAN.SZ", 1_200_000),
    express("INCOMPLETE.SZ", 1_200_000),
    express("CONFLICT.SZ", 1_200_000),
    express("ACTNULL.SZ", None),
    express("B1MULTI.SZ", 1_200_000),
    express("B1MULTI.SZ", 1_300_000),
    express("B1MISS.SZ", 1_200_000, flag="1"),
    # 同票同事件日两报告期同向，必须整组剔除。
    express("DUP.SZ", 1_200_000, end=D(2020, 6, 30)),
    express("DUP.SZ", 1_200_000, end=D(2020, 9, 30)),
    # 同票同事件日两报告期反向，必须整组剔除并记方向冲突。
    express("DIRCON.SZ", 1_200_000, end=D(2020, 6, 30)),
    express("DIRCON.SZ", -1_200_000, end=D(2020, 9, 30)),
    express("PRE2011.SZ", 1_200_000, ann=D(2010, 4, 20)),
]

forecast_rows = [
    forecast("UP.SZ", 80, 100),
    forecast("DOWN.SZ", -100, -80),
    forecast("INSIDE.SZ", 80, 100),
    forecast("BOUNDARY.SZ", 80, 100),
    # A1 必须取最近严格前置版本；较早版本若被错取会得到 inside。
    forecast("LATEST.SZ", 100, 130, ann=D(2021, 3, 1)),
    forecast("LATEST.SZ", 80, 100, ann=D(2021, 4, 10)),
    forecast("SAME.SZ", 80, 100, ann=EVENT),
    forecast("INCOMPLETE.SZ", None, 100),
    forecast("CONFLICT.SZ", 80, 100),
    forecast("CONFLICT.SZ", 90, 110),
    forecast("ACTNULL.SZ", 80, 100),
    forecast("B1MULTI.SZ", 80, 100),
    forecast("B1MISS.SZ", 80, 100),
    forecast("DUP.SZ", 80, 100, end=D(2020, 6, 30)),
    forecast("DUP.SZ", 80, 100, end=D(2020, 9, 30)),
    forecast("DIRCON.SZ", 80, 100, end=D(2020, 6, 30)),
    forecast("DIRCON.SZ", -100, -80, end=D(2020, 9, 30)),
]

s = select_events(express_rows, forecast_rows)
c = s["counters"]
by_code = {row["ts_code"]: row for row in s["events"]}

check("F1 Decimal严格up/down且负值方向正确",
      (by_code["UP.SZ"]["direction"], by_code["DOWN.SZ"]["direction"]),
      ("up", "down"))
check("F2 闭区间inside与恰等boundary均不成事件",
      (c["inside"], c["boundary"], "INSIDE.SZ" in by_code,
       "BOUNDARY.SZ" in by_code), (1, 1, False, False))
check("F3 A1取最近严格前置完整预告",
      (by_code["LATEST.SZ"]["forecast_ann_date"], by_code["LATEST.SZ"]["direction"]),
      (D(2021, 4, 10), "up"))
check("F4 同日预告不算严格前置",
      (c["same_day_forecast_groups"], c["no_strict_prior"]), (1, 1))
check("F5 孤儿与区间不完整分开留痕", (c["orphan"], c["no_complete_prior"]), (1, 1))
check("F6 A1最近日不同区间整组拒绝", c["forecast_conflict"], 1)
check("F7 B1 flag0多条与缺失均整组拒绝",
      (c["flag0_multiple_groups"], c["flag0_missing_groups"], c["b1_rejected_groups"]),
      (1, 1, 2))
check("F8 actual空值留痕不回退代理", c["actual_null"], 1)
check("F9 重复事件键全组剔除",
      (c["event_key_duplicate_groups"], c["event_key_duplicate_rows_dropped"],
       "DUP.SZ" in by_code), (2, 4, False))
check("F10 方向冲突属于重复组子集", c["direction_conflict_groups"], 1)
check("F11 研究期外快报不进入组", c["study_express_rows"], len(express_rows) - 1)
check("F12 三条恒等式均成立",
      (s["classification_identity_ok"], s["event_identity_ok"],
       s["yearly_identity_ok"]), (True, True, True))

shuffled_express = list(express_rows)
shuffled_forecast = list(forecast_rows)
random.Random(17).shuffle(shuffled_express)
random.Random(18).shuffle(shuffled_forecast)
s2 = select_events(shuffled_express, shuffled_forecast)
check("F13 输入乱序不改变事件与selection SHA",
      (s2["events"], s2["selection_sha256"]), (s["events"], s["selection_sha256"]))

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
