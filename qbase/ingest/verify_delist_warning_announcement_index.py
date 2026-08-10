#!/usr/bin/env python3
"""exp22 公告索引器离线攻击 fixture；零网络、零数据库。"""
from __future__ import annotations

import datetime as dt
import http.client
import json
import tempfile
from pathlib import Path

from qbase.ingest import delist_warning_announcement_index as indexer
from qbase.ingest import delist_warning_announcement_documents as documents
from qbase.ingest import delist_warning_announcement_contract as contract_queue
from qbase.ingest import cninfo
from qbase.ingest import verify_delist_warning_announcement_readback as readback

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


def _announcement(identifier: str, code: str = "000001",
                  day: str = "2020-01-02", title: str = "年度报告") -> dict:
    return {
        "announcementId": identifier, "secCode": code, "secName": "测试公司",
        "announcementTitle": title, "announcementTime": _ms(day),
        "announcementType": "01010101", "adjunctUrl": f"finalpage/{identifier}.PDF",
    }


def _response(items: list[dict], more: bool, total: int | None = None) -> dict:
    payload = {"announcements": items, "hasMore": more}
    if total is not None:
        payload["totalAnnouncement"] = total
    return payload


def _stable_poster(url: str, request: dict) -> dict:
    assert url == indexer.QUERY_URL
    assert request["pageNum"] == "1"
    rows = [_announcement("1", title="关于实施退市风险警示的公告"),
            _announcement("2", day="2020-02-01")]
    return _response(rows, False, 2)


def test_routes(tmp: Path) -> None:
    good = tmp / "routes.json"
    good.write_text(json.dumps({
        "artifact_status": "ROUTING_ONLY_NOT_EXP22_CANDIDATES",
        "routes": ["000001.SZ", "600000.SH"]}) + "\n")
    check("路由排序唯一", indexer.load_routes(good), ["000001.SZ", "600000.SH"])
    bad = tmp / "bad_routes.json"
    bad.write_text(json.dumps({
        "artifact_status": "ROUTING_ONLY_NOT_EXP22_CANDIDATES",
        "routes": ["600000.SH", "000001.SZ"]}))
    rejects("路由乱序拒绝", lambda: indexer.load_routes(bad), "排序后的唯一")
    bad.write_text(json.dumps({"artifact_status": "WRONG", "routes": []}))
    rejects("路由身份拒绝", lambda: indexer.load_routes(bad), "status")


def test_org_map() -> None:
    getter = lambda _: json.dumps({"stockList": [
        {"code": "000001", "orgId": "gssz0000001"},
        {"code": "600000", "orgId": "gssh0600000"}]}).encode()
    check("官方orgId映射", len(indexer.load_org_map(getter)), 2)
    duplicate = lambda _: json.dumps({"stockList": [
        {"code": "000001", "orgId": "a"},
        {"code": "000001", "orgId": "b"}]}).encode()
    rejects("orgId重复拒绝", lambda: indexer.load_org_map(duplicate), "重复")
    rejects("orgId空映射拒绝", lambda: indexer.load_org_map(lambda _: b'{"stockList":[]}'), "为空")


def test_incomplete_read_retry() -> None:
    attempts: list[int] = []
    waits: list[float] = []

    def flaky():
        attempts.append(1)
        if len(attempts) < cninfo.MAX_TRIES:
            raise http.client.IncompleteRead(b"partial", 20)
        return {"ok": True}

    original_sleep = cninfo.time.sleep
    try:
        cninfo.time.sleep = waits.append
        check("IncompleteRead整请求重试后成功", cninfo._retry(flaky, "fixture"), {"ok": True})
    finally:
        cninfo.time.sleep = original_sleep
    check("IncompleteRead最多三次尝试", len(attempts), cninfo.MAX_TRIES)
    check("IncompleteRead两次指数退避", len(waits), cninfo.MAX_TRIES - 1)


