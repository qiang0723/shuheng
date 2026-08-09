"""exp21 官方公告正文的严格金额证据纯函数；标题仅用于召回与载体标签。"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

REVISION_WORDS = ("更正", "修正", "修订", "补充", "更新")
LOCATOR_WORDS = ("业绩预告", "业绩快报", "年度报告", "商誉", "减值")
NON_DOCUMENT_WORDS = ("摘要", "问询", "回复", "说明会", "风险提示", "审计意见")
COMBINATION_WORDS = ("无形资产", "固定资产", "长期股权投资", "资产组", "其他资产", "资产减值")
UNIT_MULTIPLIER = {
    "元": Decimal(1), "万元": Decimal(10000), "亿元": Decimal(100000000),
}
NUMBER = r"([0-9]+(?:\.[0-9]+)?)"
UNIT = r"(亿元|万元|元)"
PREFIX = r"(?:计提|确认|预计计提|拟计提)?(?:的)?商誉减值(?:准备|损失)?(?:金额)?"
RANGE_PATTERN = re.compile(
    PREFIX + r"(?:约|预计)?(?:为|在)?\s*" + NUMBER + r"\s*" + UNIT
    + r"\s*(?:至|到|—|－|-)\s*" + NUMBER + r"\s*" + UNIT
)
EXACT_PATTERN = re.compile(
    PREFIX + r"(?:约|预计)?(?:为|达|合计为|人民币)?\s*" + NUMBER + r"\s*" + UNIT
)


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value or "")


def carrier_from_title(title: str) -> str:
    text = compact(title)
    if "业绩预告" in text:
        return "forecast"
    if "业绩快报" in text:
        return "express"
    if "年度报告" in text:
        return "annual_report"
    return "special_announcement"


def is_candidate_title(title: str) -> bool:
    text = compact(title)
    return any(word in text for word in LOCATOR_WORDS) \
        and not any(word in text for word in NON_DOCUMENT_WORDS)


def has_revision_marker(title: str, text: str) -> bool:
    return any(word in compact(title) for word in REVISION_WORDS) \
        or any(f"本{word}" in compact(text) for word in REVISION_WORDS)


def decimal_amount(value: str, unit: str) -> Decimal:
    try:
        return Decimal(value) * UNIT_MULTIPLIER[unit]
    except (InvalidOperation, KeyError) as exc:
        raise RuntimeError(f"金额不可解析：{value!r}/{unit!r}") from exc


def combined_context(text: str, start: int, end: int) -> bool:
    context = text[max(0, start - 80):min(len(text), end + 80)]
    return any(word in context for word in COMBINATION_WORDS)


def amount_evidence(text: str) -> dict:
    body = compact(text)
    hits = []
    range_spans = [match.span() for match in RANGE_PATTERN.finditer(body)]
    for kind, pattern in (("range", RANGE_PATTERN), ("exact", EXACT_PATTERN)):
        for match in pattern.finditer(body):
            if kind == "exact" and any(
                    match.start() >= start and match.end() <= end for start, end in range_spans):
                continue
            if combined_context(body, match.start(), match.end()):
                hits.append({"kind": "combined_unseparable", "text": match.group(0)})
                continue
            if kind == "range":
                low = decimal_amount(match.group(1), match.group(2))
                high = decimal_amount(match.group(3), match.group(4))
            else:
                low = high = decimal_amount(match.group(1), match.group(2))
            hits.append({"kind": kind, "low_cny": low, "high_cny": high,
                         "currency": "CNY", "text": match.group(0)})
    qualified = [hit for hit in hits if hit["kind"] in {"range", "exact"}
                 and hit["low_cny"] <= hit["high_cny"]]
    signatures = {(hit["low_cny"], hit["high_cny"]) for hit in qualified}
    if not hits:
        status = "not_quantified"
    elif not qualified:
        status = "combined_unseparable"
    elif len(signatures) > 1:
        status = "amount_conflict"
    else:
        status = "qualified"
    selected = qualified[0] if status == "qualified" else None
    return {"status": status, "selected": selected, "hits": hits,
            "title_or_keyword_is_not_evidence": True}
