from collections.abc import Iterable

PENALTIES = {"low": 3, "medium": 10, "high": 25}
MAX_MISSING_FIELD_PENALTY = 15
OCR_PARTIAL_PENALTY = 10
OCR_FAILED_PENALTY = 20
# A verified verdict requires at least two completed consistency checks.
MIN_CONSISTENCY_CHECKS_FOR_VERIFIED_VERDICT = 2


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
) -> tuple[int, str]:
    score = 100
    score -= sum(PENALTIES.get(finding["severity"], 0) for finding in findings)
    if required_field_count > 0 and missing_fields:
        score -= round(MAX_MISSING_FIELD_PENALTY * len(missing_fields) / required_field_count)
    if ocr_status == "partial":
        score -= OCR_PARTIAL_PENALTY
    elif ocr_status == "failed":
        score -= OCR_FAILED_PENALTY
    score = max(0, min(100, score))
    verdict = verdict_for_score(score)
    if (
        verdict == "verified"
        and consistency_checks_count is not None
        and consistency_checks_count < MIN_CONSISTENCY_CHECKS_FOR_VERIFIED_VERDICT
    ):
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
