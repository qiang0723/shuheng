#!/usr/bin/env python3
"""exp18 冻结前硬门：用巨潮公告与 PDF 抽核 fina_audit 首次披露语义。"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row
from pypdf import PdfReader

from qbase.ingest import cninfo
from qbase.ingest.seed_fina_audit import SOURCE, load_env

TARGET = ("保留意见", "无法表示意见", "否定意见")
SHANGHAI = ZoneInfo("Asia/Shanghai")
REVISION_WORDS = ("更正", "修订", "更新", "补充")
NON_DOCUMENT_WORDS = ("摘要", "提示性公告", "披露时间", "预约", "问询", "回复", "说明", "取消")


def normalized_title(title: str) -> str:
    return re.sub(r"\s+", "", title or "")


def matches_report_year(title: str, year: int) -> bool:
    text = normalized_title(title)
    return (f"{year}年" in text or f"{year}年度" in text) \
        and ("年度报告" in text or "审计报告" in text)


def is_revision_title(title: str, year: int) -> bool:
    text = normalized_title(title)
    return matches_report_year(text, year) and any(word in text for word in REVISION_WORDS)


def is_initial_document_title(title: str, year: int) -> bool:
    text = normalized_title(title)
    return matches_report_year(text, year) \
        and not any(word in text for word in REVISION_WORDS + NON_DOCUMENT_WORDS)


def announcement_date(record: dict) -> date | None:
    value = record.get("valid_time")
    return value.astimezone(SHANGHAI).date() if value else None


def load_candidates(dsn: str) -> list[dict]:
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on",
                         row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("""
            WITH grouped AS (
              SELECT ts_code,end_date,count(*) AS n,
                     count(*) FILTER (WHERE ann_date IS NULL OR audit_result IS NULL
                                      OR btrim(audit_result)='') AS missing_n,
                     min(ann_date) AS ann_date,min(audit_result) AS audit_result
              FROM public.fina_audit_snap
              WHERE batch_id=(SELECT max(batch_id) FROM public.fact_batch WHERE source=%s)
                AND to_char(end_date,'MMDD')='1231'
                AND ann_date>=DATE '2011-01-01' AND ann_date<DATE '2024-07-01'
                AND ts_code !~ '\\.BJ$'
              GROUP BY 1,2
            )
            SELECT ts_code,ann_date,end_date,audit_result FROM grouped
            WHERE n=1 AND missing_n=0 AND audit_result=ANY(%s)
            ORDER BY audit_result,ann_date,ts_code
        """, (SOURCE, list(TARGET)))
        return [dict(row) for row in cur.fetchall()]


def evenly_spaced(items: list[dict], limit: int) -> list[dict]:
    if len(items) <= limit:
        return items
    if limit == 1:
        return [items[len(items) // 2]]
    indices = {round(i * (len(items) - 1) / (limit - 1)) for i in range(limit)}
    return [items[index] for index in sorted(indices)]


def stratified_sample(candidates: list[dict], per_opinion: int) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for candidate in candidates:
        groups[candidate["audit_result"]].append(candidate)
    return [item for opinion in TARGET
            for item in evenly_spaced(groups.get(opinion, []), per_opinion)]


def select_document(announcements: list[dict], year: int) -> tuple[dict | None, list[dict]]:
    initial = [item for item in announcements if is_initial_document_title(item["title"], year)]
    revisions = [item for item in announcements if is_revision_title(item["title"], year)]
    if not initial:
        return None, revisions
    earliest = min(announcement_date(item) for item in initial if announcement_date(item))
    same_day = [item for item in initial if announcement_date(item) == earliest]
    same_day.sort(key=lambda item: ("审计报告" not in item["title"], item["title"]))
    return same_day[0], revisions


def download_pdf(record: dict, pdf_dir: Path) -> tuple[Path, str]:
    if not record.get("source_url") or not record.get("announcement_id"):
        raise RuntimeError("公告缺 source_url 或 announcement_id")
    path = pdf_dir / f"{record['announcement_id']}.pdf"
    if not path.exists():
        payload = cninfo._http_get(record["source_url"], timeout=40)  # 官方静态文件，承既有采集件
        if not payload.startswith(b"%PDF"):
            raise RuntimeError(f"{record['announcement_id']} 返回非PDF")
        path.write_bytes(payload)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def extract_text(path: Path) -> tuple[str, int]:
    reader = PdfReader(io.BytesIO(path.read_bytes()))
    texts = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(texts), len(reader.pages)


def audit_candidate(candidate: dict, evidence: Path) -> dict:
    start = candidate["end_date"] + timedelta(days=1)
    end = candidate["ann_date"] + timedelta(days=365)
    announcements = cninfo.fetch_announcements(candidate["ts_code"][:6], start, end, category="")
    metadata_path = evidence / "announcement_metadata" / f"{candidate['ts_code']}_{candidate['end_date']}.json"
    metadata_path.write_text(json.dumps(announcements, ensure_ascii=False, indent=1,
                                        default=str, sort_keys=True) + "\n", encoding="utf-8")
    document, revisions = select_document(announcements, candidate["end_date"].year)
    result = {
        **candidate,
        "announcement_count": len(announcements),
        "initial_document_found": document is not None,
        "revision_titles": [{"date": announcement_date(item), "title": item["title"],
                             "source_url": item["source_url"]} for item in revisions],
    }
    if document is None:
        return result
    path, pdf_sha = download_pdf(document, evidence / "pdf")
    content, pages = extract_text(path)
    compact_content = re.sub(r"\s+", "", content)
    source_date = announcement_date(document)
    result.update({
        "source_announcement_id": document["announcement_id"],
        "source_title": document["title"],
        "source_date": source_date,
        "source_url": document["source_url"],
        "source_pdf_sha256": pdf_sha,
        "source_pdf_pages": pages,
        "ann_date_matches_first_document": source_date == candidate["ann_date"],
        "initial_pdf_contains_audit_result": candidate["audit_result"] in compact_content,
    })
    return result


def json_ready(value):
    if isinstance(value, (date,)):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def run(dsn: str, evidence: Path, per_opinion: int) -> dict:
    (evidence / "announcement_metadata").mkdir(parents=True, exist_ok=True)
    (evidence / "pdf").mkdir(parents=True, exist_ok=True)
    candidates = load_candidates(dsn)
    sample = stratified_sample(candidates, per_opinion)
    results = []
    for position, candidate in enumerate(sample, start=1):
        print(f"audit {position}/{len(sample)} {candidate['ts_code']} {candidate['end_date']}", flush=True)
        results.append(audit_candidate(candidate, evidence))
    failures = [item for item in results if not item.get("ann_date_matches_first_document")
                or not item.get("initial_pdf_contains_audit_result")]
    return {
        "source": "CNINFO official announcement metadata and original PDF",
        "selection": "each available target opinion, chronologically evenly spaced",
        "target_opinions": TARGET,
        "candidate_count": len(candidates),
        "sample_count": len(sample),
        "per_opinion_limit": per_opinion,
        "pass_count": len(results) - len(failures),
        "failure_count": len(failures),
        "hard_gate": "PASS" if results and not failures else "FAIL",
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--env", default="/opt/quant/.env")
    parser.add_argument("--per-opinion", type=int, default=8)
    args = parser.parse_args()
    env = load_env(args.env)
    if not env.get("QBASE_APP_DSN"):
        raise RuntimeError("缺QBASE_APP_DSN（不回显值）")
    evidence = Path(args.evidence)
    evidence.mkdir(parents=True, exist_ok=True)
    payload = run(env["QBASE_APP_DSN"], evidence, args.per_opinion)
    output = evidence / "fina_audit_disclosure_audit.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=1,
                                 default=json_ready, sort_keys=True) + "\n", encoding="utf-8")
    print(f"hard_gate={payload['hard_gate']} pass={payload['pass_count']}/{payload['sample_count']}")
    return 0 if payload["hard_gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
