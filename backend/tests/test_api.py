import json
from types import SimpleNamespace

import pymupdf
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings
from app.database import Base, get_db, initialize_database
from app.main import app
from app.models import VerificationUser, VerifiedProfile
from app.routers.documents import ALLOWED_DOC_TYPES


def _configured_settings():
    return Settings(groq_api_key="test-key", groq_text_model="test-model")


def test_health_endpoint():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}


def test_root_endpoint_points_to_docs_and_health():
    with TestClient(app) as client:
        assert client.get("/").json() == {
            "name": "CreditSense API",
            "docs": "/docs",
            "health": "/health",
        }


def test_database_initialization_adds_user_link_to_existing_profiles():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE verified_profiles ("
            "id VARCHAR(36) PRIMARY KEY, "
            "created_at DATETIME NOT NULL, "
            "overall_score INTEGER NOT NULL, "
            "verdict VARCHAR(20) NOT NULL, "
            "data JSON NOT NULL)"
        ))
        connection.execute(text(
            "INSERT INTO verified_profiles "
            "(id, created_at, overall_score, verdict, data) "
            "VALUES ('legacy-profile', '2025-01-01', 85, 'needs_review', '{}')"
        ))

    initialize_database(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("verified_profiles")}
    assert "user_id" in columns
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT user_id FROM verified_profiles WHERE id = 'legacy-profile'")
        ).scalar_one() is None
    engine.dispose()


def test_upi_statement_is_an_allowed_document_type():
    assert "upi_statement" in ALLOWED_DOC_TYPES


def test_verification_reports_missing_groq_configuration():
    app.dependency_overrides[get_settings] = lambda: Settings(
        groq_api_key="",
        groq_text_model="",
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/documents/verify",
                files=[("files", ("statement.pdf", b"%PDF-1.7", "application/pdf"))],
                data={"doc_types": "salary_slip"},
            )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert response.status_code == 503
    assert "GROQ_API_KEY and GROQ_TEXT_MODEL" in response.json()["detail"]


def test_verification_rejects_mismatched_document_types():
    app.dependency_overrides[get_settings] = _configured_settings
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/documents/verify",
                files=[("files", ("statement.pdf", b"%PDF-1.7", "application/pdf"))],
                data={"doc_types": ["salary_slip", "invoice"]},
            )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert response.status_code == 400
    assert "must match" in response.json()["detail"]


def test_verification_checks_magic_bytes_not_only_extension():
    app.dependency_overrides[get_settings] = _configured_settings
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/documents/verify",
                files=[("files", ("statement.pdf", b"not a PDF", "application/pdf"))],
                data={"doc_types": "salary_slip"},
            )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert response.status_code == 400
    assert "matching file contents" in response.json()["detail"]


def test_verification_rejects_unsupported_document_type():
    app.dependency_overrides[get_settings] = _configured_settings
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/documents/verify",
                files=[("files", ("statement.pdf", b"%PDF-1.7", "application/pdf"))],
                data={"doc_types": "passport"},
            )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert response.status_code == 400
    assert "Unsupported document type" in response.json()["detail"]


def test_verification_rejects_oversized_file():
    app.dependency_overrides[get_settings] = lambda: Settings(
        groq_api_key="test-key",
        groq_text_model="test-model",
        max_file_mb=1,
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/documents/verify",
                files=[("files", ("statement.pdf", b"%PDF-" + b"x" * (1024 * 1024), "application/pdf"))],
                data={"doc_types": "salary_slip"},
            )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert response.status_code == 400
    assert "file size limit" in response.json()["detail"]


def test_verification_returns_and_persists_only_extracted_results(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_db():
        session = test_sessions()
        try:
            yield session
        finally:
            session.close()

    class MockCompletions:
        def create(self, **_):
            content = json.dumps({
                "employee_name": "Asha Rao",
                "employer_name": "Example Works",
                "month": "December 2024",
                "gross_salary": 50000,
                "total_deductions": 5000,
                "net_salary": 45000,
                "pf_amount": 2500,
                "tax_amount": 2500,
            })
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
            )

    class MockGroq:
        def __init__(self, api_key):
            self.chat = SimpleNamespace(completions=MockCompletions())

    monkeypatch.setattr("app.services.extractor.Groq", MockGroq)
    monkeypatch.setattr(
        "app.services.pipeline.analyze_pdf_report",
        lambda *_args, **_kwargs: {"findings": [], "positive_signals": []},
    )
    app.dependency_overrides[get_settings] = lambda: Settings(
        groq_api_key="test-key",
        groq_text_model="test-model",
        enable_vision_crosscheck=False,
    )
    app.dependency_overrides[get_db] = override_db
    user_id = "d6dca8d6-c33a-4faa-866b-99f3cb81f685"

    pdf = pymupdf.open()
    pdf.new_page().insert_text((72, 72), "Salary slip for Asha Rao Example Works December 2024")
    pdf_bytes = pdf.tobytes()
    pdf.close()

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/documents/verify",
                files=[("files", ("payslip.pdf", pdf_bytes, "application/pdf"))],
                data={"doc_types": "salary_slip"},
                headers={"X-User-ID": user_id},
            )
    finally:
        app.dependency_overrides.pop(get_settings, None)
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    result = response.json()
    assert result["user_id"] == user_id
    assert result["overall"]["documents_processed"] == 1
    assert result["documents"][0]["extracted_data"]["net_salary"] == 45000
    assert result["documents"][0]["extraction_method"] == "llm"
    assert result["documents"][0]["extraction_confidence"] == "medium"
    assert "extraction_check" in result["documents"][0]
    assert "checks_performed" in result["documents"][0]
    assert "checks_skipped" in result["documents"][0]
    assert result["documents"][0]["positive_signals"] == []
    with test_sessions() as session:
        profile = session.get(VerifiedProfile, result["profile_id"])
        assert profile is not None
        assert profile.user_id == user_id
        assert session.get(VerificationUser, user_id) is not None
        assert profile.overall_score == result["overall"]["authenticity_score"]
        assert "payslip.pdf" not in json.dumps(profile.data)
        assert profile.data["documents"][0]["extracted_data"]["employee_name"] == "Asha Rao"
    engine.dispose()
