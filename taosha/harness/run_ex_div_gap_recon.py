"""exp14 冻结前只读数据对账；不加载引擎、不读取收益、不要求PAP frozen。"""
from __future__ import annotations

import argparse
import hashlib
import json

from taosha.compute.ex_div_gap_rules import (
    finalize_events, prepare_events, required_factor_keys,
)
from taosha.reader.ex_div_gap import ExDivGapReader


SOURCE_SNAPSHOT_ID = 375
DRAFT_DIGEST = "b2fa1b227db7e4c8a24e18ac3d3db33796b37d393863182719ad6d00459e7d77"
EXPECTED_BATCHES = {"dividend": 17, "adj_factor": 7, "trade_cal": 10}
EXPECTED_VIEW_BATCHES = {
    "dividend": "batch17", "factor": "batch7",
}


def _canonical(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), default=str) + "\n").encode()


def _selection_digest(selection: dict) -> str:
    return hashlib.sha256(_canonical(selection)).hexdigest()


def _assert_snapshot(info: dict) -> None:
    qbase = (info.get("content") or {}).get("qbase") or {}
    mismatches = {key: {"expected": value, "got": qbase.get(key)}
                  for key, value in EXPECTED_BATCHES.items() if qbase.get(key) != value}
    if info.get("snapshot_id") != SOURCE_SNAPSHOT_ID or mismatches:
        raise SystemExit(f"fail-closed: exp14 source snapshot375向量不符:{mismatches}")


def _run_mode(mode: str) -> dict:
    reader = ExDivGapReader(SOURCE_SNAPSHOT_ID, mode)
    if reader.read_only_status() != "on":
        raise SystemExit(f"fail-closed: exp14 {mode}连接不是transaction_read_only=on")
    info = reader.snapshot_info
    _assert_snapshot(info)
    source_batches = reader.source_batches()
    if source_batches != EXPECTED_VIEW_BATCHES:
        raise SystemExit(f"fail-closed: exp14 {mode}视图批次不符:{source_batches}")
    dividend = reader.dividend_rows()
    calendar = reader.calendar_dates()
    prepared = prepare_events(dividend)
    factor_keys = required_factor_keys(prepared, calendar)
    factors = reader.factor_rows(factor_keys)
    selection = finalize_events(prepared, factors, calendar)
    return {
        "mode": mode, "transaction_read_only": "on", "source_snapshot": info,
        "source_batches": source_batches,
        "input": {"dividend_rows": len(dividend), "calendar_dates": len(calendar),
                  "factor_keys_requested": len(factor_keys),
                  "factor_rows_returned": len(factors)},
        "selection": selection, "selection_content_sha256": _selection_digest(selection),
    }


def _assert_equal(current: dict, snapshot: dict) -> None:
    if current["source_batches"] != snapshot["source_batches"]:
        raise SystemExit("fail-closed: exp14 current与snapshot375视图批次不一致")
    current_selection = _canonical(current["selection"])
    snapshot_selection = _canonical(snapshot["selection"])
    if current_selection != snapshot_selection:
        raise SystemExit(
            "fail-closed: exp14 current与snapshot375选择不一致"
            f"({current['selection_content_sha256']}!={snapshot['selection_content_sha256']})")


def _write(path: str, payload: dict) -> None:
    raw = json.dumps(payload, ensure_ascii=False, indent=2,
                     sort_keys=True, default=str) + "\n"
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(raw)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-id", type=int, required=True)
    parser.add_argument("--pap-sha256-assert", required=True)
    parser.add_argument("--json", required=True)
    args = parser.parse_args()
    if args.snapshot_id != SOURCE_SNAPSHOT_ID:
        raise SystemExit("exp14数据对账只允许source snapshot375")
    if args.pap_sha256_assert != DRAFT_DIGEST:
        raise SystemExit("exp14 NOT-FROZEN草案digest断言不符")
    current, snapshot = _run_mode("current"), _run_mode("snapshot")
    _assert_equal(current, snapshot)
    payload = {
        "mode": "pre_freeze_data_reconciliation", "not_for_verdict": True,
        "pap_status": "NOT-FROZEN", "draft_digest": DRAFT_DIGEST,
        "current": current, "snapshot": snapshot,
        "current_snapshot_exact_match": True,
    }
    _write(args.json, payload)
    counters = snapshot["selection"]["counters"]
    print(json.dumps({"events": counters["final_events"],
                      "selection_sha256": snapshot["selection"]["selection_sha256"],
                      "selection_content_sha256": snapshot["selection_content_sha256"],
                      "current_snapshot_exact_match": True}, sort_keys=True))


if __name__ == "__main__":
    main()
