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
from .extractor import ExtractionServiceError, REQUIRED_FIELDS, extract_document_data
from .file_handler import SavedUpload, delete_temporary_upload
from .forensics import analyze_forensics
from .reader import ReadResult, read_document
from .scoring import check_status, score_document, score_overall
from .vision_check import check_image_fields

logger = logging.getLogger(__name__)


def _failed_document(filename: str, doc_type: str, detail: str) -> dict[str, Any]:
    failure = {"check": "processing_error", "severity": "high", "detail": detail}
    return {
        "filename": filename,
        "doc_type": doc_type,
        "ocr_status": "failed",
        "authenticity_score": 0,
        "verdict": "suspicious",
        "forgery_check": {"status": "failed", "findings": [failure]},
        "consistency_check": {"status": "failed", "findings": []},
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
    extracted_data = extract_document_data(read_result.text, doc_type, settings)
    forgery_findings = analyze_forensics(
        path,
        file_type,
        read_result.page_images,
        settings.ela_ratio_threshold,
    )
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
    findings = [*forgery_findings, *consistency_findings]
    score, verdict = score_document(
        findings,
        missing_fields,
        len(REQUIRED_FIELDS[doc_type]),
        read_result.ocr_status,
        consistency_checks_count=len(checks_performed),
    )
    return {
        "filename": "",
        "doc_type": doc_type,
        "ocr_status": read_result.ocr_status,
        "authenticity_score": score,
        "verdict": verdict,
        "forgery_check": {
            "status": check_status(forgery_findings),
            "findings": forgery_findings,
        },
        "consistency_check": {
            "status": check_status(consistency_findings),
            "findings": consistency_findings,
        },
        "extracted_data": extracted_data,
        "missing_fields": missing_fields,
        "checks_performed": checks_performed,
        "checks_skipped": checks_skipped,
    }


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
    }
    return DocumentResult(**payload)


async def process_documents(
    uploads: list[tuple[str, str, SavedUpload]],
    settings: Settings,
    db: Session,
) -> VerificationResponse:
    tasks = [
        _process_one(filename, doc_type, upload, settings)
        for filename, doc_type, upload in uploads
    ]
    results = await asyncio.gather(*tasks)

    cross_findings = cross_document_name_findings(results, settings.name_match_threshold)
    for index, findings in cross_findings.items():
        result = results[index]
        result["consistency_check"]["findings"].extend(findings)
        result["consistency_check"]["status"] = check_status(result["consistency_check"]["findings"])
        score, verdict = score_document(
            [
                *result["forgery_check"]["findings"],
                *result["consistency_check"]["findings"],
            ],
            result["missing_fields"],
            len(REQUIRED_FIELDS[result["doc_type"]]),
            result["ocr_status"],
            consistency_checks_count=len(result["checks_performed"]),
        )
        result["authenticity_score"] = score
        result["verdict"] = verdict

    mismatch_pairs = sum(len(findings) for findings in cross_findings.values()) // 2
    overall_score, overall_verdict = score_overall(
        [result["authenticity_score"] for result in results],
        mismatch_pairs,
    )
    profile_id = str(uuid.uuid4())
    persisted_data = {
        "documents": [
            {
                "doc_type": result["doc_type"],
                "authenticity_score": result["authenticity_score"],
                "verdict": result["verdict"],
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
    )
    db.add(profile)
    db.commit()

    return VerificationResponse(
        profile_id=profile_id,
        overall=OverallResult(
            authenticity_score=overall_score,
            verdict=overall_verdict,
            documents_processed=len(results),
        ),
        documents=[_to_document_result(result) for result in results],
    )
