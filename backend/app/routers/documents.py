import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..database import get_db
from ..models import VerificationUser
from ..schemas import VerificationResponse
from ..services.extractor import ExtractionServiceError
from ..services.file_handler import (
    SavedUpload,
    UploadValidationError,
    delete_temporary_upload,
    validate_and_save_upload,
)
from ..services.pipeline import process_documents

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)
ALLOWED_DOC_TYPES = {"salary_slip", "bank_statement", "upi_statement", "invoice", "id_proof"}
MAX_FILES_PER_REQUEST = 10


@router.post("/verify", response_model=VerificationResponse)
async def verify_documents(
    files: list[UploadFile] = File(...),
    doc_types: list[str] = Form(...),
    user_id: UUID | None = Header(default=None, alias="X-User-ID"),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    if len(files) != len(doc_types):
        raise HTTPException(
            status_code=400,
            detail="The number of doc_types must match the number of uploaded files.",
        )
    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one document.")
    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"A maximum of {MAX_FILES_PER_REQUEST} documents can be verified per request.",
        )
    unsupported = [doc_type for doc_type in doc_types if doc_type not in ALLOWED_DOC_TYPES]
    if unsupported:
        raise HTTPException(
            status_code=400,
            detail="Unsupported document type. Use salary_slip, bank_statement, upi_statement, invoice, or id_proof.",
        )
    if not settings.groq_api_key.strip() or not settings.groq_text_model.strip():
        raise HTTPException(
            status_code=503,
            detail="Document verification is not configured. Set GROQ_API_KEY and GROQ_TEXT_MODEL in backend/.env.",
        )

    saved_uploads: list[tuple[str, str, SavedUpload]] = []
    try:
        for upload, doc_type in zip(files, doc_types, strict=True):
            try:
                saved = await validate_and_save_upload(
                    upload,
                    settings.max_file_mb * 1024 * 1024,
                )
            except UploadValidationError as error:
                raise HTTPException(status_code=400, detail=str(error)) from error
            saved_uploads.append((upload.filename or "document", doc_type, saved))
        resolved_user_id = str(user_id or uuid4())
        if db.get(VerificationUser, resolved_user_id) is None:
            db.add(VerificationUser(id=resolved_user_id))
            db.flush()
        return await process_documents(saved_uploads, settings, db, resolved_user_id)
    except HTTPException:
        for _, _, saved in saved_uploads:
            delete_temporary_upload(saved)
        raise
    except Exception as error:
        for _, _, saved in saved_uploads:
            delete_temporary_upload(saved)
        logger.error("Document verification request failed.")
        if isinstance(error, ExtractionServiceError):
            raise HTTPException(status_code=503, detail=str(error)) from error
        raise HTTPException(status_code=500, detail="Document verification could not be completed.") from error
