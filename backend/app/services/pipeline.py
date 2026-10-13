import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from ..config import Settings
from ..models import VerifiedProfile
from ..schemas import CheckResult, DocumentResult, OverallResult, VerificationResponse
from .consistency import check_consistency_with_coverage, cross_document_name_findings
from .extractor import (
    ExtractionServiceError,
    REQUIRED_FIELDS,
    extract_document,
    transaction_reconciliation_findings,
)
from .file_handler import SavedUpload, delete_temporary_upload
from .forensics import analyze_forensics, analyze_pdf_report
from .reader import ReadResult, read_document
from .scoring import check_status, score_document, score_overall
from .vision_check import check_image_fields

logger = logging.getLogger(__name__)


def _failed_document(filename: str, doc_type: str, detail: str) -> dict[str, Any]:
    failure = {
        "check": "processing_error",
        "severity": "low",
        "detail": detail,
        "category": "extraction",
    }
    return {
        "filename": filename,
        "doc_type": doc_type,
        "ocr_status": "failed",
        "authenticity_score": 100,
        "verdict": "needs_review",
        "verdict_message": "We could not read this document reliably. Try a clearer or original PDF.",
        "extraction_confidence": "low",
        "extraction_method": "llm_fallback",
        "positive_signals": [],
        "forgery_check": {"status": "passed", "findings": []},
        "consistency_check": {"status": "passed", "findings": []},
        "extraction_check": {"status": "warning", "findings": [failure]},
        "extracted_data": {},
        "missing_fields": REQUIRED_FIELDS[doc_type].copy(),
        "checks_performed": [],
        "checks_skipped": [
            {
                "name": "consistency_checks",
                "reason": "Document processing did not complete.",
            }
        ],
    }


def _analyze_document(
    path: Path,
    file_type: str,
    doc_type: str,
    settings: Settings,
) -> dict[str, Any]:
    read_result: ReadResult = read_document(path, file_type, settings.ocr_language_list)
    if not read_result.text.strip():
        raise ValueError("No readable text was found.")
    extraction = extract_document(read_result.text, doc_type, settings)
    extracted_data = extraction.data
    if file_type == "pdf":
        forensic_report = analyze_pdf_report(
            path,
            doc_type,
            page_images=read_result.page_images,
        )
        forgery_findings = forensic_report["findings"]
        positive_signals = forensic_report["positive_signals"]
    else:
        forgery_findings = analyze_forensics(
            path,
            file_type,
            read_result.page_images,
            settings.ela_ratio_threshold,
            doc_type,
        )
        positive_signals = []
    if read_result.page_images:
        forgery_findings.extend(
            check_image_fields(
                read_result.page_images[0],
                doc_type,
                extracted_data,
                settings,
            )
        )
    (
        consistency_findings,
        missing_fields,
        checks_performed,
        checks_skipped,
    ) = check_consistency_with_coverage(doc_type, extracted_data)
    extraction_checks = {
        "date_format",
        "required_fields",
        "statement_credit_total",
        "statement_debit_total",
        "transaction_date_format",
        "transaction_shape",
    }
    data_reading_findings = transaction_reconciliation_findings(extracted_data)
    genuine_consistency_findings = []
    for finding in consistency_findings:
        tagged_finding = {**finding, "category": "consistency"}
        if finding["check"] in extraction_checks:
            tagged_finding["category"] = "extraction"
            if finding["check"] not in {
                "statement_credit_total",
                "statement_debit_total",
            }:
                data_reading_findings.append(tagged_finding)
        else:
            genuine_consistency_findings.append(tagged_finding)
    for finding in forgery_findings:
        finding["category"] = "forensics"
    if extraction.invalid_date_count:
        genuine_consistency_findings.append({
            "check": "impossible_transaction_date",
            "severity": "high",
            "detail": (
                f"{extraction.invalid_date_count} impossible transaction date(s) "
                "were rejected during parsing."
            ),
            "category": "consistency",
        })
    positive_signals = [
        *positive_signals,
        *_statement_positive_signals(extracted_data, doc_type),
    ]
    positive_signals = sorted(set(positive_signals))

    findings = [
        *forgery_findings,
        *genuine_consistency_findings,
        *data_reading_findings,
    ]
    score, verdict = score_document(
        findings,
        missing_fields,
        len(REQUIRED_FIELDS[doc_type]),
        read_result.ocr_status,
        consistency_checks_count=len(checks_performed),
        extraction_confidence=extraction.extraction_confidence,
        positive_signals=positive_signals,
    )
    verdict_message = (
        "We could not read this document reliably. Try a clearer or original PDF."
        if verdict == "needs_review" and extraction.extraction_confidence == "low"
        else "No signs of tampering found. This is not proof of authenticity."
        if verdict == "no_tampering_detected"
        else None
    )
    return {
        "filename": "",
        "doc_type": doc_type,
        "ocr_status": read_result.ocr_status,
        "authenticity_score": score,
        "verdict": verdict,
        "verdict_message": verdict_message,
        "extraction_confidence": extraction.extraction_confidence,
        "extraction_method": extraction.extraction_method,
        "positive_signals": positive_signals,
        "forgery_check": {
            "status": check_status(forgery_findings),
            "findings": forgery_findings,
        },
        "consistency_check": {
            "status": check_status(genuine_consistency_findings),
            "findings": genuine_consistency_findings,
        },
        "extraction_check": {
            "status": check_status(data_reading_findings),
            "findings": data_reading_findings,
        },
        "extracted_data": extracted_data,
        "missing_fields": missing_fields,
        "checks_performed": checks_performed,
        "checks_skipped": checks_skipped,
    }


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(str(value).replace(",", "").replace("₹", "").strip())
    except (TypeError, ValueError):
        return None


