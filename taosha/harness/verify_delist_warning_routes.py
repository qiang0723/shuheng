#!/usr/bin/env python3
"""exp22 公告路由导出的纯函数攻击 fixture；零网络、零数据库。"""
from __future__ import annotations

import datetime as dt

from taosha.harness import export_delist_warning_routes as exporter


def main() -> int:
    rows = [
        {"ts_code": "000001.SZ", "alias": "平安银行",
         "start_date": dt.date(2020, 1, 1),
         "ann_date": dt.date(2019, 12, 31), "snapshot_batch": "7"},
        {"ts_code": "000001.SZ", "alias": "*ST平安",
         "start_date": dt.date(2021, 1, 2),
         "ann_date": dt.date(2021, 1, 1), "snapshot_batch": "7"},
    ]
    selection = exporter._selection(rows)
    checks = {
        "路由纯函数事件": selection["counters"]["final_events"] == 1,
        "路由纯函数带星": selection["counters"]["starred_events"] == 1,
    }
    try:
        exporter.route_payload(rows, "on")
    except RuntimeError as error:
        checks["参考硬闸拒绝小fixture"] = "fail-closed" in str(error)
    else:
        checks["参考硬闸拒绝小fixture"] = False
    try:
        exporter.route_payload(rows, "off")
    except RuntimeError as error:
        checks["只读状态拒绝"] = "fail-closed" in str(error)
    else:
        checks["只读状态拒绝"] = False
    for name, passed in checks.items():
        if not passed:
            raise AssertionError(name)
        print(f"PASS {name}")
    print(f"verify_delist_warning_routes: {len(checks)}/{len(checks)} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
