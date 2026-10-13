# CreditSense verification API

FastAPI backend for document verification. It uses Groq for structured text extraction, optionally cross-checks numeric fields with a vision model, and stores extracted fields and scores (not uploaded files) in SQLite.

## Setup

From the repository root, create and activate a Python 3.11+ virtual environment:

```powershell
py -3.11 -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Edit `backend\.env` and set `GROQ_API_KEY` and `GROQ_TEXT_MODEL`. Choose model names from the current Groq console model list; they are intentionally not hardcoded. `GROQ_REASONING_EFFORT` defaults to `low`, and `MAX_COMPLETION_TOKENS` defaults to `4096` for reasoning models. `GROQ_VISION_MODEL` is optional and is only used when `ENABLE_VISION_CROSSCHECK=true`. Set `OCR_LANGUAGES` to a comma-separated list if languages other than English are needed, adjust `ELA_RATIO_THRESHOLD` to tune image forensics, and adjust `NAME_MATCH_THRESHOLD` to tune cross-document name matching. EasyOCR downloads its selected language model the first time image OCR is used.

## Run

From the `backend` directory with the virtual environment active:

```powershell
uvicorn app.main:app --reload --port 8001
```

The health check is at `http://127.0.0.1:8001/health`; interactive API documentation is at `http://127.0.0.1:8001/docs`. Use the `/api/documents/verify` form there to upload one or more documents and provide a matching `doc_types` value for each file.

## Test

From the `backend` directory:

```powershell
pytest
```

The consistency, scoring and forensics tests are offline and do not call Groq.

## Privacy and response contract

Uploads are size- and signature-validated, held in temporary files only while processed, and removed even if processing fails. Original documents and OCR text are never persisted. ID numbers are masked before extracted data is returned or stored. SQLite stores the profile UUID, overall score/verdict, extracted fields and per-document scores/verdicts.

The verification endpoint accepts PDF, JPG/JPEG and PNG files up to `MAX_FILE_MB` each, with at most 10 files per request. `doc_types` must match the number and order of uploaded files and use `salary_slip`, `bank_statement`, `upi_statement`, `invoice` or `id_proof`. Per-document responses include `checks_performed` and `checks_skipped`; a verified verdict requires at least two completed consistency checks.
