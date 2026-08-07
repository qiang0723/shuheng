#!/usr/bin/env python3
"""exp23 硬门：巨潮官方元数据/PDF核首次披露、方案身份与正文用途。"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row
from pypdf import PdfReader

from qbase.ingest import cninfo
from qbase.ingest.repurchase_common import SOURCE, required_env
from qbase.ingest.repurchase_disclosure import document_evidence, is_candidate_title

SHANGHAI = ZoneInfo("Asia/Shanghai")


def announcement_date(record: dict) -> date | None:
    value = record.get("valid_time")
    return value.astimezone(SHANGHAI).date() if value else None


def load_candidates(dsn: str) -> list[dict]:
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on",
                         row_factory=dict_row) as conn:
        rows = conn.execute("""
          WITH src AS (
            SELECT * FROM repurchase_snap
            WHERE batch_id=(SELECT max(batch_id) FROM fact_batch WHERE source=%s)
              AND ann_date<DATE '2024-07-01' AND ts_code !~ '\\.BJ$'
          ), grouped AS (
            SELECT ts_code,ann_date,count(*) AS row_n,
                   count(*) FILTER (WHERE proc='预案') AS proposal_n,
                   min(high_limit) FILTER (WHERE proc='预案') AS high_limit
            FROM src GROUP BY ts_code,ann_date
          )
          SELECT ts_code,ann_date,high_limit FROM grouped
          WHERE row_n=1 AND proposal_n=1
          ORDER BY ann_date,ts_code
        """, (SOURCE,)).fetchall()
    return [dict(row) for row in rows]


def evenly_spaced(rows: list[dict], count: int) -> list[dict]:
    if len(rows) <= count:
        return rows
    indices = {round(i * (len(rows) - 1) / (count - 1)) for i in range(count)}
    return [rows[index] for index in sorted(indices)]


def sample_by_year(rows: list[dict], per_year: int) -> list[dict]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["ann_date"].year].append(row)
    return [item for year in sorted(grouped) for item in evenly_spaced(grouped[year], per_year)]


def fetch_documents(candidate: dict, evidence: Path) -> list[dict]:
    ann = candidate["ann_date"]
    records = cninfo.fetch_announcements(candidate["ts_code"][:6], ann, ann, category="")
    target = evidence / "announcement_metadata" / f"{candidate['ts_code']}_{ann}.json"
    target.write_text(json.dumps(records, ensure_ascii=False, indent=1, default=str,
                                 sort_keys=True) + "\n", encoding="utf-8")
    return [row for row in records if announcement_date(row) == ann
            and is_candidate_title(row["title"])]


def download_text(document: dict, pdf_dir: Path) -> tuple[str, dict]:
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
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    return text, {"pdf_sha256": hashlib.sha256(payload).hexdigest(),
                  "pdf_pages": len(reader.pages)}


def audit_candidate(candidate: dict, evidence: Path) -> dict:
    documents = fetch_documents(candidate, evidence)
    attempts = []
    for document in documents:
        text, meta = download_text(document, evidence / "pdf")
        proof = document_evidence(text, candidate["high_limit"])
        attempts.append({"announcement_id": document["announcement_id"],
                         "title": document["title"], "source_url": document["source_url"],
                         "source_date": announcement_date(document), **proof, **meta})
    passed = [item for item in attempts if item["first_disclosure_supported"]
              and item["scheme_identity_supported"]
              and item["purpose"]["category"] != "unclassifiable"]
    categories = sorted({item["purpose"]["category"] for item in passed})
    return {**candidate, "candidate_documents_on_ann_date": len(documents),
            "attempts": attempts, "pass": len(categories) == 1,
            "purpose_category": categories[0] if len(categories) == 1 else "unclassifiable"}


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
        key = f"{item['ts_code']}|{item['ann_date']}"
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


def run(dsn: str, evidence: Path, per_year: int, all_candidates: bool,
        study_start: date) -> dict:
    (evidence / "announcement_metadata").mkdir(parents=True, exist_ok=True)
    (evidence / "pdf").mkdir(parents=True, exist_ok=True)
    candidates = [row for row in load_candidates(dsn) if row["ann_date"] >= study_start]
    selected = candidates if all_candidates else sample_by_year(candidates, per_year)
    checkpoint = evidence / "repurchase_disclosure_results.jsonl"
    results = checkpoint_rows(checkpoint)
    for index, candidate in enumerate(selected, start=1):
        key = f"{candidate['ts_code']}|{candidate['ann_date']}"
        if key not in results:
            print(f"audit={index}/{len(selected)} {key}", flush=True)
            item = audit_candidate(candidate, evidence)
            append_checkpoint(checkpoint, item)
            results[key] = json.loads(json.dumps(item, default=json_default))
    ordered = [results[f"{item['ts_code']}|{item['ann_date']}"] for item in selected]
    by_year, purpose = {}, Counter(item["purpose_category"] for item in ordered)
    for year in sorted({str(item["ann_date"])[:4] for item in ordered}):
        subset = [item for item in ordered if str(item["ann_date"]).startswith(year)]
        by_year[year] = {"sample": len(subset), "pass": sum(item["pass"] for item in subset)}
    passed = sum(item["pass"] for item in ordered)
    return {"source": "CNINFO official metadata and original PDF body",
            "mode": "all" if all_candidates else "yearly_sample",
            "study_start_evidence_scope": study_start,
            "candidate_count": len(candidates), "tested_count": len(ordered),
            "pass_count": passed, "failure_count": len(ordered) - passed,
            "evidence_status": "PASS" if ordered and passed == len(ordered) else "FAIL",
            "purpose_composition_nfv": dict(sorted(purpose.items())),
            "by_year": by_year, "results": ordered}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--per-year", type=int, default=2)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--study-start", default="2011-01-01")
    args = parser.parse_args()
    evidence = Path(args.evidence)
    payload = run(required_env("QBASE_APP_DSN")["QBASE_APP_DSN"], evidence,
                  args.per_year, args.all, date.fromisoformat(args.study_start))
    (evidence / "repurchase_disclosure_audit.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True,
                   default=json_default) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: payload[key] for key in (
        "mode", "candidate_count", "tested_count", "pass_count",
        "failure_count", "evidence_status")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
