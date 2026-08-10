#!/usr/bin/env python3
"""exp22 日期二分与叶片双读攻击 fixture；零网络、零数据库。"""
from __future__ import annotations

import datetime as dt
import json
import tempfile
from pathlib import Path

from qbase.ingest import delist_warning_announcement_bisection as bisection
from qbase.ingest import delist_warning_announcement_index as indexer

PASSED = 0
TOTAL = 0


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


def _ms(day: str) -> int:
    value = dt.datetime.fromisoformat(day + "T12:00:00+08:00")
    return int(value.timestamp() * 1000)


def _item(identifier: str, day: str, title: str = "年度报告") -> dict:
    return {
        "announcementId": identifier, "secCode": "000001", "secName": "测试公司",
        "announcementTitle": title, "announcementTime": _ms(day),
        "announcementType": "01010101", "adjunctUrl": f"finalpage/{identifier}.PDF",
    }


def _response(items: list[dict], more: bool, total: int | None = None) -> dict:
    payload = {"announcements": items, "hasMore": more}
    if total is not None:
        payload["totalAnnouncement"] = total
    return payload


def _range(request: dict) -> tuple[dt.date, dt.date]:
    left, right = request["seDate"].split("~")
    return dt.date.fromisoformat(left), dt.date.fromisoformat(right)


def _dataset_poster(dataset: list[dict]):
    def poster(_url: str, request: dict) -> dict:
        assert request["pageNum"] == "1"
        start, end = _range(request)
        timezone = dt.timezone(dt.timedelta(hours=8))
        rows = [item for item in dataset if start <= dt.datetime.fromtimestamp(
            item["announcementTime"] / 1000, timezone).date() <= end]
        return _response(rows[:indexer.PAGE_SIZE], len(rows) > indexer.PAGE_SIZE, len(rows))
    return poster


def _paged_poster(passes: list[list[dict]]):
    current_pass = -1
    def poster(_url: str, request: dict) -> dict:
        nonlocal current_pass
        page = int(request["pageNum"])
        if page == 1:
            current_pass += 1
        dataset = passes[current_pass]
        offset = (page - 1) * indexer.PAGE_SIZE
        rows = dataset[offset:offset + indexer.PAGE_SIZE]
        return _response(rows, offset + len(rows) < len(dataset), len(dataset))
    return poster


def test_bisection(tmp: Path) -> None:
    dataset = []
    for day in range(1, 5):
        dataset.extend(_item(f"{day}-{i}", f"2020-01-0{day}") for i in range(10))
    rows, audit = indexer.collect_code(
        "000001", "org", dt.date(2020, 1, 1), dt.date(2020, 1, 4),
        tmp / "split", _dataset_poster(dataset))
    check("二分全集守恒", len(rows), 40)
    check("二分叶片数", audit["bisection_audit_by_year"]["2020"]["leaf_count"], 2)
    check("根探针加叶片双读", audit["pages"], 5)
    leaves = audit["bisection_audit_by_year"]["2020"]["leaves"]
    check("叶片互斥覆盖", [(x["start"], x["end"]) for x in leaves],
          [("2020-01-01", "2020-01-02"), ("2020-01-03", "2020-01-04")])
    check("新布局请求件数", len(list((tmp / "split" / "000001" /
                                      indexer.RAW_LAYOUT).rglob("*.json"))), 5)


def test_double_read_attacks(tmp: Path) -> None:
    start = end = dt.date(2020, 1, 1)
    calls = 0
    def drifting(_url, _request):
        nonlocal calls
        calls += 1
        return _response([_item(str(calls), "2020-01-01")], False, 1)
    rejects("叶片双读漂移拒绝", lambda: indexer.collect_code(
        "000001", "org", start, end, tmp / "drift", drifting), "双读规范化行不一致")

    calls = 0
    def state_drift(_url, _request):
        nonlocal calls
        calls += 1
        return _response([_item("1", "2020-01-01")], calls == 2, 1)
    rejects("叶片分页状态漂移拒绝", lambda: indexer.collect_code(
        "000001", "org", start, end, tmp / "state", state_drift), "分页状态不一致")
    wrong_total = lambda _url, _req: _response([_item("1", "2020-01-01")], False, 2)
    rejects("叶片总数不命中拒绝", lambda: indexer.collect_code(
        "000001", "org", start, end, tmp / "total", wrong_total), "未命中API")
    calls = 0
    def total_drift(_url, _request):
        nonlocal calls
        calls += 1
        return _response([_item("1", "2020-01-01")], False, calls)
    rows, audit = indexer.collect_code(
        "000001", "org", start, end, tmp / "total_drift", total_drift)
    check("双读计数漂移但规范化行一致通过", len(rows), 1)
    leaf = audit["bisection_audit_by_year"]["2020"]["leaves"][0]
    check("双读计数观测完整保留", leaf["api_totals"], (1, 2))


