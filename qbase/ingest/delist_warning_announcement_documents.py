#!/usr/bin/env python3
"""exp22 公告宽召回原件物化；标题只作路由，不判事件。"""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

from qbase.ingest import cninfo
from qbase.ingest.delist_warning_announcement_index import _atomic_json, _sha


def fetch_document(url: str) -> tuple[int, str, bytes]:
    def attempt() -> tuple[int, str, bytes]:
        cninfo._throttle()
        request = urllib.request.Request(url, headers={"User-Agent": cninfo.UA})
        with urllib.request.urlopen(request, timeout=40) as response:
            return response.status, response.headers.get_content_type(), response.read()
    return cninfo._retry(attempt, f"GET {url}")


def materialize_documents(evidence: Path, getter=fetch_document) -> dict:
    rows = [json.loads(line) for line in
            (evidence / "candidate_index.jsonl").read_text(encoding="utf-8").splitlines()]
    by_id: dict[str, list[dict]] = {}
    for row in rows:
        by_id.setdefault(row["announcement_id"], []).append(row)
    manifest_rows = []
    errors = []
    documents = evidence / "documents"
    documents.mkdir(parents=True, exist_ok=True)
    for announcement_id in sorted(by_id):
        group = by_id[announcement_id]
        urls = {row.get("source_url") for row in group}
        if None in urls or len(urls) != 1:
            raise RuntimeError(f"公告 {announcement_id} 原件URL缺失或冲突")
        try:
            status, content_type, payload = getter(next(iter(urls)))
            if payload.startswith(b"%PDF"):
                suffix, media = ".pdf", "application/pdf"
            elif b"<html" in payload[:1024].lower():
                suffix, media = ".html", "text/html"
            else:
                raise RuntimeError("返回未知媒体")
        except Exception as error:
            errors.append({"announcement_id": announcement_id,
                           "source_url": next(iter(urls)),
                           "error_type": type(error).__name__, "error": str(error),
                           "routed_ts_codes": sorted({row["ts_code"] for row in group})})
            continue
        path = documents / f"{announcement_id}{suffix}"
        if path.exists() and path.read_bytes() != payload:
            raise RuntimeError(f"公告 {announcement_id} 已有原件与当前响应不一致")
        if not path.exists():
            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_bytes(payload); tmp.replace(path)
        manifest_rows.append({
            "announcement_id": announcement_id, "source_url": next(iter(urls)),
            "http_status": status, "response_content_type": content_type,
            "stored_media_type": media, "bytes": len(payload),
            "sha256": _sha(payload), "path": str(path.relative_to(evidence)),
            "routed_ts_codes": sorted({row["ts_code"] for row in group}),
        })
    result = {
        "artifact_status": "WIDE_RECALL_DOCUMENTS_NOT_EXP22_EVENTS",
        "title_is_recall_only": True, "documents": manifest_rows,
        "downloaded_count": len(manifest_rows), "failed_count": len(errors),
        "candidate_rows": len(rows), "errors": errors, "e1_gate_closed": False,
    }
    _atomic_json(evidence / "document_manifest.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    args = parser.parse_args()
    result = materialize_documents(Path(args.evidence))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
