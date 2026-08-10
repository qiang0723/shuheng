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


def _row_key(row: dict) -> tuple[str, str, str]:
    return (row["announcement_date_cn"], row["valid_time_utc"],
            row["announcement_id"])


def _canonical(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=_row_key)


def _path(root: Path, start: dt.date, end: dt.date, read: str) -> Path:
    return root / f"{start.isoformat()}_{end.isoformat()}" / f"{read}.json"


def _split(start: dt.date, end: dt.date) -> tuple[tuple[dt.date, dt.date],
                                                   tuple[dt.date, dt.date]]:
    midpoint = start + dt.timedelta(days=(end - start).days // 2)
    return (start, midpoint), (midpoint + dt.timedelta(days=1), end)


def _leaf(code: str, start: dt.date, end: dt.date, request: dict,
          probe_rows: list[dict], probe_total: int | None, root: Path,
          poster, fetch, validate) -> tuple[list[dict], LeafAudit, int]:
    response = fetch(_path(root, start, end, "confirm"), request, poster)
    confirm_rows, confirm_more, confirm_total = validate(code, response, start, end)
    if confirm_more:
        raise RuntimeError(f"{code}/{start}..{end} 双读分页状态不一致")
    first, second = _canonical(probe_rows), _canonical(confirm_rows)
    if first != second:
        raise RuntimeError(f"{code}/{start}..{end} 双读规范化行不一致")
    totals = tuple(sorted({x for x in (probe_total, confirm_total) if x is not None}))
    if totals and len(first) not in totals:
        raise RuntimeError(f"{code}/{start}..{end} 行数未命中API观测总数")
    return first, LeafAudit(start.isoformat(), end.isoformat(), len(first), totals), 1


def _walk(code: str, org_id: str, start: dt.date, end: dt.date, root: Path,
          poster, request_fn: Callable, fetch: Callable,
          validate: Callable, page_size: int) -> tuple[list[dict], list[LeafAudit], int]:
    request = request_fn(code, org_id, start, end, 1)
    response = fetch(_path(root, start, end, "probe"), request, poster)
    rows, has_more, total = validate(code, response, start, end)
    if not has_more:
        accepted, audit, confirms = _leaf(
            code, start, end, request, rows, total, root, poster, fetch, validate)
        return accepted, [audit], 1 + confirms
    if len(rows) != page_size:
        raise RuntimeError(f"{code}/{start}..{end} 非终页行数不满")
    if start == end:
        raise RuntimeError(f"{code}/{start} 单日仍超过单页")
    left, right = _split(start, end)
    left_rows, left_audit, left_reads = _walk(
        code, org_id, *left, root, poster, request_fn, fetch, validate, page_size)
    right_rows, right_audit, right_reads = _walk(
        code, org_id, *right, root, poster, request_fn, fetch, validate, page_size)
    return left_rows + right_rows, left_audit + right_audit, 1 + left_reads + right_reads


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