def test_pages(tmp: Path) -> None:
    start, end = dt.date(2020, 1, 1), dt.date(2020, 12, 31)
    rows, audit = indexer.collect_code("000001", "org", start, end,
                                       tmp / "raw", _stable_poster)
    check("双读公告数", len(rows), 2)
    check("双读审计请求数", audit["pages"], 2)
    check("双读审计公告数", audit["announcements"], 2)
    check("双读审计API总数", audit["api_total"], 2)
    check("双读审计原始页SHA", len(audit["raw_pages_sha256"]), 64)
    check("原始页留存", len(list((tmp / "raw" / "000001" /
                                  indexer.RAW_LAYOUT).rglob("*.json"))), 2)
    check("HTTPS原件URL", rows[0]["source_url"].startswith("https://"), True)
    mixed = _response([_announcement("1", code="000002")], False, 1)
    rejects("混票拒绝", lambda: indexer.validate_page("000001", mixed, start, end), "混票")
    duplicate = _response([_announcement("1"), _announcement("1")], False, 2)
    rejects("页内重复拒绝", lambda: indexer.validate_page("000001", duplicate, start, end), "重复")
    empty_more = _response([], True, 1)
    rejects("空页仍hasMore拒绝", lambda: indexer.validate_page("000001", empty_more, start, end), "为空")
    out = _response([_announcement("1", day="2021-01-01")], False, 1)
    rejects("日期越界拒绝", lambda: indexer.validate_page("000001", out, start, end), "越界")


def test_full_index(tmp: Path) -> None:
    routes = ["000001.SZ"]
    evidence = tmp / "evidence"
    result = indexer.collect_all(routes, {"000001": "org"}, evidence,
                                 dt.date(2020, 1, 1), dt.date(2020, 12, 31),
                                 _stable_poster)
    check("全集路由数", result["route_count"], 1)
    check("全集公告数", result["counts"]["announcements"], 2)
    check("宽召回只一行", result["counts"]["wide_recall"], 1)
    check("标题仅召回身份", result["title_is_recall_only"], True)
    check("元数据不闭E1", result["e1_gate_closed"], False)
    start, end = dt.date(2020, 1, 1), dt.date(2020, 12, 31)
    check("done marker可复核", indexer._done_valid(
        evidence, "000001.SZ", start, end), True)
    (evidence / "normalized" / "000001.SZ.json").write_text("[]\n")
    check("原件被改done失效", indexer._done_valid(
        evidence, "000001.SZ", start, end), False)
    rejects("损坏完成件拒绝覆盖", lambda: indexer.collect_all(
        routes, {"000001": "org"}, evidence, start, end, _stable_poster), "拒绝覆盖")
    rejects("缺orgId拒绝", lambda: indexer.collect_all(
        routes, {}, tmp / "missing", dt.date(2020, 1, 1),
        dt.date(2020, 12, 31), _stable_poster), "映射缺")
    legacy = tmp / "legacy"; raw = legacy / "raw_pages" / "000001"
    request = indexer._request("000001", "org", start, end, 1)
    response = _response([_announcement("legacy")], False, 1)
    indexer._write_once_json(raw / "00001.json", {"request": request, "response": response})
    normalized = [indexer._normalize("000001", response["announcements"][0], start, end)]
    digest = indexer._atomic_json(legacy / "normalized" / "000001.SZ.json", normalized)
    pages, page_sha = indexer._page_tree(raw)
    indexer._atomic_json(legacy / "done" / "000001.SZ.json", {
        "start": start, "end": end, "normalized_sha256": digest,
        "pages": pages, "raw_pages_sha256": page_sha})
    check("旧版平铺marker继续自验", indexer._done_valid(
        legacy, "000001.SZ", start, end), True)


