#!/usr/bin/env python3
"""exp22 巨潮公告完整元数据索引与宽召回原件物化（零数据库写入）。"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from zoneinfo import ZoneInfo

from qbase.ingest import cninfo
from qbase.ingest import delist_warning_announcement_bisection as bisection

QUERY_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
ORGID_URL = "https://www.cninfo.com.cn/new/data/szse_stock.json"
STATIC_BASE = "https://static.cninfo.com.cn/"
SHANGHAI = ZoneInfo("Asia/Shanghai")
PAGE_SIZE = 30
RAW_LAYOUT = "bisect_v6"
SUPPORTED_LAYOUTS = {
    None, "annual_v2", "bisect_v3", "bisect_v4", "bisect_v5", RAW_LAYOUT,
}
ROLE_RE = re.compile(r"退市风险警示|其他风险警示|撤销风险警示|撤销退市|暂停上市|终止上市")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_json(path: Path, payload) -> str:
    data = (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), default=str) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    return _sha(data)


def _write_once_json(path: Path, payload) -> str:
    data = (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), default=str) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise RuntimeError(f"已有原始页与当前官方响应不一致: {path}")
        return _sha(data)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    return _sha(data)


def _page_tree(raw_dir: Path, recursive: bool = False) -> tuple[int, str]:
    pages = sorted(raw_dir.rglob("*.json") if recursive else raw_dir.glob("*.json"))
    body = "".join(
        f"{path.relative_to(raw_dir)}:{_sha(path.read_bytes())}\n" for path in pages
    ).encode()
    return len(pages), _sha(body)


def _read_or_fetch(path: Path, request: dict, poster) -> dict:
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("request") != request or not isinstance(payload.get("response"), dict):
            raise RuntimeError(f"已有原始页请求或响应无效: {path}")
        return payload["response"]
    response = poster(QUERY_URL, request)
    _write_once_json(path, {"request": request, "response": response})
    return response


def _append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":"), default=str) + "\n")
        handle.flush()


def load_routes(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    routes = payload.get("routes")
    if payload.get("artifact_status") != "ROUTING_ONLY_NOT_EXP22_CANDIDATES":
        raise ValueError("route artifact status 非预期")
    if not isinstance(routes, list) or routes != sorted(set(routes)):
        raise ValueError("routes 须为排序后的唯一列表")
    if any(not re.fullmatch(r"\d{6}\.(SH|SZ)", code) for code in routes):
        raise ValueError("routes 含非沪深A股代码")
    return routes


def load_org_map(getter=cninfo._http_get) -> dict[str, str]:
    payload = json.loads(getter(ORGID_URL).decode("utf-8"))
    rows = payload.get("stockList") or []
    pairs = [(row.get("code"), row.get("orgId")) for row in rows]
    if not pairs or any(not code or not org for code, org in pairs):
        raise RuntimeError("官方orgId映射为空或含缺失")
    if len({code for code, _ in pairs}) != len(pairs):
        raise RuntimeError("官方orgId映射证券代码重复")
    return dict(pairs)


def _request(code: str, org_id: str, start: dt.date, end: dt.date,
             page: int) -> dict[str, str]:
    return {
        "stock": f"{code},{org_id}", "tabName": "fulltext",
        "pageSize": str(PAGE_SIZE), "pageNum": str(page),
        "column": "sse" if code.startswith("6") else "szse",
        "category": "", "plate": "", "seDate": f"{start.isoformat()}~{end.isoformat()}",
        "searchkey": "", "secid": "", "sortName": "", "sortType": "",
        "isHLtitle": "false",
    }


def _normalize(code: str, item: dict, start: dt.date, end: dt.date) -> dict:
    announcement_id = str(item.get("announcementId") or "").strip()
    stock_code = str(item.get("secCode") or "").strip()
    valid_time = cninfo.ts_to_utc(item.get("announcementTime"))
    local_date = valid_time.astimezone(SHANGHAI).date() if valid_time else None
    if not announcement_id or stock_code != code or local_date is None:
        raise RuntimeError("公告ID/证券身份/公告时戳缺失或混票")
    if not start <= local_date <= end:
        raise RuntimeError(f"公告时戳越界: {code}/{announcement_id}/{local_date}")
    adjunct = item.get("adjunctUrl")
    return {
        "announcement_id": announcement_id,
        "stock_code": stock_code,
        "raw_company_name": item.get("secName"),
        "title": re.sub(r"\s+", " ", str(item.get("announcementTitle") or "")).strip(),
        "valid_time_utc": valid_time.isoformat(),
        "announcement_date_cn": local_date.isoformat(),
        "announcement_type": item.get("announcementType") or None,
        "source_url": STATIC_BASE + adjunct if adjunct else None,
    }


def validate_page(code: str, response: dict, start: dt.date,
                  end: dt.date) -> tuple[list[dict], bool, int | None]:
    raw = response.get("announcements") or []
    rows = [_normalize(code, item, start, end) for item in raw]
    ids = [row["announcement_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"{code} 页内公告ID重复")
    has_more = bool(response.get("hasMore"))
    if has_more and not rows:
        raise RuntimeError(f"{code} hasMore=true但当前页为空")
    total_raw = response.get("totalAnnouncement")
    total = int(total_raw) if total_raw not in (None, "") else None
    if total is not None and total < 0:
        raise RuntimeError(f"{code} totalAnnouncement非法")
    return rows, has_more, total


def collect_code(code: str, org_id: str, start: dt.date, end: dt.date,
                 raw_root: Path, poster=cninfo._http_post) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    seen_ids: set[str] = set()
    audits_by_year: dict[str, dict] = {}
    read_total = 0
    active_root = raw_root / code / RAW_LAYOUT
    for year in range(start.year, end.year + 1):
        shard_start = max(start, dt.date(year, 1, 1))
        shard_end = min(end, dt.date(year, 12, 31))
        shard_rows, shard_audit = bisection.collect_interval(
            code, org_id, shard_start, shard_end, active_root / str(year), poster,
            _request, _read_or_fetch, validate_page, PAGE_SIZE)
        ids = {item["announcement_id"] for item in shard_rows}
        if seen_ids.intersection(ids):
            raise RuntimeError(f"{code} 跨年度公告ID重复")
        seen_ids.update(ids)
        audits_by_year[str(year)] = shard_audit
        read_total += shard_audit["raw_reads"]
        rows.extend(shard_rows)
    rows.sort(key=lambda item: (item["announcement_date_cn"],
                                item["valid_time_utc"], item["announcement_id"]))
    page_count, raw_pages_sha = _page_tree(active_root, recursive=True)
    if page_count != read_total:
        raise RuntimeError(f"{code} 原始页目录含陈旧或缺失页")
    return rows, {"pages": read_total, "announcements": len(rows),
                  "api_total": len(rows), "api_total_source": "bisected_double_read_leaves",
                  "bisection_audit_by_year": audits_by_year,
                  "raw_layout": RAW_LAYOUT, "raw_pages_sha256": raw_pages_sha}


def _done_valid(evidence: Path, code: str, start: dt.date, end: dt.date) -> bool:
    marker = evidence / "done" / f"{code}.json"
    normalized = evidence / "normalized" / f"{code}.json"
    if not marker.exists() or not normalized.exists():
        return False
    payload = json.loads(marker.read_text(encoding="utf-8"))
    layout = payload.get("raw_layout")
    if layout not in SUPPORTED_LAYOUTS:
        return False
    raw_dir = evidence / "raw_pages" / code[:6]
    if layout is not None:
        raw_dir /= layout
    page_count, page_sha = _page_tree(raw_dir, recursive=layout is not None)
    return all((
        payload.get("start") == start.isoformat(), payload.get("end") == end.isoformat(),
        payload.get("normalized_sha256") == _sha(normalized.read_bytes()),
        payload.get("pages") == page_count,
        payload.get("raw_pages_sha256") == page_sha,
    ))


def collect_all(routes: list[str], org_map: dict[str, str], evidence: Path,
                start: dt.date, end: dt.date, poster=cninfo._http_post) -> dict:
    missing = [code for code in routes if code[:6] not in org_map]
    if missing:
        raise RuntimeError(f"官方orgId映射缺 {len(missing)} 票，首个={missing[0]}")
    for position, ts_code in enumerate(routes, start=1):
        if _done_valid(evidence, ts_code, start, end):
            continue
        marker = evidence / "done" / f"{ts_code}.json"
        normalized = evidence / "normalized" / f"{ts_code}.json"
        if marker.exists() or normalized.exists():
            raise RuntimeError(f"{ts_code} 已有完成件但校验失败，拒绝覆盖")
        try:
            rows, audit = collect_code(ts_code[:6], org_map[ts_code[:6]], start, end,
                                       evidence / "raw_pages", poster)
            digest = _atomic_json(evidence / "normalized" / f"{ts_code}.json", rows)
            _atomic_json(evidence / "done" / f"{ts_code}.json",
                         {"ts_code": ts_code, "start": start.isoformat(),
                          "end": end.isoformat(), "normalized_sha256": digest, **audit})
            print(f"[{position}/{len(routes)}] {ts_code} rows={len(rows)}", flush=True)
        except Exception as error:
            _append_jsonl(evidence / "errors.jsonl", {
                "ts_code": ts_code, "error_type": type(error).__name__, "error": str(error)})
            raise
    return finalize(routes, evidence, start, end)


def finalize(routes: list[str], evidence: Path, start: dt.date, end: dt.date) -> dict:
    if any(not _done_valid(evidence, code, start, end) for code in routes):
        raise RuntimeError("路由全集尚未完成或done marker校验失败")
    index_path = evidence / "announcement_index.jsonl"
    candidates_path = evidence / "candidate_index.jsonl"
    counts: Counter[str] = Counter()
    with index_path.open("w", encoding="utf-8") as index, \
            candidates_path.open("w", encoding="utf-8") as candidates:
        for code in routes:
            rows = json.loads((evidence / "normalized" / f"{code}.json").read_text())
            for row in rows:
                line = json.dumps({"ts_code": code, **row}, ensure_ascii=False,
                                  sort_keys=True, separators=(",", ":")) + "\n"
                index.write(line); counts["announcements"] += 1
                counts[f"year_{row['announcement_date_cn'][:4]}"] += 1
                if ROLE_RE.search(row["title"]):
                    candidates.write(line); counts["wide_recall"] += 1
    manifest = {
        "artifact_status": "COMPLETE_METADATA_INDEX_NOT_EXP22_EVENTS",
        "route_count": len(routes), "start": start, "end": end,
        "counts": dict(sorted(counts.items())),
        "announcement_index_sha256": _sha(index_path.read_bytes()),
        "candidate_index_sha256": _sha(candidates_path.read_bytes()),
        "title_is_recall_only": True, "e1_gate_closed": False,
    }
    _atomic_json(evidence / "manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--routes", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--start", default="1991-01-01")
    parser.add_argument("--end", default="2024-06-30")
    args = parser.parse_args()
    routes = load_routes(Path(args.routes))
    org_map = load_org_map()
    result = collect_all(routes, org_map, Path(args.evidence),
                         dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
