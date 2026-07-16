"""holder_sell 事件适配器自检(§5 白名单④;零DB零I/O,合成行)。
验:events_from_rows 映射正确性(EventRow 字段/event_id 格式/规则留痕透传/确定性双跑)。
用法: python taosha/harness/verify_holder_sell_adapter.py
"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.harness.run_holder_sell_study import events_from_rows  # noqa: E402

FAIL = 0
N = 0


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    if not ok:
        FAIL += 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


ROWS = [
    {"ts_code": "000001.SZ", "stock_code": "000001", "announcement_id": "A1",
     "title": "关于股东减持股份计划的预披露公告", "holder_name": "张三",
     "reduce_ratio_max_pct": 2.0, "reduce_period_start": "2023-02-01",
     "reduce_period_end": "2023-07-31", "valid_time": "2023-01-10T09:00:00+00:00",
     "snapshot_batch": "batch12"},
    {"ts_code": "000001.SZ", "stock_code": "000001", "announcement_id": "A2",
     "title": "关于股东减持计划时间过半的公告", "holder_name": None,
     "reduce_ratio_max_pct": None, "reduce_period_start": None,
     "reduce_period_end": None, "valid_time": "2023-04-10T09:00:00+00:00",
     "snapshot_batch": "batch12"},
    {"ts_code": "600000.SH", "stock_code": "600000", "announcement_id": "A3",
     "title": "关于持股5%以上股东减持股份计划的预披露公告", "holder_name": None,
     "reduce_ratio_max_pct": 1.5, "reduce_period_start": None,
     "reduce_period_end": None, "valid_time": "2023-03-01T22:00:00+00:00",
     "snapshot_batch": "batch12"},
]

events, sel = events_from_rows(ROWS)
check("事件数(污染1条拒)", len(events), 2)
check("EventRow.ts_code 序", [e.ts_code for e in events], ["000001.SZ", "600000.SH"])
# A1: 2023-01-10T09:00Z = 京时 17:00 → 事件日 2023-01-10
check("event_id 格式", events[0].event_id, "000001.SZ:20230110")
check("first_ann_date 类型", isinstance(events[0].first_ann_date, dt.date), True)
# A3: 2023-03-01T22:00Z = 京时 03-02 06:00 → 事件日 2023-03-02(跨日换算)
check("京时跨日换算", events[1].event_id, "600000.SH:20230302")
check("event_type_layer", {e.event_type_layer for e in events}, {"holder_sell"})
check("snapshot_batch 透传", events[0].snapshot_batch, "batch12")
check("规则留痕透传:halfway 拒1", sel["counters"]["class"]["halfway"], 1)
check("规则留痕透传:events 计数", sel["counters"]["events"], 2)

r1 = json.dumps([e.event_id for e in events_from_rows(ROWS)[0]])
r2 = json.dumps([e.event_id for e in events_from_rows(ROWS)[0]])
check("确定性双跑", r1 == r2, True)

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