def test_single_day_pagination(tmp: Path) -> None:
    start = end = dt.date(2020, 1, 1)
    full = [_item(str(i), "2020-01-01") for i in range(indexer.PAGE_SIZE)]
    stable = full + [_item("30", "2020-01-01")]
    rows, audit = indexer.collect_code(
        "000001", "org", start, end, tmp / "single", _paged_poster([stable, stable]))
    leaf = audit["bisection_audit_by_year"]["2020"]["leaves"][0]
    check("单日多页双遍全集通过", len(rows), 31)
    check("单日多页四次原始读取", audit["pages"], 4)
    check("单日多页双遍页数留痕", leaf["pass_pages"], (2, 2))
    check("单日多页双遍计数观测留痕", leaf["pass_api_totals"],
          ((31, 31), (31, 31)))

    drifted = stable[:-1] + [_item("changed", "2020-01-01")]
    rejects("单日多页双遍漂移拒绝", lambda: indexer.collect_code(
        "000001", "org", start, end, tmp / "multi_drift",
        _paged_poster([stable, drifted])), "双遍规范化全集不一致")
    duplicate = full + [_item("0", "2020-01-01")]
    rejects("单日多页跨页重复拒绝", lambda: indexer.collect_code(
        "000001", "org", start, end, tmp / "page_duplicate",
        _paged_poster([duplicate])), "跨页公告ID重复")

    def short(_url, request):
        page = int(request["pageNum"])
        return _response(full[:29] if page == 1 else full[:2], page == 1, 31)
    rejects("单日多页非终页短读拒绝", lambda: indexer.collect_code(
        "000001", "org", start, end, tmp / "day_short", short), "非终页行数不满")

    def no_total(_url, request):
        page = int(request["pageNum"])
        rows = full if page == 1 else [_item("30", "2020-01-01")]
        return _response(rows, page == 1)
    rejects("单日多页缺计数观测拒绝", lambda: indexer.collect_code(
        "000001", "org", start, end, tmp / "no_total", no_total), "未命中API")

    calls = 0
    def second_pass_bad_total(_url, request):
        nonlocal calls
        page = int(request["pageNum"])
        if page == 1:
            calls += 1
        rows = stable[(page - 1) * indexer.PAGE_SIZE:page * indexer.PAGE_SIZE]
        total = 31 if calls == 1 else 99
        return _response(rows, page == 1, total)
    rejects("单日多页任一遍计数不闭拒绝", lambda: indexer.collect_code(
        "000001", "org", start, end, tmp / "bad_total", second_pass_bad_total),
        "未命中API")


def test_partition_attacks(tmp: Path) -> None:
    start = end = dt.date(2020, 1, 1)
    full = [_item(str(i), "2020-01-01") for i in range(indexer.PAGE_SIZE)]
    old_max = bisection.MAX_DAY_PAGES
    bisection.MAX_DAY_PAGES = 2
    def endless(_url, request):
        page = int(request["pageNum"])
        rows = [_item(f"{page}-{i}", "2020-01-01") for i in range(indexer.PAGE_SIZE)]
        return _response(rows, True, 90)
    try:
        rejects("单日多页上限拒绝", lambda: indexer.collect_code(
            "000001", "org", start, end, tmp / "page_limit", endless), "超过2页")
    finally:
        bisection.MAX_DAY_PAGES = old_max

    rejects("非终页短读拒绝", lambda: indexer.collect_code(
        "000001", "org", dt.date(2020, 1, 1), dt.date(2020, 1, 2),
        tmp / "short", lambda _u, _r: _response(full[:1], True, 31)), "非终页行数不满")

    def duplicate_leaf(_url, request):
        left, right = _range(request)
        if (right - left).days:
            return _response(full, True, 31)
        return _response([_item("same", left.isoformat())], False, 1)
    rejects("跨叶片公告ID重复拒绝", lambda: indexer.collect_code(
        "000001", "org", dt.date(2020, 1, 1), dt.date(2020, 1, 2),
        tmp / "duplicate", duplicate_leaf), "跨叶片公告ID重复")


