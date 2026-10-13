import asyncio

from app.services.file_handler import SavedUpload
from app.services.pipeline import (
    _analyze_document,
    _failed_document,
    _process_one,
    _statement_positive_signals,
)
from app.config import Settings
from app.services.reader import ReadResult


def test_failed_document_has_required_failure_shape():
    result = _failed_document("statement.pdf", "bank_statement", "Document could not be processed.")

    assert result["ocr_status"] == "failed"
    assert result["authenticity_score"] == 100
    assert result["verdict"] == "needs_review"
    assert result["extraction_check"]["findings"][0]["severity"] == "low"
    assert result["checks_performed"] == []
    assert result["checks_skipped"][0]["name"] == "consistency_checks"


def test_temporary_upload_is_deleted_when_processing_fails(tmp_path, monkeypatch):
    path = tmp_path / "upload.pdf"
    path.write_bytes(b"%PDF-1.7")

    def fail_processing(*_):
        raise ValueError("Untrusted document failed to parse.")

    monkeypatch.setattr("app.services.pipeline._analyze_document", fail_processing)
    result = asyncio.run(
        _process_one(
            "statement.pdf",
            "salary_slip",
            SavedUpload(path=path, file_type="pdf"),
            Settings(groq_api_key="test-key", groq_text_model="test-model"),
        )
    )

    assert not path.exists()
    assert result["authenticity_score"] == 100
    assert "Untrusted document" not in result["extraction_check"]["findings"][0]["detail"]


def test_statement_reconciliation_is_a_quality_finding_not_authenticity_penalty(
    tmp_path,
    monkeypatch,
):
    text = (
        "Name: Asha Rao\n"
        "03 Sep 2026\nPaid to Shop\n₹60.00\n"
        "04 Sep 2026\nReceived from Maya\n₹10.00\n"
        "Sent ₹100.00\nReceived ₹10.00"
    )
    monkeypatch.setattr(
        "app.services.pipeline.read_document",
        lambda *_: ReadResult(text, [], "success", text.splitlines()),
    )
    monkeypatch.setattr(
        "app.services.pipeline.analyze_pdf_report",
        lambda *_args, **_kwargs: {"findings": [], "positive_signals": []},
    )
    path = tmp_path / "statement.pdf"
    path.write_bytes(b"%PDF-1.7")

    result = _analyze_document(
        path,
        "pdf",
        "upi_statement",
        Settings(groq_api_key="", groq_text_model=""),
    )

    assert result["extraction_method"] == "parser"
    assert result["extraction_confidence"] == "low"
    assert result["authenticity_score"] == 100
    assert result["verdict"] == "needs_review"
    assert result["verdict_message"] == "We could not read this document reliably. Try a clearer or original PDF."
    assert result["consistency_check"]["findings"] == []
    issue = result["extraction_check"]["findings"][0]
    assert issue["category"] == "extraction"
    assert "Could not fully verify transactions" in issue["detail"]


def test_statement_positive_signals_require_reconciled_totals_and_balances():
    data = {
        "transactions": [
            {"debit": 25, "credit": None},
            {"debit": None, "credit": 100},
        ],
        "total_debits": 25,
        "total_credits": 100,
        "opening_balance": 500,
        "closing_balance": 575,
    }

    assert _statement_positive_signals(data, "bank_statement") == [
        "transaction_sums_reconcile",
        "balance_chain_reconciles",
    ]

    data["closing_balance"] = 999
    assert _statement_positive_signals(data, "bank_statement") == [
        "transaction_sums_reconcile",
    ]
