"""exp568 普通→ST事件规则攻击 fixture（纯函数、零数据库）。"""
from __future__ import annotations

import datetime as dt
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.compute.st_imposition_rules import (  # noqa: E402
    composition_identity_ok,
    funnel_identity_ok,
    merge_selections,
    run_funnel,
    select_st_imposition_events,
)

FAIL = 0
N = 0


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    FAIL += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


def row(alias, start, ann):
    return {
        "alias": alias,
        "start_date": dt.date.fromisoformat(start) if start else None,
        "ann_date": dt.date.fromisoformat(ann) if ann else None,
    }


def pair(before="甲股份", after="*ST甲", ann="2020-04-29", start="2020-04-30",
         before_start="2018-01-01"):
    return [row(before, before_start, "2010-01-01"), row(after, start, ann)]


# 目标事件及组成审计
starred = run_funnel("000001.SZ", pair())
plain = run_funnel("000002.SZ", pair(after="ST乙"))
check("普通→带星ST入事件", (starred["counters"]["final_events"],
                            starred["events"][0]["st_variant"]), (1, "starred"))
check("普通→不带星ST入事件", (plain["counters"]["final_events"],
                              plain["events"][0]["st_variant"]), (1, "plain_st"))

# 非目标转换全部排除
non_targets = [
    pair(before="ST甲", after="*ST甲"),
    pair(before="*ST甲", after="甲股份"),
    pair(before="甲股份", after="退市甲"),
    pair(before="退市甲", after="*ST甲"),
]
check("ST→ST/ST→普通/普通→退市/退市→ST均非事件",
      [run_funnel(f"x{i}", rows)["counters"]["final_events"]
       for i, rows in enumerate(non_targets)], [0, 0, 0, 0])

# 状态与锚 fail-closed
mixed = [row("甲股份", "2018-01-01", "2017-12-29"),
         row("*ST甲", "2020-04-30", "2020-04-29"),
         row("甲科技", "2020-04-30", "2020-04-29")]
selection = run_funnel("000003.SZ", mixed)
check("孪生段ST/普通混名 fail-closed",
      (selection["counters"]["state_unjudgeable_fail_closed"],
       selection["counters"]["final_events"]), (1, 0))

for label, rows, reason in [
    ("锚缺失", pair(ann=None), "anchor_missing"),
    ("ann>start", pair(ann="2020-05-01"), "ann_after_start_fail_closed"),
    ("研究期外", pair(ann="2010-04-29"), "out_of_period"),
]:
    selection = run_funnel("000004.SZ", rows)
    check(f"{label} fail-closed", (selection["counters"][reason],
                                  selection["counters"]["final_events"]), (1, 0))

conflict = pair() + [row("*ST甲", "2020-04-30", "2020-04-28")]
selection = run_funnel("000005.SZ", conflict)
check("段内ann冲突 fail-closed", (selection["counters"]["anchor_conflict_fail_closed"],
                                  selection["counters"]["final_events"]), (1, 0))

# 研究期边界
for ann, start, expected in (("2011-01-01", "2011-01-04", 1),
                             ("2024-06-30", "2024-07-01", 1),
                             ("2024-07-01", "2024-07-02", 0)):
    selection = run_funnel("000006.SZ", pair(ann=ann, start=start,
                                              before_start="2010-01-01"))
    check(f"研究期边界 {ann}", selection["counters"]["final_events"], expected)

# 同票同锚两次候选全部拒绝
duplicate = pair() + [
    row("甲股份", "2021-01-01", "2020-12-30"),
    row("ST甲", "2022-01-03", "2020-04-29"),
]
selection = run_funnel("000007.SZ", duplicate)
check("重复事件键整组剔除", (selection["counters"]["duplicate_event_keys"],
                              selection["counters"]["event_key_duplicate_fail_closed"],
                              selection["counters"]["final_events"]), (1, 2, 0))

# 恒等式、组成守恒、跨票聚合、输入行序确定性
merged = merge_selections([starred, plain, run_funnel("000003.SZ", mixed)])
check("主漏斗恒等式", funnel_identity_ok(merged["counters"]), True)
check("带星+不带星=最终事件", composition_identity_ok(merged["counters"]), True)
check("组成计数", (merged["counters"]["starred_events"],
                   merged["counters"]["plain_st_events"],
                   merged["counters"]["final_events"]), (1, 1, 2))

rows = pair(after="ST乙")
shuffled = list(rows)
random.Random(17).shuffle(shuffled)
first = select_st_imposition_events("000008.SZ", sorted(rows, key=lambda x: x["start_date"]))
second = select_st_imposition_events("000008.SZ", sorted(shuffled, key=lambda x: x["start_date"]))
check("确定性双跑逐字节同",
      json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True), True)

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
