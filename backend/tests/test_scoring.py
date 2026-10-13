import pytest

from app.services.scoring import (
    MIN_CONSISTENCY_CHECKS_FOR_VERIFIED_VERDICT,
    MIN_POSITIVE_SIGNALS_FOR_VERIFIED_VERDICT,
    check_status,
    score_document,
    score_overall,
    verdict_for_score,
)


@pytest.mark.parametrize(
    ("finding", "expected"),
    [
        ({"severity": "low"}, 97),
        ({"severity": "medium"}, 90),
        ({"severity": "high"}, 75),
    ],
)
def test_finding_penalties(finding, expected):
    score, verdict = score_document(
        [finding], [], 4, "success",
        positive_signals=["valid_digital_signature", "transaction_sums_reconcile"],
    )
    assert score == expected
    assert verdict == verdict_for_score(expected)


def test_missing_fields_do_not_reduce_authenticity_score():
    score, _ = score_document([], ["one", "two"], 4, "success")
    assert score == 100


@pytest.mark.parametrize("ocr_status", ["partial", "failed"])
def test_ocr_quality_caps_verdict_without_reducing_authenticity_score(ocr_status):
    score, verdict = score_document([], [], 4, ocr_status)
    assert score == 100
    assert verdict == "needs_review"


@pytest.mark.parametrize(
    ("score", "expected"),
    [(100, "verified"), (80, "verified"), (79, "needs_review"), (50, "needs_review"), (49, "suspicious"), (0, "suspicious")],
)
def test_verdict_thresholds(score, expected):
    assert verdict_for_score(score) == expected


def test_category_penalty_caps_prevent_repeated_findings_from_erasing_score():
    score, verdict = score_document([{"severity": "high"}] * 5, ["a", "b", "c"], 3, "failed")
    assert (score, verdict) == (65, "needs_review")


def test_extraction_reconciliation_failure_alone_is_needs_review():
    score, verdict = score_document(
        [{
            "severity": "medium",
            "category": "extraction",
            "check": "transaction_total_reconciliation",
        }],
        [],
        4,
        "success",
        consistency_checks_count=2,
        extraction_confidence="low",
    )

    assert score == 100
    assert verdict == "needs_review"


def test_repeated_findings_are_capped_per_category():
    findings = [
        {"severity": "high", "category": "forensics"},
        {"severity": "high", "category": "forensics"},
        {"severity": "high", "category": "forensics"},
        {"severity": "high", "category": "consistency"},
        {"severity": "high", "category": "consistency"},
    ]
    score, verdict = score_document(findings, [], 4, "success")
    assert (score, verdict) == (15, "suspicious")


def test_editor_metadata_remains_authenticity_evidence():
    score, verdict = score_document(
        [{"severity": "high", "category": "forensics", "check": "pdf_editor_metadata"}],
        [],
        4,
        "success",
    )
    assert (score, verdict) == (75, "needs_review")


def test_verified_verdict_requires_two_consistency_checks():
    assert MIN_CONSISTENCY_CHECKS_FOR_VERIFIED_VERDICT == 2
    assert MIN_POSITIVE_SIGNALS_FOR_VERIFIED_VERDICT == 2

    capped_score, capped_verdict = score_document(
        [], [], 4, "success", consistency_checks_count=1,
    )
    verified_score, verified_verdict = score_document(
        [], [], 4, "success", consistency_checks_count=2,
        positive_signals=["valid_digital_signature", "transaction_sums_reconcile"],
    )

    assert (capped_score, capped_verdict) == (85, "no_tampering_detected")
    assert (verified_score, verified_verdict) == (100, "verified")


def test_no_negative_findings_without_two_signals_is_not_verified():
    score, verdict = score_document([], [], 4, "success", positive_signals=[])

    assert (score, verdict) == (85, "no_tampering_detected")


def test_medium_or_high_forensic_finding_blocks_verified():
    score, verdict = score_document(
        [{"severity": "medium", "category": "forensics"}],
        [],
        4,
        "success",
        consistency_checks_count=2,
        positive_signals=["valid_digital_signature", "transaction_sums_reconcile"],
    )

    assert score == 90
    assert verdict == "needs_review"


def test_overall_weights_lowest_document_and_average():
    score, verdict = score_overall([80, 100])
    assert score == 84
    assert verdict == "verified"


def test_check_status_severity():
    assert check_status([]) == "passed"
    assert check_status([{"severity": "low"}]) == "warning"
    assert check_status([{"severity": "high"}]) == "failed"