def _amount_matches(expected: float, actual: float) -> bool:
    return abs(expected - actual) <= max(1.0, abs(expected) * 0.01)


def _statement_positive_signals(data: dict[str, Any], doc_type: str) -> list[str]:
    if doc_type not in {"bank_statement", "upi_statement"}:
        return []
    transactions = data.get("transactions")
    if not isinstance(transactions, list) or not all(
        isinstance(transaction, dict) for transaction in transactions
    ):
        return []

    totals = {}
    for direction in ("debit", "credit"):
        amounts = [_number(transaction.get(direction)) for transaction in transactions]
        if any(
            transaction.get(direction) is not None and amount is None
            for transaction, amount in zip(transactions, amounts, strict=True)
        ):
            return []
        stated_total = _number(data.get(f"total_{direction}s"))
        if stated_total is None:
            return []
        totals[direction] = (sum(amount or 0.0 for amount in amounts), stated_total)
    signals = (
        ["transaction_sums_reconcile"]
        if all(_amount_matches(expected, actual) for expected, actual in totals.values())
        else []
    )

    if doc_type == "bank_statement":
        opening = _number(data.get("opening_balance"))
        closing = _number(data.get("closing_balance"))
        if opening is not None and closing is not None:
            expected_closing = opening + totals["credit"][0] - totals["debit"][0]
            if _amount_matches(expected_closing, closing):
                signals.append("balance_chain_reconciles")
    return signals


async def _process_one(
    filename: str,
    doc_type: str,
    upload: SavedUpload,
    settings: Settings,
) -> dict[str, Any]:
    try:
        result = await asyncio.to_thread(
            _analyze_document,
            upload.path,
            upload.file_type,
            doc_type,
            settings,
        )
        result["filename"] = filename
        return result
    except ExtractionServiceError as error:
        logger.warning("Document extraction service failed.")
        return _failed_document(filename, doc_type, str(error))
    except Exception:
        logger.error("Document processing failed.")
        return _failed_document(
            filename,
            doc_type,
            "This document could not be processed. Check that it is readable and try again.",
        )
    finally:
        delete_temporary_upload(upload)


def _to_document_result(result: dict[str, Any]) -> DocumentResult:
    payload = {
        **result,
        "forgery_check": CheckResult(**result["forgery_check"]),
        "consistency_check": CheckResult(**result["consistency_check"]),
        "extraction_check": CheckResult(**result["extraction_check"]),
    }
    return DocumentResult(**payload)


async def process_documents(
    uploads: list[tuple[str, str, SavedUpload]],
    settings: Settings,
    db: Session,
    user_id: str,
) -> VerificationResponse:
    tasks = [
        _process_one(filename, doc_type, upload, settings)
        for filename, doc_type, upload in uploads
    ]
    results = await asyncio.gather(*tasks)

    cross_findings = cross_document_name_findings(results, settings.name_match_threshold)
    for index, findings in cross_findings.items():
        result = results[index]
        for finding in findings:
            finding["category"] = "consistency"
        result["consistency_check"]["findings"].extend(findings)
        result["consistency_check"]["status"] = check_status(result["consistency_check"]["findings"])
        score, verdict = score_document(
            [
                *result["forgery_check"]["findings"],
                *result["consistency_check"]["findings"],
                *result["extraction_check"]["findings"],
            ],
            result["missing_fields"],
            len(REQUIRED_FIELDS[result["doc_type"]]),
            result["ocr_status"],
            consistency_checks_count=len(result["checks_performed"]),
            extraction_confidence=result["extraction_confidence"],
            positive_signals=result.get("positive_signals", []),
        )
        result["authenticity_score"] = score
        result["verdict"] = verdict
        result["verdict_message"] = (
            "We could not read this document reliably. Try a clearer or original PDF."
            if verdict == "needs_review" and result["extraction_confidence"] == "low"
            else "No signs of tampering found. This is not proof of authenticity."
            if verdict == "no_tampering_detected"
            else None
        )

    mismatch_pairs = sum(len(findings) for findings in cross_findings.values()) // 2
    overall_score, overall_verdict = score_overall(
        [result["authenticity_score"] for result in results],
        mismatch_pairs,
    )
    if overall_verdict == "verified" and any(
        result["verdict"] != "verified" for result in results
    ):
        overall_verdict = "needs_review"
    profile_id = str(uuid.uuid4())
    persisted_data = {
        "documents": [
            {
                "doc_type": result["doc_type"],
                "authenticity_score": result["authenticity_score"],
                "verdict": result["verdict"],
                "extraction_method": result["extraction_method"],
                "extraction_confidence": result["extraction_confidence"],
                "extracted_data": result["extracted_data"],
            }
            for result in results
        ],
    }
    profile = VerifiedProfile(
        id=profile_id,
        overall_score=overall_score,
        verdict=overall_verdict,
        data=persisted_data,
        user_id=user_id,
    )
    db.add(profile)
    db.commit()

    return VerificationResponse(
        user_id=user_id,
        profile_id=profile_id,
        overall=OverallResult(
            authenticity_score=overall_score,
            verdict=overall_verdict,
            documents_processed=len(results),
        ),
        documents=[_to_document_result(result) for result in results],
    )
