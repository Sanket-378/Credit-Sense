import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

DATE_PATTERN = re.compile(
    r"^\s*(\d{4}-\d{2}-\d{2}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}|"
    r"\d{1,2}\s*[A-Za-z]{3,9},?\s*\d{4}|\d{1,2}/\d{1,2}/\d{4})"
)
MIN_TRANSACTIONS_FOR_PARSER = 2
AMOUNT_PATTERN = re.compile(r"₹\s*([0-9][0-9,]*(?:\.\d{1,2})?)")
DIRECTION_PATTERNS = (
    ("debit", re.compile(r"^\s*(Paid to|Payment to|Sent to)\b\s*(.*)$", re.IGNORECASE)),
    ("credit", re.compile(r"^\s*(Received from|Refund)\b\s*(.*)$", re.IGNORECASE)),
)
TRANSACTION_ID_PATTERN = re.compile(
    r"\b(?:UPI\s*)?(?:transaction|txn|reference|ref|rrn|utr)\s*(?:id|no\.?|number)?\s*[:#-]?\s*([A-Z0-9-]{6,})\b",
    re.IGNORECASE,
)
TIME_PATTERN = re.compile(r"\b(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\b", re.IGNORECASE)
ACCOUNT_HOLDER_PATTERN = re.compile(
    r"^\s*(?:name|statement\s+for|account\s+holder)\s*(?::|-)?\s*([^\r\n]+)",
    re.IGNORECASE | re.MULTILINE,
)
ACCOUNT_NUMBER_PATTERN = re.compile(
    r"^\s*(?:account(?:\s+number)?|a/c(?:\s+no\.?)?)\s*[:#-]?\s*([0-9 -]{4,})",
    re.IGNORECASE | re.MULTILINE,
)
SUMMARY_AMOUNT = r"(?:₹\s*)?([0-9][0-9,]*(?:\.\d{1,2})?)"
SUMMARY_PATTERNS = {
    "total_debits": re.compile(
        rf"^\s*(?:total\s+)?(?:sent|paid|debits?)\s*[:\-]?\s*{SUMMARY_AMOUNT}\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    "total_credits": re.compile(
        rf"^\s*(?:total\s+)?(?:received|credits?)\s*[:\-]?\s*{SUMMARY_AMOUNT}\s*$",
        re.IGNORECASE | re.MULTILINE,
    ),
}
NOISE_LINE_PATTERN = re.compile(
    r"^\s*(?:upi\s*)?(?:transaction|txn|reference|ref|rrn|utr)\b",
    re.IGNORECASE,
)


@dataclass
class StatementParseResult:
    transactions: list[dict[str, Any]]
    total_debits: float | None
    total_credits: float | None
    account_holder: str | None
    account_last4: str | None
    layout_matches: bool
    invalid_date_count: int


def _normalize_date(value: str) -> str | None:
    candidate = re.sub(r"\s+", " ", value.strip().rstrip(","))
    candidate = re.sub(r"\bSept(?=\s)", "Sep", candidate, flags=re.IGNORECASE)
    formats = (
        "%Y-%m-%d",
        "%b %d, %Y",
        "%b %d %Y",
        "%B %d, %Y",
        "%B %d %Y",
        "%d%b, %Y",
        "%d%b %Y",
        "%d %b, %Y",
        "%d %b %Y",
        "%d%B, %Y",
        "%d%B %Y",
        "%d %B, %Y",
        "%d %B %Y",
        "%d/%m/%Y",
    )
    for date_format in formats:
        try:
            return datetime.strptime(candidate, date_format).date().isoformat()
        except ValueError:
            continue
    return None


def _date_at_line_start(line: str) -> tuple[str, str] | None:
    match = DATE_PATTERN.match(line)
    if match is None:
        return None
    normalized = _normalize_date(match.group(1))
    if normalized is None:
        return None
    return normalized, line[match.end():].strip(" \t,|•-")


def _amount(line: str) -> float | None:
    match = AMOUNT_PATTERN.search(line)
    if match is None:
        return None
    return float(match.group(1).replace(",", ""))


def _summary_total(text: str, field: str) -> float | None:
    matches = list(SUMMARY_PATTERNS[field].finditer(text.replace("\f", "\n")))
    if not matches:
        return None
    return float(matches[-1].group(1).replace(",", ""))


def _transaction_id(lines: list[str]) -> str | None:
    for line in lines:
        match = TRANSACTION_ID_PATTERN.search(line)
        if match:
            return match.group(1).upper()
    return None


