#!/usr/bin/env python3
"""把宽召回原件映射为证据合同待核队列；不从标题推断正文事实。"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def build_queue(evidence: Path, contract_path: Path) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("artifact_status") != "DRAFT_EVIDENCE_CONTRACT_NOT_FOR_FREEZE":
        raise ValueError("证据合同身份不符")
    candidates = [json.loads(line) for line in
                  (evidence / "candidate_index.jsonl").read_text().splitlines()]
    documents = json.loads((evidence / "document_manifest.json").read_text())
    by_id = {row["announcement_id"]: row for row in documents["documents"]}
    failures = {row["announcement_id"]: row for row in documents["errors"]}
    queue = []
    status_counts: Counter[str] = Counter()
    for row in candidates:
        announcement_id = row["announcement_id"]
        document = by_id.get(announcement_id)
        status = ("UNPROVEN_BODY_CONTRACT_PENDING" if document
                  else "FAIL_ARCHIVE_COMPLETENESS_UNPROVEN")
        status_counts[status] += 1
        queue.append({
            "source_id": f"CNINFO_{announcement_id}", "source_url": row["source_url"],
            "source_content_sha256": document["sha256"] if document else None,
            "announcement_id": announcement_id,
            "announcement_date": row["announcement_date_cn"],
            "ts_code": row["ts_code"], "company_name": row["raw_company_name"],
            "document_title": row["title"], "document_role": None,
            "implementation_effective_date": None, "a1_reason_code": None,
            "a1_financial_years": None, "rule_source_id": None, "rule_clause": None,
            "scheme_id": None, "predecessor_announcement_ids": None,
            "successor_announcement_ids": None, "firstness_proof": None,
            "pass_checks": {name: None for name in
                            contract["contract"]["required_pass_checks"]},
            "contract_status": status, "download_error": failures.get(announcement_id),
        })
    queue.sort(key=lambda row: (row["ts_code"], row["announcement_date"],
                                row["announcement_id"]))
    result = {
        "artifact_status": "CONTRACT_QUEUE_NOT_EXP22_EVENTS",
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "candidate_rows": len(candidates), "queue_rows": len(queue),
        "status_counts": dict(sorted(status_counts.items())),
        "title_is_not_evidence": True, "e1_gate_closed": False, "queue": queue,
    }
    data = (json.dumps(result, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode()
    (evidence / "contract_queue.json").write_bytes(data)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--contract", required=True)
    args = parser.parse_args()
    result = build_queue(Path(args.evidence), Path(args.contract))
    print(json.dumps({key: result[key] for key in (
        "candidate_rows", "queue_rows", "status_counts", "e1_gate_closed")},
        ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
