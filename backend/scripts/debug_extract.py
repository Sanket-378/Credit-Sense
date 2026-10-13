import argparse
import json
from pathlib import Path
import sys

import pymupdf as fitz

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import get_settings
from app.services.extractor import extract_document
from app.services.reader import read_document


def main() -> int:
    argument_parser = argparse.ArgumentParser(
        description="Print PDF text-layer pages and extracted statement totals."
    )
    argument_parser.add_argument("path", type=Path, help="Path to a statement PDF")
    argument_parser.add_argument(
        "--doc-type",
        choices=("upi_statement", "bank_statement"),
        default="upi_statement",
    )
    arguments = argument_parser.parse_args()

    if not arguments.path.is_file():
        argument_parser.error(f"PDF not found: {arguments.path}")

    with fitz.open(arguments.path) as document:
        pages = [page.get_text("text") for page in document]

    for index, page_text in enumerate(pages, start=1):
        print(f"--- Page {index} text layer (first 3000 chars) ---")
        print(page_text[:3000])

    settings = get_settings()
    read_result = read_document(arguments.path, "pdf", settings.ocr_language_list)
    extraction = extract_document(
        read_result.text,
        arguments.doc_type,
        settings,
    )
    extracted = extraction.data
    transactions = extracted.get("transactions", [])
    debit_total = sum(
        (transaction.get("debit") or 0)
        for transaction in transactions
        if isinstance(transaction, dict)
    )
    credit_total = sum(
        (transaction.get("credit") or 0)
        for transaction in transactions
        if isinstance(transaction, dict)
    )

    print("--- Extracted transactions ---")
    print(json.dumps(transactions, indent=2, ensure_ascii=False))
    print("--- Extracted totals ---")
    print(json.dumps({
        "extraction_method": extraction.extraction_method,
        "extraction_confidence": extraction.extraction_confidence,
        "transaction_count": len(transactions),
        "debit_sum": debit_total,
        "stated_total_debits": extracted.get("total_debits"),
        "credit_sum": credit_total,
        "stated_total_credits": extracted.get("total_credits"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