def test_documents(tmp: Path) -> None:
    evidence = tmp / "documents_case"
    evidence.mkdir()
    rows = [
        {"announcement_id": "10", "ts_code": "000001.SZ", "source_url": "https://x/10"},
        {"announcement_id": "10", "ts_code": "600000.SH", "source_url": "https://x/10"},
        {"announcement_id": "11", "ts_code": "000001.SZ", "source_url": "https://x/11"},
    ]
    (evidence / "candidate_index.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows))
    getter = lambda url: ((200, "application/pdf", b"%PDF-test") if url.endswith("10")
                          else (200, "text/html", b"<html>ok</html>"))
    result = documents.materialize_documents(evidence, getter)
    check("原件按公告ID去重", result["downloaded_count"], 2)
    check("跨票同公告保留", result["documents"][0]["routed_ts_codes"],
          ["000001.SZ", "600000.SH"])
    check("PDF与HTML均保留", sorted(x["stored_media_type"] for x in result["documents"]),
          ["application/pdf", "text/html"])
    bad = tmp / "bad_doc"; bad.mkdir()
    (bad / "candidate_index.jsonl").write_text(json.dumps({
        "announcement_id": "12", "ts_code": "000001.SZ", "source_url": "https://x/12"}) + "\n")
    failed = documents.materialize_documents(
        bad, lambda _: (200, "application/octet-stream", b"binary"))
    check("未知媒体显式失败", failed["failed_count"], 1)


def test_contract_queue(tmp: Path) -> None:
    evidence = tmp / "contract_case"; evidence.mkdir()
    candidate = {"announcement_id": "10", "ts_code": "000001.SZ",
                 "source_url": "https://x/10", "announcement_date_cn": "2020-01-02",
                 "raw_company_name": "测试", "title": "实施退市风险警示"}
    (evidence / "candidate_index.jsonl").write_text(json.dumps(candidate) + "\n")
    (evidence / "document_manifest.json").write_text(json.dumps({
        "documents": [{"announcement_id": "10", "sha256": "a" * 64}], "errors": []}))
    contract = tmp / "contract.json"
    contract.write_text(json.dumps({
        "artifact_status": "DRAFT_EVIDENCE_CONTRACT_NOT_FOR_FREEZE",
        "contract": {"required_pass_checks": ["official_original", "firstness"]}}))
    result = contract_queue.build_queue(evidence, contract)
    check("合同队列守恒", result["candidate_rows"], result["queue_rows"])
    check("合同不按标题关E1", result["e1_gate_closed"], False)
    check("正文未核保持UNPROVEN", result["queue"][0]["contract_status"],
          "UNPROVEN_BODY_CONTRACT_PENDING")


def test_readback() -> None:
    routes = [f"{prefix}001.{exchange}" for prefix, exchange in [
        ("600", "SH"), ("601", "SH"), ("603", "SH"), ("605", "SH"),
        ("688", "SH"), ("000", "SZ"), ("001", "SZ"), ("002", "SZ"),
        ("003", "SZ"), ("300", "SZ"), ("301", "SZ"), ("600", "SZ")]]
    routes = sorted(routes)
    events = [{"ts_code": code, "ann_date": f"{2011 + i}-01-01"}
              for i, code in enumerate(routes)]
    selected = readback.select_codes({"routes": routes, "events": events}, 12)
    check("读回分层选12票", len(selected), 12)
    check("读回选择无重复", len(set(selected)), 12)
    rows = [{"announcement_id": "1", "title": "x"}]
    check("读回三项恰等", all(readback.compare_rows(rows, rows, "000001.SZ")["checks"].values()), True)
    rejects("读回差异拒绝", lambda: readback.compare_rows(
        rows, [{"announcement_id": "2", "title": "x"}], "000001.SZ"), "不等")
    rejects("读回不足12拒绝", lambda: readback.select_codes(
        {"routes": routes, "events": events}, 11), "至少12")


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        test_routes(root); test_org_map(); test_incomplete_read_retry()
        test_pages(root); test_full_index(root); test_documents(root)
        test_contract_queue(root); test_readback()
    print(f"verify_delist_warning_announcement_index: {PASSED}/{TOTAL} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