def test_resume_and_layouts(tmp: Path) -> None:
    start = end = dt.date(2020, 1, 1)
    stable = lambda _u, _r: _response([_item("1", "2020-01-01")], False, 1)
    root = tmp / "resume"
    old_page = root / "000001" / "annual_v2" / "2020" / "00001.json"
    old_page.parent.mkdir(parents=True); old_page.write_bytes(b"annual-v2-evidence\n")
    v3_page = (root / "000001" / "bisect_v3" / "2020" /
               "2020-01-01_2020-01-01" / "probe.json")
    v3_page.parent.mkdir(parents=True); v3_page.write_bytes(b"bisect-v3-evidence\n")
    indexer.collect_code("000001", "org", start, end, root, stable)
    check("annual_v2失败证据未覆盖", old_page.read_bytes(), b"annual-v2-evidence\n")
    check("bisect_v3失败证据未覆盖", v3_page.read_bytes(), b"bisect-v3-evidence\n")
    no_fetch = lambda _u, _r: (_ for _ in ()).throw(AssertionError("不应重抓"))
    rows, _ = indexer.collect_code("000001", "org", start, end, root, no_fetch)
    check("新布局成功件只读恢复", len(rows), 1)
    probe = next((root / "000001" / indexer.RAW_LAYOUT).rglob("00001.json"))
    payload = json.loads(probe.read_text()); payload["request"]["pageNum"] = "2"
    probe.write_text(json.dumps(payload))
    rejects("新布局请求漂移拒绝", lambda: indexer.collect_code(
        "000001", "org", start, end, root, no_fetch), "请求或响应无效")

    evidence = tmp / "v2_marker"
    v2_raw = evidence / "raw_pages" / "000001" / "annual_v2" / "2020"
    indexer._write_once_json(v2_raw / "00001.json", {"legacy": "annual_v2"})
    digest = indexer._atomic_json(evidence / "normalized" / "000001.SZ.json", [])
    pages, tree_sha = indexer._page_tree(v2_raw.parent, recursive=True)
    indexer._atomic_json(evidence / "done" / "000001.SZ.json", {
        "start": start, "end": end, "normalized_sha256": digest,
        "pages": pages, "raw_pages_sha256": tree_sha, "raw_layout": "annual_v2"})
    check("annual_v2成功marker继续自验", indexer._done_valid(
        evidence, "000001.SZ", start, end), True)

    v3_evidence = tmp / "v3_marker"
    v3_raw = (v3_evidence / "raw_pages" / "000001" / "bisect_v3" /
              "2020" / "2020-01-01_2020-01-01")
    indexer._write_once_json(v3_raw / "probe.json", {"legacy": "bisect_v3"})
    digest = indexer._atomic_json(v3_evidence / "normalized" / "000001.SZ.json", [])
    pages, tree_sha = indexer._page_tree(
        v3_evidence / "raw_pages" / "000001" / "bisect_v3", recursive=True)
    indexer._atomic_json(v3_evidence / "done" / "000001.SZ.json", {
        "start": start, "end": end, "normalized_sha256": digest,
        "pages": pages, "raw_pages_sha256": tree_sha, "raw_layout": "bisect_v3"})
    check("bisect_v3成功marker继续自验", indexer._done_valid(
        v3_evidence, "000001.SZ", start, end), True)


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        test_bisection(root); test_double_read_attacks(root)
        test_single_day_pagination(root); test_partition_attacks(root)
        test_resume_and_layouts(root)
    print(f"verify_delist_warning_announcement_bisection: {PASSED}/{TOTAL} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