def _parse_page(page_text: str, page_number: int) -> list[dict[str, Any]]:
    lines = page_text.splitlines()
    dated_lines = [
        (index, *_date_at_line_start(line))
        for index, line in enumerate(lines)
        if _date_at_line_start(line) is not None
    ]
    transactions: list[dict[str, Any]] = []
    for dated_index, (line_index, normalized_date, date_suffix) in enumerate(dated_lines):
        block_end = (
            dated_lines[dated_index + 1][0]
            if dated_index + 1 < len(dated_lines)
            else len(lines)
        )
        block = lines[line_index:block_end]
        direction_matches: list[tuple[int, str, str, str]] = []
        if date_suffix:
            for direction, pattern in DIRECTION_PATTERNS:
                match = pattern.match(date_suffix)
                if match:
                    direction_matches.append((0, direction, match.group(1), match.group(2)))
                    break
        for relative_index, line in enumerate(block[1:], start=1):
            for direction, pattern in DIRECTION_PATTERNS:
                match = pattern.match(line)
                if match:
                    direction_matches.append(
                        (relative_index, direction, match.group(1), match.group(2))
                    )
                    break

        for match_index, (direction_index, direction, keyword, suffix) in enumerate(direction_matches):
            next_direction_index = (
                direction_matches[match_index + 1][0]
                if match_index + 1 < len(direction_matches)
                else len(block)
            )
            details = [suffix]
            supporting_lines = [block[direction_index]] if direction_index < len(block) else []
            if direction_index == 0 and date_suffix:
                supporting_lines.append(date_suffix)
            for supporting_line in block[direction_index + 1:next_direction_index]:
                has_amount = AMOUNT_PATTERN.search(supporting_line) is not None
                if not supporting_line.strip() or (
                    NOISE_LINE_PATTERN.match(supporting_line) and not has_amount
                ):
                    continue
                if has_amount:
                    supporting_lines.append(supporting_line)
                    break
                if TIME_PATTERN.search(supporting_line):
                    supporting_lines.append(supporting_line)
                    continue
                details.append(supporting_line.strip())
                supporting_lines.append(supporting_line)

            amount = next(
                (
                    parsed_amount
                    for supporting_line in supporting_lines
                    if (parsed_amount := _amount(supporting_line)) is not None
                ),
                None,
            )
            if amount is None:
                continue

            description = " ".join(
                part.strip()
                for part in [keyword, *details]
                if part and part.strip()
            )
            description = re.sub(r"\s+", " ", description).strip()
            description = TRANSACTION_ID_PATTERN.sub("", description).strip(" :-")
            if not description:
                continue

            time_match = next(
                (
                    match.group(1).upper()
                    for supporting_line in [*block[:direction_index + 1], *supporting_lines]
                    if (match := TIME_PATTERN.search(supporting_line))
                ),
                None,
            )
            transaction = {
                "date": normalized_date,
                "description": description,
                "debit": amount if direction == "debit" else None,
                "credit": amount if direction == "credit" else None,
                "transaction_id": _transaction_id(block[direction_index:next_direction_index]),
                "time": time_match,
                "_page": page_number,
            }
            transactions.append(transaction)
    return transactions


def _deduplicate_page_boundary_rows(
    pages: list[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for page_index, page_transactions in enumerate(pages):
        current = [transaction.copy() for transaction in page_transactions]
        if (
            page_index
            and result
            and current
            and result[-1].get("_page") == page_index - 1
        ):
            previous_last = result[-1]
            current_first = current[0]
            duplicate_fields = (
                "date",
                "description",
                "debit",
                "credit",
                "transaction_id",
                "time",
            )
            if all(previous_last.get(field) == current_first.get(field) for field in duplicate_fields):
                current.pop(0)
        result.extend(current)
    for transaction in result:
        transaction.pop("_page", None)
    return result


def _account_holder(text: str) -> str | None:
    match = ACCOUNT_HOLDER_PATTERN.search(text)
    if match is None:
        return None
    name = match.group(1).strip()
    if "@" in name or not name or sum(character.isdigit() for character in name) > len(name) / 2:
        return None
    return name


def _account_last4(text: str) -> str | None:
    match = ACCOUNT_NUMBER_PATTERN.search(text)
    if match is None:
        return None
    digits = re.sub(r"\D", "", match.group(1))
    return digits[-4:] if digits else None


def parse_statement(text: str, doc_type: str) -> StatementParseResult:
    if doc_type not in ("upi_statement", "bank_statement"):
        raise ValueError("Unsupported statement document type.")

    page_texts = text.split("\f")
    transactions_by_page = [
        _parse_page(page_text, page_number)
        for page_number, page_text in enumerate(page_texts)
    ]
    transactions = _deduplicate_page_boundary_rows(transactions_by_page)
    detected_date_count = sum(
        1
        for line in text.splitlines()
        if _date_at_line_start(line) is not None
    )
    invalid_date_count = sum(
        1
        for line in text.splitlines()
        if (match := DATE_PATTERN.match(line)) is not None
        and _normalize_date(match.group(1)) is None
    )
    direction_count = sum(
        1
        for line in text.splitlines()
        if any(pattern.match(line) for _, pattern in DIRECTION_PATTERNS)
    )
    amount_count = len(AMOUNT_PATTERN.findall(text))
    layout_matches = (
        detected_date_count > 0
        and direction_count > 0
        and amount_count > 0
        and len(transactions) >= MIN_TRANSACTIONS_FOR_PARSER
        and len(transactions) >= detected_date_count
    )

    return StatementParseResult(
        transactions=transactions,
        total_debits=_summary_total(text, "total_debits"),
        total_credits=_summary_total(text, "total_credits"),
        account_holder=_account_holder(text),
        account_last4=_account_last4(text),
        layout_matches=layout_matches,
        invalid_date_count=invalid_date_count,
    )
