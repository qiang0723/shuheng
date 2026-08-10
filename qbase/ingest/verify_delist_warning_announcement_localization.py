#!/usr/bin/env python3
"""exp22 多日双读漂移定位攻击 fixture；零网络、零数据库。"""
from __future__ import annotations

import datetime as dt
import tempfile
from pathlib import Path

from qbase.ingest import delist_warning_announcement_index as indexer

PASSED = 0
TOTAL = 0
START, END = dt.date(2020, 1, 1), dt.date(2020, 1, 4)
TZ = dt.timezone(dt.timedelta(hours=8))


def check(name: str, actual, expected) -> None:
    global PASSED, TOTAL
    TOTAL += 1
    if actual != expected:
        raise AssertionError(f"{name}: actual={actual!r}, expected={expected!r}")
    PASSED += 1
    print(f"PASS {name}")


def rejects(name: str, fn, contains: str) -> None:
    try:
        fn()
    except Exception as error:
        check(name, contains in str(error), True)
        return
    raise AssertionError(f"{name}: 未拒绝")


def _item(identifier: str, day: str) -> dict:
    stamp = int(dt.datetime.fromisoformat(day + "T12:00:00+08:00").timestamp() * 1000)
    return {"announcementId": identifier, "secCode": "000001", "secName": "测试公司",
            "announcementTitle": "年度报告", "announcementTime": stamp,
            "announcementType": "01010101", "adjunctUrl": f"finalpage/{identifier}.PDF"}


def _response(rows: list[dict], more: bool, total: int) -> dict:
    return {"announcements": rows, "hasMore": more, "totalAnnouncement": total}


def _range(request: dict) -> tuple[dt.date, dt.date]:
    left, right = request["seDate"].split("~")
    return dt.date.fromisoformat(left), dt.date.fromisoformat(right)


def _within(rows: list[dict], request: dict) -> list[dict]:
    start, end = _range(request)
    return [row for row in rows if start <= dt.datetime.fromtimestamp(
        row["announcementTime"] / 1000, TZ).date() <= end]


def test_content_drift(tmp: Path) -> None:
    dataset = [_item(str(day), f"2020-01-0{day}") for day in range(1, 5)]
    root_calls = 0
    def poster(_url, request):
        nonlocal root_calls
        rows = _within(dataset, request)
        if _range(request) == (START, END):
            root_calls += 1
            rows = rows if root_calls == 1 else rows[:-1]
        return _response(rows, False, len(rows))
    rows, audit = indexer.collect_code(
        "000001", "org", START, END, tmp / "content", poster)
    check("多日集合漂移继续二分", [row["announcement_id"] for row in rows],
          ["1", "2", "3", "4"])
    check("漂移父双读计入守恒", audit["pages"], 6)
    check("漂移后子叶双读", audit["bisection_audit_by_year"]["2020"]["leaf_count"], 2)


def test_state_and_structure(tmp: Path) -> None:
    dataset = [_item(str(i), "2020-01-01" if i < 15 else "2020-01-04")
               for i in range(indexer.PAGE_SIZE)]
    root_calls = 0
    def state_poster(_url, request):
        nonlocal root_calls
        rows = _within(dataset, request)
        if _range(request) != (START, END):
            return _response(rows, False, len(rows))
        root_calls += 1
        return _response(rows, root_calls == 2, 30 if root_calls == 1 else 31)
    rows, audit = indexer.collect_code(
        "000001", "org", START, END, tmp / "state", state_poster)
    check("多日分页状态漂移继续二分", len(rows), 30)
    check("状态漂移父双读计入守恒", audit["pages"], 6)

    calls = 0
    def malformed(_url, _request):
        nonlocal calls
        calls += 1
        return _response(dataset[:1], calls == 2, 1)
    rejects("结构性短页不以二分掩盖", lambda: indexer.collect_code(
        "000001", "org", START, END, tmp / "malformed", malformed),
        "pass_b 非终页行数不满")


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        test_content_drift(root); test_state_and_structure(root)
    print(f"verify_delist_warning_announcement_localization: {PASSED}/{TOTAL} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
