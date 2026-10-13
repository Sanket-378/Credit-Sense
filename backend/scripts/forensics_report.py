import argparse
import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.forensics import analyze_pdf_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print deterministic PDF tamper-evidence signals."
    )
    parser.add_argument("path", type=Path, help="Path to a PDF")
    parser.add_argument(
        "--doc-type",
        choices=("bank_statement", "upi_statement"),
        default="bank_statement",
    )
    arguments = parser.parse_args()
    if not arguments.path.is_file():
        parser.error(f"PDF not found: {arguments.path}")

    report = analyze_pdf_report(arguments.path, arguments.doc_type)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
