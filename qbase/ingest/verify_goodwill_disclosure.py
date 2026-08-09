#!/usr/bin/env python3
"""exp21 硬门：巨潮原件核首次量化披露、商誉专属金额与PIT归母权益。"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row
from pypdf import PdfReader

from qbase.ingest import cninfo
from qbase.ingest.balancesheet_common import SOURCE, required_env
from qbase.ingest.goodwill_disclosure import (
    amount_evidence, carrier_from_title, has_revision_marker, is_candidate_title,
)

SHANGHAI = ZoneInfo("Asia/Shanghai")


def announcement_date(record: dict) -> date | None:
    value = record.get("valid_time")
    return value.astimezone(SHANGHAI).date() if value else None


def load_locators(dsn: str) -> list[dict]:
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on",
                         row_factory=dict_row) as conn:
        rows = conn.execute(
            "SELECT ts_code,end_date,min(ann_date) AS first_locator_date,"
            "max(ann_date) AS last_locator_date,count(*) AS locator_rows "
            "FROM forecast_snap WHERE batch_id=(SELECT max(batch_id) FROM fact_batch "
            "WHERE source='tushare:forecast') AND ann_date<DATE '2024-07-01' "
            "AND ts_code ~ '\\.(SH|SZ)$' AND end_date IS NOT NULL "
            "AND (COALESCE(summary,'') ILIKE '%商誉%' OR COALESCE(change_reason,'') ILIKE '%商誉%') "
            "GROUP BY ts_code,end_date ORDER BY first_locator_date,ts_code,end_date"
        ).fetchall()
    return [dict(row) for row in rows]


def evenly_spaced(rows: list[dict], count: int) -> list[dict]:
    if len(rows) <= count:
        return rows
    indices = {round(i * (len(rows) - 1) / (count - 1)) for i in range(count)}
    return [rows[index] for index in sorted(indices)]


def sample_by_year(rows: list[dict], per_year: int) -> list[dict]:
    groups = defaultdict(list)
    for row in rows:
        groups[row["first_locator_date"].year].append(row)
    return [item for year in sorted(groups) for item in evenly_spaced(groups[year], per_year)]


def fetch_documents(candidate: dict, evidence: Path) -> list[dict]:
    start = candidate["end_date"] + timedelta(days=1)
    end = candidate["last_locator_date"]
    records = cninfo.fetch_announcements(candidate["ts_code"][:6], start, end, category="")
    target = evidence / "announcement_metadata" / f"{candidate['ts_code']}_{candidate['end_date']}.json"
    target.write_text(json.dumps(records, ensure_ascii=False, indent=1, default=str,
                                 sort_keys=True) + "\n", encoding="utf-8")
    return [row for row in records if announcement_date(row) and is_candidate_title(row["title"])]


def download_pages(document: dict, pdf_dir: Path) -> tuple[list[str], dict]:
    if not document.get("source_url") or not document.get("announcement_id"):
        raise RuntimeError("公告缺source_url或announcement_id")
    path = pdf_dir / f"{document['announcement_id']}.pdf"
    if not path.exists():
        payload = cninfo._http_get(document["source_url"], timeout=40)
        if not payload.startswith(b"%PDF"):
            raise RuntimeError(f"{document['announcement_id']}返回非PDF")
        path.write_bytes(payload)
    payload = path.read_bytes()
    reader = PdfReader(io.BytesIO(payload))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return pages, {"pdf_sha256": hashlib.sha256(payload).hexdigest(),
                   "pdf_pages": len(pages)}


def audit_document(document: dict, evidence: Path) -> dict:
    pages, meta = download_pages(document, evidence / "pdf")
    page_proofs = []
    for number, text in enumerate(pages, start=1):
        proof = amount_evidence(text)
        if proof["status"] != "not_quantified":
            page_proofs.append({"page": number, **proof})
    qualified = [item for item in page_proofs if item["status"] == "qualified"]
    signatures = {(item["selected"]["low_cny"], item["selected"]["high_cny"])
                  for item in qualified}
    status = "qualified" if len(signatures) == 1 else (
        "amount_conflict" if len(signatures) > 1 else
        (page_proofs[0]["status"] if page_proofs else "not_quantified")
    )
    selected = qualified[0]["selected"] if status == "qualified" else None
    return {"announcement_id": document["announcement_id"], "title": document["title"],
            "source_url": document["source_url"], "source_date": announcement_date(document),
            "carrier": carrier_from_title(document["title"]),
            "revision_marker": has_revision_marker(document["title"], "\n".join(pages)),
            "amount_status": status, "selected_amount": selected,
            "page_evidence": page_proofs, **meta}


def denominator_evidence(dsn: str, ts_code: str, event_date: date) -> dict:
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on",
                         row_factory=dict_row) as conn:
        rows = conn.execute(
            "SELECT ann_date,f_ann_date,end_date,report_type,update_flag,"
            "total_hldr_eqy_exc_min_int FROM balancesheet_pit_snap "
            "WHERE batch_id=(SELECT max(batch_id) FROM fact_batch WHERE source=%s) "
            "AND ts_code=%s AND COALESCE(f_ann_date,ann_date)<%s "
            "ORDER BY COALESCE(f_ann_date,ann_date) DESC,end_date DESC", (SOURCE, ts_code, event_date)
        ).fetchall()
    if not rows:
        return {"status": "missing_prior_report"}
    latest_date = rows[0]["f_ann_date"] or rows[0]["ann_date"]
    latest = [dict(row) for row in rows if (row["f_ann_date"] or row["ann_date"]) == latest_date]
    signatures = {(row["end_date"], row["report_type"], row["update_flag"],
                   row["total_hldr_eqy_exc_min_int"]) for row in latest}
    if len(signatures) != 1:
        return {"status": "version_unresolvable", "disclosure_date": latest_date,
                "row_count": len(latest)}
    value = latest[0]["total_hldr_eqy_exc_min_int"]
    status = "qualified" if value and value > 0 else (
        "missing" if value is None else "zero" if value == 0 else "negative"
    )
    return {"status": status, "disclosure_date": latest_date,
            "end_date": latest[0]["end_date"], "report_type": latest[0]["report_type"],
            "update_flag": latest[0]["update_flag"], "equity_cny": value}


def audit_candidate(candidate: dict, dsn: str, evidence: Path) -> dict:
    documents = fetch_documents(candidate, evidence)
    attempts = [audit_document(document, evidence) for document in documents]
    qualified = sorted((item for item in attempts if item["amount_status"] == "qualified"),
                       key=lambda item: (item["source_date"], item["announcement_id"]))
    if not qualified:
        return {**candidate, "documents": attempts, "status": "amount_unproven"}
    first = qualified[0]
    revision_ok = all(item["revision_marker"] for item in qualified[1:])
    if not revision_ok:
        return {**candidate, "documents": attempts, "status": "revision_chain_unproven"}
    denominator = denominator_evidence(dsn, candidate["ts_code"], first["source_date"])
    if denominator["status"] != "qualified":
        return {**candidate, "documents": attempts, "first_qualified": first,
                "denominator": denominator, "status": f"denominator_{denominator['status']}"}
    ratio = first["selected_amount"]["low_cny"] / denominator["equity_cny"]
    return {**candidate, "documents": attempts, "first_qualified": first,
            "denominator": denominator, "ratio_lower_bound": ratio,
            "threshold_qualified": ratio >= Decimal("0.05"), "status": "proven"}


def json_default(value):
    if isinstance(value, (date, Decimal)):
        return str(value)
    raise TypeError(type(value).__name__)


def checkpoint_rows(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    rows = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        item = json.loads(raw)
        key = f"{item['ts_code']}|{item['end_date']}"
        if key in rows:
            raise RuntimeError(f"证据断点重复：{key}")
        rows[key] = item
    return rows


def append_checkpoint(path: Path, item: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False, separators=(",", ":"),
                                default=json_default) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def run(dsn: str, evidence: Path, per_year: int, all_candidates: bool) -> dict:
    (evidence / "announcement_metadata").mkdir(parents=True, exist_ok=True)
    (evidence / "pdf").mkdir(parents=True, exist_ok=True)
    locators = load_locators(dsn)
    selected = locators if all_candidates else sample_by_year(locators, per_year)
    checkpoint = evidence / "goodwill_disclosure_results.jsonl"
    results = checkpoint_rows(checkpoint)
    for index, candidate in enumerate(selected, start=1):
        key = f"{candidate['ts_code']}|{candidate['end_date']}"
        if key not in results:
            print(f"audit={index}/{len(selected)} {key}", flush=True)
            item = audit_candidate(candidate, dsn, evidence)
            append_checkpoint(checkpoint, item)
            results[key] = json.loads(json.dumps(item, default=json_default))
    ordered = [results[f"{item['ts_code']}|{item['end_date']}"] for item in selected]
    statuses = Counter(item["status"] for item in ordered)
    by_year = defaultdict(Counter)
    for item in ordered:
        by_year[str(item["first_locator_date"])[:4]][item["status"]] += 1
    passed = statuses["proven"]
    return {"source": "CNINFO official metadata and original PDF body",
            "locator_limit": "forecast goodwill text is recall-only, not event or coverage evidence",
            "mode": "all" if all_candidates else "yearly_sample", "locator_groups": len(locators),
            "tested_count": len(ordered), "proven_count": passed,
            "failure_count": len(ordered) - passed, "status_counts": dict(sorted(statuses.items())),
            "by_year": {year: dict(sorted(values.items())) for year, values in sorted(by_year.items())},
            "evidence_status": "PASS" if ordered and passed == len(ordered) else "FAIL",
            "results": ordered}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--per-year", type=int, default=2)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    evidence = Path(args.evidence)
    dsn = required_env("QBASE_APP_DSN")["QBASE_APP_DSN"]
    payload = run(dsn, evidence, args.per_year, args.all)
    (evidence / "goodwill_disclosure_audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True,
                   default=json_default) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: payload[key] for key in (
        "mode", "locator_groups", "tested_count", "proven_count",
        "failure_count", "evidence_status")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
