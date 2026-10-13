from collections.abc import Iterable

PENALTIES = {"low": 3, "medium": 10, "high": 25}
# Caps: forensics 50, consistency 35, extraction 0; repeated issues cannot erase authenticity alone.
MAX_CATEGORY_PENALTIES = {
    "forensics": 50,
    "consistency": 35,
    "extraction": 0,
}
# A verified verdict requires at least two completed consistency checks.
MIN_CONSISTENCY_CHECKS_FOR_VERIFIED_VERDICT = 2
MIN_POSITIVE_SIGNALS_FOR_VERIFIED_VERDICT = 2


def verdict_for_score(score: int) -> str:
    if score >= 80:
        return "verified"
    if score >= 50:
        return "needs_review"
    return "suspicious"


def check_status(findings: Iterable[dict[str, str]]) -> str:
    severities = {finding["severity"] for finding in findings}
    if "high" in severities:
        return "failed"
    if severities.intersection({"low", "medium"}):
        return "warning"
    return "passed"


def score_document(
    findings: list[dict[str, str]],
    missing_fields: list[str],
    required_field_count: int,
    ocr_status: str,
    consistency_checks_count: int | None = None,
    extraction_confidence: str | None = None,
    positive_signals: list[str] | None = None,
) -> tuple[int, str]:
    score = 100
    category_penalties = {category: 0 for category in MAX_CATEGORY_PENALTIES}
    for finding in findings:
        category = finding.get("category", "consistency")
        if category not in category_penalties:
            category = "consistency"
        category_penalties[category] += PENALTIES.get(finding["severity"], 0)
    score -= sum(
        min(category_penalties[category], penalty_cap)
        for category, penalty_cap in MAX_CATEGORY_PENALTIES.items()
    )
    score = max(0, min(100, score))
    verdict = verdict_for_score(score)
    positive_signal_count = len(set(positive_signals or []))
    has_findings = bool(findings)
    if (
        not has_findings
        and positive_signal_count < MIN_POSITIVE_SIGNALS_FOR_VERIFIED_VERDICT
        and extraction_confidence != "low"
        and not missing_fields
        and ocr_status == "success"
    ):
        score = min(score, 85)
        verdict = "no_tampering_detected"
    if (
        verdict == "verified"
        and consistency_checks_count is not None
        and consistency_checks_count < MIN_CONSISTENCY_CHECKS_FOR_VERIFIED_VERDICT
    ):
        verdict = "needs_review"
    if (
        verdict == "verified"
        and (
            positive_signal_count < MIN_POSITIVE_SIGNALS_FOR_VERIFIED_VERDICT
            or any(
                finding.get("category") == "forensics"
                and finding["severity"] in {"medium", "high"}
                for finding in findings
            )
            or extraction_confidence == "low"
            or any(finding.get("category") == "extraction" for finding in findings)
            or bool(missing_fields)
            or ocr_status != "success"
        )
    ):
        verdict = "needs_review"
    if verdict == "verified" and positive_signal_count < MIN_POSITIVE_SIGNALS_FOR_VERIFIED_VERDICT:
        verdict = "needs_review"
    return score, verdict


def score_overall(document_scores: list[int], cross_document_mismatches: int = 0) -> tuple[int, str]:
    if not document_scores:
        return 0, "suspicious"
    minimum = min(document_scores)
    average = sum(document_scores) / len(document_scores)
    score = round(0.6 * minimum + 0.4 * average)
    score = max(0, min(100, score - cross_document_mismatches * PENALTIES["medium"]))
    return score, verdict_for_score(score)
