import asyncio

from app.services.file_handler import SavedUpload
from app.services.pipeline import _failed_document, _process_one
from app.config import Settings


def test_failed_document_has_required_failure_shape():
    result = _failed_document("statement.pdf", "bank_statement", "Document could not be processed.")

    assert result["ocr_status"] == "failed"
    assert result["authenticity_score"] == 0
    assert result["forgery_check"]["findings"][0]["severity"] == "high"
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
    assert result["authenticity_score"] == 0
    assert "Untrusted document" not in result["forgery_check"]["findings"][0]["detail"]
