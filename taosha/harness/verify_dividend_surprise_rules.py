"""exp19 A1/B2-P1/C1/D1/E1 冻结事件规则攻击 fixture；纯函数、零 I/O。"""
from __future__ import annotations

import datetime as dt
import random
import sys

from taosha.compute.dividend_surprise_rules import select_events


FAIL = 0
N = 0
D = dt.date
EVENT = D(2021, 4, 20)


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    FAIL += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


def row(code, year, value, *, ann=None, stage="预案", flag="0"):
    ann = ann or D(year + 1, 4, 20)
    return {"ts_code": code, "end_date": D(year, 12, 31), "ann_date": ann,
            "div_proc": stage, "cash_div_tax": value, "base_date": None,
            "base_share": None, "update_flag": flag}


rows = []
for code, prior, current in (
    ("UP.SZ", "1", "1.5"), ("DOWN.SZ", "1", "0.5"),
    ("INSIDE.SZ", "1", "1.49"), ("ZERO.SZ", "1", "0"),
):
    rows.extend([row(code, 2019, prior, ann=D(2020, 4, 20)),
                 row(code, 2020, current)])
rows.extend([
    row("PRIORZERO.SZ", 2019, "0", ann=D(2020, 4, 20)),
    row("PRIORZERO.SZ", 2020, "1"),
    row("MISSING.SZ", 2020, "1"),
    row("UNRES.SZ", 2019, "1", ann=D(2020, 4, 20), flag="1"),
    row("UNRES.SZ", 2020, "2"),
    row("NONADJ.SZ", 2018, "1", ann=D(2019, 4, 20)),
    row("NONADJ.SZ", 2020, "2"),
    row("NOBACKFILL.SZ", 2019, "1", ann=D(2020, 4, 20), stage="实施"),
    row("NOBACKFILL.SZ", 2020, "2"),
    row("MULTI.SZ", 2020, "1"), row("MULTI.SZ", 2020, "2"),
    row("PREPERIOD.SZ", 2018, "1", ann=D(2019, 4, 20)),
    row("PREPERIOD.SZ", 2019, "2", ann=D(2020, 4, 20)),
])
# 同票两个相邻财年在同一公告日形成事件，必须按事件键整组剔除。
rows.extend([row("DUP.SZ", 2018, "1", ann=D(2020, 4, 20)),
             row("DUP.SZ", 2019, "2", ann=EVENT),
             row("DUP.SZ", 2020, "4", ann=EVENT)])
# 同型但方向相反，方向冲突是重复键的子集。
rows.extend([row("DIRCON.SZ", 2018, "1", ann=D(2020, 4, 20)),
             row("DIRCON.SZ", 2019, "2", ann=EVENT),
             row("DIRCON.SZ", 2020, "1", ann=EVENT)])

s = select_events(rows)
c = s["counters"]
study = c["research_classification"]
by_code = {event["ts_code"]: event for event in s["events"]}

check("F1 D1恰等+50%/-50%进入up/down",
      (by_code["UP.SZ"]["direction"], by_code["DOWN.SZ"]["direction"],
       c["research_exact_boundary"]), ("up", "down", 3))
check("F2 current=0且prior>0按-100%进入down",
      (by_code["ZERO.SZ"]["direction"], by_code["ZERO.SZ"]["change"]),
      ("down", -1))
check("F3 inside不进事件", (study["inside"], "INSIDE.SZ" in by_code), (1, False))
check("F4 prior=0单列zero_undefined", study["zero_undefined"], 1)
check("F5 上年无组与非相邻记录均为missing_prior", study["missing_prior"], 2)
check("F6 上年组存在但E1不合格为unresolvable_prior",
      study["unresolvable_prior"], 2)
check("F7 E1多初始行整组剔除且不入研究分类",
      c["initial_multiple_conflict_groups"], 1)
check("F8 后续阶段值不回填",
      (c["later_value_without_initial_groups"], c["implementation_backfill_hits"]), (1, 0))
check("F9 B2-P1前的当前公告不进研究事件", "PREPERIOD.SZ" in by_code, False)
check("F10 重复事件键整组剔除",
      (c["event_key_duplicate_groups"], c["event_key_duplicate_rows_dropped"],
       "DUP.SZ" in by_code), (2, 4, False))
check("F11 方向冲突属于重复键子集", c["direction_conflict_groups"], 1)
check("F12 五条恒等式全成立", s["identities"],
      {"group": True, "full_classification": True, "research_classification": True,
       "event": True, "direction": True})

shuffled = list(rows)
random.Random(19).shuffle(shuffled)
s2 = select_events(shuffled)
check("F13 输入乱序不改变事件与selection SHA",
      (s2["events"], s2["selection_sha256"]), (s["events"], s["selection_sha256"]))

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
