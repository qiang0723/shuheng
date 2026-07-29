"""exp10 volume_drought_rules 冻结口径攻击 fixture（纯函数、零 DB）。"""
import datetime as dt
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from taosha.compute.volume_drought_rules import (  # noqa: E402
    finalize_events, merge_selections, select_volume_drought_events,
)


FAIL = 0
N = 0
START = dt.date(2015, 1, 1)


def check(name, got, want):
    global FAIL, N
    N += 1
    ok = got == want
    FAIL += 0 if ok else 1
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: got={got!r} want={want!r}")


def rows(amounts, opens=None, closes=None, ranks=None, start=START):
    opens = opens or [Decimal("10")] * len(amounts)
    closes = closes or [Decimal("11")] * len(amounts)
    ranks = ranks or list(range(1, len(amounts) + 1))
    return [{"trade_date": start + dt.timedelta(days=i), "cal_rank": ranks[i],
             "amount": amounts[i], "open": opens[i], "close": closes[i]}
            for i in range(len(amounts))]


def select(amounts, opens=None, closes=None, ranks=None, code="000001.SZ"):
    return select_volume_drought_events(code, rows(amounts, opens, closes, ranks))


# F1 基本事件：60根历史→5日低量→首次放量收阳。
s = select([Decimal("100")] * 60 + [Decimal("20")] * 5 + [Decimal("150")])
check("F1 首次放量收阳成事件", (len(s["events"]), s["counters"]["armed_segments"]), (1, 1))
check("F1 当前bar排除在prior60", s["events"][0]["amount_to_prior_ma"] != "1", True)

# F2 第一次放量不收阳终结；后续必须重新五低武装，不能等待第二根。
amounts = [Decimal("100")] * 60 + [Decimal("20")] * 5 + [Decimal("150")]
amounts += [Decimal("20")] * 5 + [Decimal("150")]
opens = [Decimal("10")] * len(amounts)
closes = [Decimal("11")] * len(amounts)
closes[65] = Decimal("9")
s = select(amounts, opens, closes)
check("F2 非收阳拒绝后重新蓄积", (len(s["events"]), len(s["terminal_rejects"]),
                                  s["counters"]["armed_segments"]), (1, 1, 2))

# F3 历史不足60根不参与状态判定。
s = select([Decimal("10")] * 59)
check("F3 不足60根零事件", (len(s["events"]), s["counters"]["insufficient_ma_rows"]), (0, 59))

# F4 30%严格边界不算低；随后5个真正低量才武装。
amounts = [Decimal("100")] * 60 + [Decimal("30")] + [Decimal("20")] * 5 + [Decimal("150")]
s = select(amounts)
check("F4 恰30%不算低", (len(s["events"]), s["counters"]["exact_low_boundary"],
                          s["events"][0]["low_days"]), (1, 1, 5))

# F5 armed 后 amount==滚动均量不终结；下一根严格大于才终结。
amounts = [Decimal("100")] * 60 + [Decimal("20")] * 5
prior = amounts[-60:]
equal_ma = sum(prior) / Decimal(60)
amounts += [equal_ma, equal_ma + Decimal("1")]
s = select(amounts)
check("F5 恰100%保持armed", (len(s["events"]), s["counters"]["exact_breakout_boundary"],
                              s["counters"]["armed_neutral_rows"]), (1, 1, 1))

# F6 停牌gap打断低量段但不清prior；gap后五低仍能直接重新武装。
amounts = [Decimal("100")] * 60 + [Decimal("20")] * 2 + [Decimal("20")] * 5 + [Decimal("150")]
ranks = list(range(1, len(amounts) + 1))
for idx in range(62, len(ranks)):
    ranks[idx] += 2
s = select(amounts, ranks=ranks)
check("F6 prior60跨停牌保留", (len(s["events"]), s["counters"]["calendar_gap_breaks"]), (1, 1))

# F7 armed 后 gap 为互斥终局；gap后终端不能沿用旧armed。
amounts = [Decimal("100")] * 60 + [Decimal("20")] * 5 + [Decimal("150")]
ranks = list(range(1, len(amounts) + 1)); ranks[65] += 2
s = select(amounts, ranks=ranks)
check("F7 gap打断armed", (len(s["events"]), s["counters"]["armed_gap_breaks"]), (0, 1))

# F8 invalid bar 打断 armed 且不入均量；随后的放量不能成事件。
amounts = [Decimal("100")] * 60 + [Decimal("20")] * 5 + [None, Decimal("150")]
s = select(amounts)
check("F8 invalid打断armed", (len(s["events"]), s["counters"]["armed_invalid_breaks"]), (0, 1))

# F9 右删失是互斥终局。
s = select([Decimal("100")] * 60 + [Decimal("20")] * 5)
check("F9 armed右删失", s["counters"]["right_censored_armed"], 1)

# F10 事件键重复全剔；研究期两端严格。
event = {"ts_code": "000001.SZ", "event_date": "2015-01-01", "low_start": "2014-12-01"}
merged = {"events": [event, dict(event)], "terminal_rejects": [], "counters": {}}
f = finalize_events(merged)
check("F10 重复事件键全剔", (len(f["events"]), f["counters"]["event_key_uniqueness_violations"],
                              f["counters"]["uniqueness_dropped_events"]), (0, 1, 2))
events = [dict(event, ts_code="A", event_date="2010-12-31"),
          dict(event, ts_code="B", event_date="2011-01-01"),
          dict(event, ts_code="C", event_date="2024-07-01")]
f = finalize_events({"events": events, "terminal_rejects": [], "counters": {}})
check("F10 研究期闭开边界", [(e["ts_code"], e["event_date"]) for e in f["events"]],
      [("B", "2011-01-01")])

# F11 合并与双跑确定性。
a = select([Decimal("100")] * 60 + [Decimal("20")] * 5 + [Decimal("150")], code="A")
b = select([Decimal("100")] * 60 + [Decimal("20")] * 5 + [Decimal("150")], code="B")
r1 = finalize_events(merge_selections([a, b]))
r2 = finalize_events(merge_selections([a, b]))
check("F11 双跑selection确定性", (r1["selection_sha256"], r1["events"]),
      (r2["selection_sha256"], r2["events"]))
check("F11 armed终局守恒", r1["counters"]["armed_segments"],
      r1["counters"]["events_all_periods"] + r1["counters"]["breakout_not_positive_all_periods"]
      + r1["counters"]["armed_gap_breaks"] + r1["counters"]["armed_invalid_breaks"]
      + r1["counters"]["right_censored_armed"])

print(f"\n{N - FAIL}/{N} PASS" + ("" if FAIL == 0 else f"  ⚠ {FAIL} FAIL"))
sys.exit(1 if FAIL else 0)
