"""exp23 官方公告正文证据的纯函数：不以标题或后验阶段判用途。"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

TITLE_EXCLUDES = (
    "进展", "实施", "完成", "结果", "期限届满", "股份变动", "修订", "调整",
    "法律意见", "独立意见", "核查意见", "债权人", "董事会决议", "监事会决议",
)
INITIAL_PATTERNS = (
    re.compile(r"董事会.{0,180}(?:审议通过|通过).{0,180}回购.{0,100}(?:方案|议案)"),
    re.compile(r"回购.{0,100}(?:方案|议案).{0,180}(?:经|由).{0,100}董事会.{0,80}(?:审议通过|通过)"),
)
REVISION_PATTERN = re.compile(
    r"(?:回购方案|回购股份方案)(?:修订稿|修订版|调整稿|变更稿)"
    r"|(?:修订后|调整后|变更后)(?:的)?(?:回购方案|回购股份方案)"
)
PRICE_PATTERN = re.compile(
    r"回购(?:股份)?(?:的)?价格.{0,60}?(?:不超过|不高于|上限为|最高为|为)\s*(?:人民币)?\s*"
    r"([0-9]+(?:\.[0-9]+)?)\s*元\s*/?\s*股"
)
PURPOSE_PATTERNS = {
    "cancellation": (
        re.compile(r"用于.{0,30}注销.{0,40}减少.{0,20}注册资本"),
        re.compile(r"回购.{0,30}股份.{0,30}(?:全部|将).{0,20}注销"),
        re.compile(r"(?:本次|上述|同意将|需|公司将).{0,20}回购注销.{0,100}限制性股票"),
        re.compile(r"限制性股票.{0,100}(?:全部|由公司|进行|予以|需).{0,30}回购注销"),
        re.compile(r"办理.{0,30}减少注册资本.{0,30}(?:股份)?注销"),
    ),
    "inventory": (
        re.compile(r"用于.{0,50}(?:员工持股计划|股权激励)"),
        re.compile(r"用于.{0,60}转换.{0,60}可转换.{0,20}公司债券"),
        re.compile(r"存放于.{0,40}回购专用证券账户"),
        re.compile(r"作为.{0,30}库存股"),
    ),
    "other": (
        re.compile(r"用于.{0,60}维护公司价值及股东权益"),
        re.compile(r"为维护.{0,60}公司价值及股东权益"),
    ),
}


def compact(value: str) -> str:
    return re.sub(r"\s+", "", value or "")


def is_candidate_title(value: str) -> bool:
    text = compact(value)
    return "回购" in text and not any(term in text for term in TITLE_EXCLUDES)


def decimal_values(pattern: re.Pattern, text: str) -> list[Decimal]:
    values = []
    for match in pattern.finditer(compact(text)):
        try:
            values.append(Decimal(match.group(1)))
        except InvalidOperation:
            continue
    return values


def has_initial_board_marker(text: str) -> bool:
    body = compact(text)
    return any(pattern.search(body) for pattern in INITIAL_PATTERNS)


def has_revision_marker(text: str) -> bool:
    return bool(REVISION_PATTERN.search(compact(text)))


def purpose_evidence(text: str) -> dict:
    body = compact(text)
    matches = {}
    for label, patterns in PURPOSE_PATTERNS.items():
        hits = [match.group(0) for pattern in patterns for match in pattern.finditer(body)]
        if hits:
            matches[label] = hits[:3]
    labels = set(matches)
    if labels == {"cancellation"}:
        category = "cancellation"
    elif labels == {"inventory"}:
        category = "inventory"
    elif labels:
        category = "other_explicit"
    else:
        category = "unclassifiable"
    return {"category": category, "body_phrase_hits": matches,
            "not_for_verdict": True, "title_used_for_purpose": False}


def document_evidence(text: str, high_limit) -> dict:
    prices = decimal_values(PRICE_PATTERN, text)
    expected = Decimal(str(high_limit)) if high_limit is not None else None
    initial = has_initial_board_marker(text)
    revision = has_revision_marker(text)
    price_match = expected is not None and expected in prices
    purpose = purpose_evidence(text)
    return {
        "initial_board_marker": initial,
        "revision_marker": revision,
        "source_high_limit": expected,
        "body_price_limits": prices,
        "exact_high_limit_match": price_match,
        "first_disclosure_supported": initial and not revision and price_match,
        "scheme_identity_supported": initial and not revision and price_match,
        "purpose": purpose,
    }
