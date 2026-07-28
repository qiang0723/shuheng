"""exp24 L2 规则攻击 fixture（纯函数、零 DB）。"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from taosha.compute.sox_spillover_rules import (
    detect_triggers, expand_members, map_and_drop_collisions, select_events,
)


class Checks:
    def __init__(self):
        self.n = 0

    def ok(self, value, note):
        assert value, note
        self.n += 1


def _sox_rows():
    return [
        {"trade_date": dt.date(2020, 1, 1), "close": Decimal("100"), "currency": ""},
        {"trade_date": dt.date(2020, 1, 2), "close": Decimal("103"), "currency": "USD"},
        {"trade_date": dt.date(2020, 1, 3), "close": Decimal("99.91"), "currency": "USD"},
        {"trade_date": dt.date(2020, 1, 4), "close": Decimal("102.9073"), "currency": "USD"},
    ]


def main():
    c = Checks()
    triggers, audit = detect_triggers(_sox_rows())
    c.ok(len(triggers) == 3, "三次恰±3%均触发")
    c.ok([t["direction"] for t in triggers] == ["up", "down", "up"], "方向")
    c.ok(audit["exact_boundary"] == 3, "闭区间恰位")
    c.ok(audit["empty_currency_rows"] == 1, "currency空值只披露")
    c.ok(all(isinstance(t["return"], Decimal) for t in triggers), "Decimal保真")

    below = _sox_rows()[:1] + [
        {"trade_date": dt.date(2020, 1, 2), "close": Decimal("102.999"), "currency": "USD"}]
    c.ok(detect_triggers(below)[1]["triggers"] == 0, "阈值下不触发")
    try:
        detect_triggers(_sox_rows() + [_sox_rows()[1]])
    except ValueError:
        c.ok(True, "重复SOX日期fail-closed")
    else:
        c.ok(False, "重复SOX日期应拒")

    calendar = [dt.date(2020, 1, 3), dt.date(2020, 1, 5)]
    kept, mapping = map_and_drop_collisions(triggers, calendar)
    c.ok(len(kept) == 1 and kept[0]["event_date"] == dt.date(2020, 1, 3), "T+1起映射")
    c.ok(mapping["collision_dates"] == 1, "长假多对一识别")
    c.ok(mapping["collision_triggers_dropped"] == 2, "D4整组剔除")
    c.ok(mapping["collision_items"][0]["trigger_dates"]
         == [dt.date(2020, 1, 3), dt.date(2020, 1, 4)], "D4清单")

    event = {"event_date": dt.date(2020, 1, 3), "trigger_date": dt.date(2020, 1, 2),
             "return": Decimal("0.03"), "direction": "up", "direction_sign": 1}
    members = [
        {"index_code": "801081.SI", "ts_code": "A.SZ", "in_date": dt.date(2019, 1, 1),
         "out_date": None},
        {"index_code": "801081.SI", "ts_code": "B.SZ", "in_date": dt.date(2020, 1, 3),
         "out_date": None},
        {"index_code": "801081.SI", "ts_code": "C.SZ", "in_date": dt.date(2019, 1, 1),
         "out_date": dt.date(2020, 1, 3)},
        {"index_code": "801081.SI", "ts_code": "D.BJ", "in_date": dt.date(2019, 1, 1),
         "out_date": None},
        {"index_code": "801081.SI", "ts_code": "E.SZ", "in_date": dt.date(2020, 2, 1),
         "out_date": dt.date(2020, 1, 1)},
    ]
    events, ma = expand_members([event], members)
    c.ok([e["ts_code"] for e in events] == ["A.SZ", "B.SZ"], "成员[in,out)边界")
    c.ok(ma["member_rejected_rows"] == 2, "北交所+非法区间剔除")
    c.ok(ma["pool_members_by_event_date"][dt.date(2020, 1, 3)] == 2, "成员日计数")
    c.ok(all(e["direction_sign"] == 1 for e in events), "方向符号带入事件")

    dup_events, dup_audit = expand_members([event], members[:1] + members[:1])
    c.ok(dup_events == [], "重复事件键涉事组全剔")
    c.ok(dup_audit["duplicate_event_keys"] == 1, "重复键计数")
    c.ok(dup_audit["duplicate_events_dropped"] == 2, "重复行逐条核销")

    full = select_events(_sox_rows()[:2], members[:2], [dt.date(2020, 1, 3)])
    c.ok(full["funnel_identity_ok"], "总漏斗恒等")
    c.ok(full["counters"]["surviving_trigger_dates"] == 1, "存活触发日")
    c.ok(full["counters"]["final_events"] == 2, "池展开事件数")
    c.ok(full["trigger_yearly"] == {2020: 1}, "逐年分布")
    c.ok(full["counters"]["zero_member_event_dates"] == 0, "零成员日计数")

    print(f"verify_sox_spillover_rules: {c.n}/{c.n} PASS")


if __name__ == "__main__":
    main()
