import json

import pymupdf
import pytest

from app.services import forensics
from app.services.scoring import score_document


def _write_control_pdf(path):
    document = pymupdf.open()
    page = document.new_page(width=400, height=300)
    page.insert_text((72, 70), "Sample Bank Statement", fontsize=12)
    for y, amount in ((130, "₹100.00"), (160, "₹200.00"), (190, "₹300.00")):
        page.insert_text((72, y), amount, fontsize=12, fontname="helv")
    document.set_metadata({
        "producer": "Sample Bank PDF Engine",
        "creator": "Sample Bank PDF Engine",
        "creationDate": "D:20240101000000",
        "modDate": "D:20240101000000",
    })
    document.save(path)
    document.close()


def _fingerprint(path, tmp_path):
    with pymupdf.open(path) as document:
        fonts = sorted({
            str(font[3]).casefold()
            for page in document
            for font in page.get_fonts(full=True)
        })
    fingerprint_path = tmp_path / "known_generators.json"
    fingerprint_path.write_text(json.dumps({
        "sources": {
            "sample bank": {
                "doc_types": ["bank_statement"],
                "producers": ["Sample Bank PDF Engine"],
                "creators": ["Sample Bank PDF Engine"],
                "font_set": fonts,
            },
        },
    }), encoding="utf-8")
    return fingerprint_path


def _analyze(path, fingerprint_path, monkeypatch):
    monkeypatch.setattr(
        forensics,
        "_ocr_numeric_tokens",
        lambda _page: ["100.00", "200.00", "300.00"],
    )
    return forensics.analyze_pdf_report(
        path,
        "bank_statement",
        fingerprint_path=fingerprint_path,
    )


def _verdict(report):
    findings = [{**finding, "category": "forensics"} for finding in report["findings"]]
    return score_document(
        findings,
        [],
        4,
        "success",
        consistency_checks_count=2,
        extraction_confidence="high",
        positive_signals=[
            *report["positive_signals"],
            "transaction_sums_reconcile",
        ],
    )


def test_clean_pdf_has_registered_generator_and_positive_evidence(tmp_path, monkeypatch):
    path = tmp_path / "clean.pdf"
    _write_control_pdf(path)
    fingerprint_path = _fingerprint(path, tmp_path)

    report = _analyze(path, fingerprint_path, monkeypatch)
    score, verdict = _verdict(report)

    assert "generator_matches_known_source" in report["positive_signals"]
    assert score == 100
    assert verdict == "verified"


@pytest.mark.parametrize("edit", ["incremental", "overlay", "font", "visible_text"])
def test_pdf_edits_produce_findings_and_lower_verdict(
    edit,
    tmp_path,
    monkeypatch,
):
    path = tmp_path / f"{edit}.pdf"
    _write_control_pdf(path)
    fingerprint_path = _fingerprint(path, tmp_path)
    with pymupdf.open(path) as document:
        page = document[0]
        if edit == "incremental":
            page.insert_text((220, 250), "Updated")
        elif edit == "overlay":
            page.draw_rect(
                pymupdf.Rect(68, 145, 150, 165),
                color=None,
                fill=(1, 1, 1),
                overlay=True,
            )
            page.insert_text((72, 160), "₹999.00", fontsize=12)
        elif edit == "font":
            page.insert_text((72, 160), "₹999.00", fontsize=12, fontname="cour")
        else:
            page.insert_text((72, 220), "₹999.00", fontsize=12, render_mode=3)
        if edit == "incremental":
            document.saveIncr()
        else:
            document.saveIncr()

    report = _analyze(path, fingerprint_path, monkeypatch)
    checks = {finding["check"] for finding in report["findings"]}
    score, verdict = _verdict(report)

    expected_checks = {
        "incremental": {"pdf_incremental_updates", "pdf_replaced_objects"},
        "overlay": {"pdf_white_overlay"},
        "font": {"pdf_amount_font_inconsistency", "known_generator_mismatch"},
        "visible_text": {"pdf_visual_text_mismatch"},
    }
    assert expected_checks[edit].intersection(checks)
    assert score < 100
    assert verdict == "needs_review"
