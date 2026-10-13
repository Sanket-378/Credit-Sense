from typing import Any, Literal

from pydantic import BaseModel, Field

Verdict = Literal["verified", "no_tampering_detected", "needs_review", "suspicious"]
CheckStatus = Literal["passed", "warning", "failed"]
FindingSeverity = Literal["low", "medium", "high"]
FindingCategory = Literal["forensics", "consistency", "extraction"]
OCRStatus = Literal["success", "partial", "failed"]
ExtractionConfidence = Literal["high", "medium", "low"]
ExtractionMethod = Literal["parser", "llm", "llm_fallback"]


class Finding(BaseModel):
    check: str
    severity: FindingSeverity
    detail: str
    category: FindingCategory = "consistency"


class CheckResult(BaseModel):
    status: CheckStatus
    findings: list[Finding] = Field(default_factory=list)


class SkippedCheck(BaseModel):
    name: str
    reason: str


class DocumentResult(BaseModel):
    filename: str
    doc_type: str
    ocr_status: OCRStatus
    authenticity_score: int = Field(ge=0, le=100)
    verdict: Verdict
    verdict_message: str | None = None
    extraction_confidence: ExtractionConfidence
    extraction_method: ExtractionMethod
    positive_signals: list[str] = Field(default_factory=list)
    forgery_check: CheckResult
    consistency_check: CheckResult
    extraction_check: CheckResult = Field(default_factory=lambda: CheckResult(status="passed"))
    extracted_data: dict[str, Any]
    missing_fields: list[str]
    checks_performed: list[str] = Field(default_factory=list)
    checks_skipped: list[SkippedCheck] = Field(default_factory=list)


class OverallResult(BaseModel):
    authenticity_score: int = Field(ge=0, le=100)
    verdict: Verdict
    documents_processed: int = Field(ge=0)


class VerificationResponse(BaseModel):
    user_id: str
    profile_id: str
    overall: OverallResult
    documents: list[DocumentResult]
