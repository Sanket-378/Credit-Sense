import pytest

from app.services.scoring import (
    MIN_CONSISTENCY_CHECKS_FOR_VERIFIED_VERDICT,
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
    score, verdict = score_document([finding], [], 4, "success")
    assert score == expected
    assert verdict == verdict_for_score(expected)


def test_missing_field_penalty_is_proportional():
    score, _ = score_document([], ["one", "two"], 4, "success")
    assert score == 92


@pytest.mark.parametrize(("ocr_status", "expected"), [("partial", 90), ("failed", 80)])
def test_ocr_penalty(ocr_status, expected):
    score, _ = score_document([], [], 4, ocr_status)
    assert score == expected


@pytest.mark.parametrize(
    ("score", "expected"),
    [(100, "verified"), (80, "verified"), (79, "needs_review"), (50, "needs_review"), (49, "suspicious"), (0, "suspicious")],
)
def test_verdict_thresholds(score, expected):
    assert verdict_for_score(score) == expected


def test_score_clamps_to_zero():
    score, verdict = score_document([{"severity": "high"}] * 5, ["a", "b", "c"], 3, "failed")
    assert (score, verdict) == (0, "suspicious")


def test_verified_verdict_requires_two_consistency_checks():
    assert MIN_CONSISTENCY_CHECKS_FOR_VERIFIED_VERDICT == 2

    capped_score, capped_verdict = score_document(
        [], [], 4, "success", consistency_checks_count=1,
    )
    verified_score, verified_verdict = score_document(
        [], [], 4, "success", consistency_checks_count=2,
    )

    assert (capped_score, capped_verdict) == (100, "needs_review")
    assert (verified_score, verified_verdict) == (100, "verified")


def test_overall_weights_lowest_document_and_average():
    score, verdict = score_overall([80, 100])
    assert score == 84
    assert verdict == "verified"


def test_check_status_severity():
    assert check_status([]) == "passed"
    assert check_status([{"severity": "low"}]) == "warning"
    assert check_status([{"severity": "high"}]) == "failed"
