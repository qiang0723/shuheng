#!/usr/bin/env python3
"""exp19 冻结硬门：巨潮官方元数据/PDF抽核初始预案日与税前现金分红值。"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row
from pypdf import PdfReader

from qbase.ingest import cninfo
from qbase.ingest.dividend_common import SOURCE, required_env

SHANGHAI = ZoneInfo("Asia/Shanghai")
TITLE_TERMS = (
    "利润分配预案", "分配利润预案", "利润分配方案", "年度利润分配",
    "权益分派预案", "特别分红方案", "年度报告",
)
TITLE_EXCLUDES = (
    "实施", "股东大会", "决议", "修订", "更正", "进展", "取消", "问询", "回复",
    "说明会", "披露提示",
)
CASH_PATTERN = re.compile(
    r"每\s*10\s*股.{0,60}?(?:派发|派送|派|发放|分配)"
    r"(?:现金红利|现金股利|现金)?(?:人民币)?\s*([0-9]+(?:\.[0-9]+)?)\s*元.{0,20}?含税"
)
PER_SHARE_PATTERN = re.compile(
    r"每\s*股.{0,40}?(?:派发|派送|派|发放|分配)"
    r"(?:现金红利|现金股利|现金)?(?:人民币)?\s*([0-9]+(?:\.[0-9]+)?)\s*元.{0,20}?含税"
)


def announcement_date(record: dict) -> date | None:
    value = record.get("valid_time")
    return value.astimezone(SHANGHAI).date() if value else None


def normalized_title(value: str) -> str:
    return re.sub(r"\s+", "", value or "")


def is_proposal_title(title: str) -> bool:
    text = normalized_title(title)
    return any(term in text for term in TITLE_TERMS) and not any(term in text for term in TITLE_EXCLUDES)


def cash_per_ten_values(text: str) -> list[Decimal]:
    compact = re.sub(r"\s+", "", text or "")
    values = []
    for match in CASH_PATTERN.finditer(compact):
        try:
            values.append(Decimal(match.group(1)))
        except InvalidOperation:
            continue
    return values


def cash_per_share_values(text: str) -> list[Decimal]:
    compact = re.sub(r"\s+", "", text or "")
    values = []
    for match in PER_SHARE_PATTERN.finditer(compact):
        try:
            values.append(Decimal(match.group(1)))
        except InvalidOperation:
            continue
    return values


def load_candidates(dsn: str) -> list[dict]:
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on",
                         row_factory=dict_row) as conn:
        rows = conn.execute("""
          WITH src AS (
            SELECT d.* FROM dividend_snap d
            WHERE d.batch_id=(SELECT max(batch_id) FROM fact_batch WHERE source=%s)
              AND d.end_date IS NOT NULL AND to_char(d.end_date,'MMDD')='1231'
              AND d.ann_date<DATE '2024-07-01' AND d.ts_code !~ '\\.BJ$'
          ), grouped AS (
            SELECT ts_code,end_date,
                   count(*) FILTER (WHERE div_proc='预案' AND update_flag='0') AS initial_n,
                   min(ann_date) FILTER (WHERE div_proc='预案' AND update_flag='0') AS ann_date,
                   min(cash_div_tax) FILTER (WHERE div_proc='预案' AND update_flag='0') AS cash_div_tax
            FROM src GROUP BY ts_code,end_date
          )
          SELECT ts_code,end_date,ann_date,cash_div_tax FROM grouped
          WHERE initial_n=1 AND ann_date IS NOT NULL AND cash_div_tax>0
          ORDER BY extract(year FROM ann_date),ann_date,ts_code
        """, (SOURCE,)).fetchall()
    return [dict(row) for row in rows]


def evenly_spaced(rows: list[dict], count: int) -> list[dict]:
    if len(rows) <= count:
        return rows
    indices = {round(i * (len(rows) - 1) / (count - 1)) for i in range(count)}
    return [rows[index] for index in sorted(indices)]


def sample_by_year(rows: list[dict], per_year: int) -> list[dict]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["ann_date"].year].append(row)
    return [item for year in sorted(grouped) for item in evenly_spaced(grouped[year], per_year)]


def fetch_documents(candidate: dict, evidence: Path) -> list[dict]:
    ann = candidate["ann_date"]
    records = cninfo.fetch_announcements(candidate["ts_code"][:6], ann - timedelta(days=2),
                                         ann + timedelta(days=2), category="")
    path = evidence / "announcement_metadata" / f"{candidate['ts_code']}_{candidate['end_date']}.json"
    path.write_text(json.dumps(records, ensure_ascii=False, indent=1, default=str,
                               sort_keys=True) + "\n", encoding="utf-8")
    return [row for row in records if announcement_date(row) == ann and is_proposal_title(row["title"])]


def download_and_extract(document: dict, pdf_dir: Path) -> tuple[str, dict]:
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
    return text, {"pdf_sha256": hashlib.sha256(payload).hexdigest(), "pdf_pages": len(reader.pages)}


def audit_candidate(candidate: dict, evidence: Path) -> dict:
    documents = fetch_documents(candidate, evidence)
    expected_share = candidate["cash_div_tax"]
    expected_ten = expected_share * Decimal(10)
    attempts = []
    for document in documents:
        text, meta = download_and_extract(document, evidence / "pdf")
        per_share = cash_per_share_values(text)
        per_ten = cash_per_ten_values(text)
        attempts.append({
            "announcement_id": document["announcement_id"], "title": document["title"],
            "source_url": document["source_url"], "source_date": announcement_date(document),
            "cash_per_share_values": per_share, "cash_per_ten_values": per_ten,
            "expected_cash_div_tax_per_share": expected_share,
            "exact_value_match": expected_share in per_share or expected_ten in per_ten, **meta,
        })
    passed = [attempt for attempt in attempts if attempt["exact_value_match"]]
    return {**candidate, "proposal_documents_on_ann_date": len(documents),
            "attempts": attempts, "pass": bool(passed)}


def json_default(value):
    if isinstance(value, (date, Decimal)):
        return str(value)
    raise TypeError(type(value).__name__)


def run(dsn: str, evidence: Path, per_year: int) -> dict:
    (evidence / "announcement_metadata").mkdir(parents=True, exist_ok=True)
    (evidence / "pdf").mkdir(parents=True, exist_ok=True)
    candidates = load_candidates(dsn)
    sample = sample_by_year(candidates, per_year)
    results = []
    for index, candidate in enumerate(sample, start=1):
        print(f"audit={index}/{len(sample)} {candidate['ts_code']} {candidate['ann_date']}", flush=True)
        results.append(audit_candidate(candidate, evidence))
    by_year = {}
    for year in sorted({row["ann_date"].year for row in results}):
        items = [row for row in results if row["ann_date"].year == year]
        by_year[str(year)] = {"sample": len(items), "pass": sum(row["pass"] for row in items)}
    passed = sum(row["pass"] for row in results)
    return {
        "source": "CNINFO official metadata and original PDF",
        "test": "ann_date exact-day original document + exact tax-inclusive cash_div_tax in per-share or per-10-share units",
        "candidate_count": len(candidates), "sample_count": len(sample),
        "pass_count": passed, "failure_count": len(sample) - passed,
        "evidence_status": "PASS" if sample and passed == len(sample)
                           else "PARTIAL" if passed else "FAIL",
        "by_year": by_year, "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--per-year", type=int, default=3)
    args = parser.parse_args()
    evidence = Path(args.evidence)
    payload = run(required_env("QBASE_APP_DSN")["QBASE_APP_DSN"], evidence, args.per_year)
    output = evidence / "dividend_disclosure_audit.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True,
                                 default=json_default) + "\n", encoding="utf-8")
    print(json.dumps({key: payload[key] for key in (
        "sample_count", "pass_count", "failure_count", "evidence_status")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
