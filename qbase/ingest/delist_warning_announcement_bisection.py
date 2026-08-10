#!/usr/bin/env python3
"""exp22 公告元数据日期二分读取；只负责确定性分片与双读一致性。"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class LeafAudit:
    start: str
    end: str
    rows: int
    api_totals: tuple[int, ...]
    pass_pages: tuple[int, int]
    pass_api_totals: tuple[tuple[int, ...], tuple[int, ...]]


MAX_DAY_PAGES = 100


class _LeafMismatch(RuntimeError):
    """仅标记可用日期二分继续定位的双读漂移。"""


def _row_key(row: dict) -> tuple[str, str, str]:
    return (row["announcement_date_cn"], row["valid_time_utc"],
            row["announcement_id"])


def _canonical(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=_row_key)


def _path(root: Path, start: dt.date, end: dt.date,
          read: str, page: int = 1) -> Path:
    return (root / f"{start.isoformat()}_{end.isoformat()}" / read /
            f"{page:05d}.json")


def _split(start: dt.date, end: dt.date) -> tuple[tuple[dt.date, dt.date],
                                                   tuple[dt.date, dt.date]]:
    midpoint = start + dt.timedelta(days=(end - start).days // 2)
    return (start, midpoint), (midpoint + dt.timedelta(days=1), end)


def _leaf(code: str, start: dt.date, end: dt.date, request: dict,
          probe_rows: list[dict], probe_total: int | None, root: Path,
          poster, fetch, validate, page_size: int) -> tuple[list[dict], LeafAudit, int]:
    response = fetch(_path(root, start, end, "pass_b"), request, poster)
    confirm_rows, confirm_more, confirm_total = validate(code, response, start, end)
    if confirm_more and len(confirm_rows) != page_size:
        raise RuntimeError(f"{code}/{start}..{end}/pass_b 非终页行数不满")
    if confirm_more:
        raise _LeafMismatch(f"{code}/{start}..{end} 双读分页状态不一致")
    first, second = _canonical(probe_rows), _canonical(confirm_rows)
    if first != second:
        raise _LeafMismatch(f"{code}/{start}..{end} 双读规范化行不一致")
    totals = tuple(sorted({x for x in (probe_total, confirm_total) if x is not None}))
    if totals and len(first) not in totals:
        raise RuntimeError(f"{code}/{start}..{end} 行数未命中API观测总数")
    pass_totals = ((probe_total,) if probe_total is not None else (),
                   (confirm_total,) if confirm_total is not None else ())
    audit = LeafAudit(start.isoformat(), end.isoformat(), len(first), totals,
                      (1, 1), pass_totals)
    return first, audit, 1


def _scan_day(code: str, org_id: str, day: dt.date, root: Path, label: str,
              poster, request_fn: Callable, fetch: Callable, validate: Callable,
              page_size: int, first_response=None) -> tuple[list[dict], tuple[int, ...], int]:
    rows: list[dict] = []
    ids: set[str] = set()
    totals: list[int] = []
    for page in range(1, MAX_DAY_PAGES + 1):
        request = request_fn(code, org_id, day, day, page)
        response = first_response if page == 1 and first_response is not None else fetch(
            _path(root, day, day, label, page), request, poster)
        current, has_more, total = validate(code, response, day, day)
        current_ids = {row["announcement_id"] for row in current}
        if ids.intersection(current_ids):
            raise RuntimeError(f"{code}/{day}/{label} 跨页公告ID重复")
        if has_more and len(current) != page_size:
            raise RuntimeError(f"{code}/{day}/{label} 非终页行数不满")
        ids.update(current_ids); rows.extend(current)
        if total is not None:
            totals.append(total)
        if not has_more:
            if not totals or len(rows) not in totals:
                raise RuntimeError(f"{code}/{day}/{label} 行数未命中API观测总数")
            return _canonical(rows), tuple(totals), page
    raise RuntimeError(f"{code}/{day}/{label} 超过{MAX_DAY_PAGES}页")


def _multi_page_day(code: str, org_id: str, day: dt.date, root: Path,
                    first_response, poster, request_fn: Callable, fetch: Callable,
                    validate: Callable, page_size: int) -> tuple[list[dict], LeafAudit, int]:
    first, totals_a, pages_a = _scan_day(
        code, org_id, day, root, "pass_a", poster, request_fn, fetch, validate,
        page_size, first_response)
    second, totals_b, pages_b = _scan_day(
        code, org_id, day, root, "pass_b", poster, request_fn, fetch, validate, page_size)
    if first != second:
        raise RuntimeError(f"{code}/{day} 双遍规范化全集不一致")
    totals = tuple(sorted(set(totals_a + totals_b)))
    audit = LeafAudit(day.isoformat(), day.isoformat(), len(first), totals,
                      (pages_a, pages_b), (totals_a, totals_b))
    return first, audit, pages_a + pages_b


def _branches(code: str, org_id: str, start: dt.date, end: dt.date, root: Path,
              poster, request_fn: Callable, fetch: Callable, validate: Callable,
              page_size: int, parent_reads: int):
    left, right = _split(start, end)
    left_rows, left_audit, left_reads = _walk(
        code, org_id, *left, root, poster, request_fn, fetch, validate, page_size)
    right_rows, right_audit, right_reads = _walk(
        code, org_id, *right, root, poster, request_fn, fetch, validate, page_size)
    return (left_rows + right_rows, left_audit + right_audit,
            parent_reads + left_reads + right_reads)


def _walk(code: str, org_id: str, start: dt.date, end: dt.date, root: Path,
          poster, request_fn: Callable, fetch: Callable,
          validate: Callable, page_size: int) -> tuple[list[dict], list[LeafAudit], int]:
    request = request_fn(code, org_id, start, end, 1)
    response = fetch(_path(root, start, end, "pass_a"), request, poster)
    rows, has_more, total = validate(code, response, start, end)
    if not has_more:
        try:
            accepted, audit, confirms = _leaf(
                code, start, end, request, rows, total, root, poster, fetch,
                validate, page_size)
        except _LeafMismatch:
            if start == end:
                raise
            return _branches(
                code, org_id, start, end, root, poster, request_fn, fetch,
                validate, page_size, 2)
        return accepted, [audit], 1 + confirms
    if len(rows) != page_size:
        raise RuntimeError(f"{code}/{start}..{end} 非终页行数不满")
    if start == end:
        accepted, audit, reads = _multi_page_day(
            code, org_id, start, root, response, poster, request_fn, fetch,
            validate, page_size)
        return accepted, [audit], reads
    return _branches(
        code, org_id, start, end, root, poster, request_fn, fetch, validate,
        page_size, 1)


def collect_interval(code: str, org_id: str, start: dt.date, end: dt.date,
                     root: Path, poster, request_fn: Callable, fetch: Callable,
                     validate: Callable, page_size: int) -> tuple[list[dict], dict]:
    """二分到单页叶片，每叶双读；跨叶公告 ID 必须唯一。"""
    rows, audits, reads = _walk(
        code, org_id, start, end, root, poster, request_fn, fetch, validate, page_size)
    rows = _canonical(rows)
    ids = [row["announcement_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"{code}/{start.year} 跨叶片公告ID重复")
    return rows, {
        "raw_reads": reads,
        "leaf_count": len(audits),
        "leaves": [audit.__dict__ for audit in audits],
    }
