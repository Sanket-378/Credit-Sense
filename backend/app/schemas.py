from typing import Any, Literal

from pydantic import BaseModel, Field

Verdict = Literal["verified", "needs_review", "suspicious"]
CheckStatus = Literal["passed", "warning", "failed"]
FindingSeverity = Literal["low", "medium", "high"]
OCRStatus = Literal["success", "partial", "failed"]


class Finding(BaseModel):
    check: str
    severity: FindingSeverity
    detail: str


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
    forgery_check: CheckResult
    consistency_check: CheckResult
    extracted_data: dict[str, Any]
    missing_fields: list[str]
    checks_performed: list[str] = Field(default_factory=list)
    checks_skipped: list[SkippedCheck] = Field(default_factory=list)


class OverallResult(BaseModel):
    authenticity_score: int = Field(ge=0, le=100)
    verdict: Verdict
    documents_processed: int = Field(ge=0)


class VerificationResponse(BaseModel):
    profile_id: str
    overall: OverallResult
    documents: list[DocumentResult]
