#!/usr/bin/env python3
"""exp22 公告元数据全集的分层独立二次读回；只读官方接口。"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from qbase.ingest import delist_warning_announcement_index as indexer


def _board(code: str) -> str:
    prefix = code[:3]
    if prefix == "688":
        return "SSE_STAR"
    if prefix == "300":
        return "SZSE_CHINEXT"
    if prefix == "002":
        return "SZSE_FORMER_SME"
    return "SSE_MAIN" if code.endswith(".SH") else "SZSE_MAIN"


def select_codes(route_payload: dict, count: int) -> list[str]:
    routes = route_payload.get("routes") or []
    events = route_payload.get("events") or []
    if count < 12 or routes != sorted(set(routes)):
        raise ValueError("读回至少12票且routes须排序唯一")
    strata: dict[tuple[str, str, str], set[str]] = {}
    for event in events:
        code = event.get("ts_code")
        day = str(event.get("ann_date") or "")
        if code not in routes or len(day) < 4:
            raise ValueError("route event身份或日期非法")
        key = (code[-2:], _board(code), day[:4])
        strata.setdefault(key, set()).add(code)
    selected: list[str] = []
    for key in sorted(strata):
        for code in sorted(strata[key]):
            if code not in selected:
                selected.append(code)
                break
        if len(selected) == count:
            break
    for code in routes:
        if len(selected) == count:
            break
        if code not in selected:
            selected.append(code)
    if len(selected) < count:
        raise RuntimeError("路由全集不足读回票数")
    return selected


def compare_rows(primary: list[dict], readback: list[dict], code: str) -> dict:
    primary_ids = [row["announcement_id"] for row in primary]
    readback_ids = [row["announcement_id"] for row in readback]
    checks = {
        "announcement_id_set_equal": set(primary_ids) == set(readback_ids),
        "announcement_id_order_equal": primary_ids == readback_ids,
        "normalized_rows_equal": primary == readback,
    }
    if not all(checks.values()):
        raise RuntimeError(f"{code} 独立读回与主索引不等: {checks}")
    return {"ts_code": code, "announcement_count": len(primary), "checks": checks}


def run(routes_path: Path, evidence: Path, count: int,
        poster=indexer.cninfo._http_post) -> dict:
    route_payload = json.loads(routes_path.read_text(encoding="utf-8"))
    selected = select_codes(route_payload, count)
    manifest = json.loads((evidence / "manifest.json").read_text(encoding="utf-8"))
    start = dt.date.fromisoformat(manifest["start"])
    end = dt.date.fromisoformat(manifest["end"])
    org_map = indexer.load_org_map()
    audits = []
    for code in selected:
        primary = json.loads((evidence / "normalized" / f"{code}.json").read_text())
        rows, api = indexer.collect_code(
            code[:6], org_map[code[:6]], start, end,
            evidence / "readback" / "raw_pages", poster)
        audits.append({**compare_rows(primary, rows, code), "api": api,
                       "exchange": code[-2:], "historical_board": _board(code)})
    payload = {
        "artifact_status": "INDEPENDENT_READBACK_NOT_EXP22_EVENTS",
        "sample_count": len(selected), "selected_codes": selected,
        "all_equal": True, "audits": audits,
    }
    data = (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode()
    output = evidence / "readback" / "readback_result.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    payload["sha256"] = hashlib.sha256(data).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--routes", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--count", type=int, default=12)
    args = parser.parse_args()
    result = run(Path(args.routes), Path(args.evidence), args.count)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
