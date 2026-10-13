from datetime import date, datetime
from difflib import SequenceMatcher
from typing import Any

from .extractor import REQUIRED_FIELDS

AMOUNT_TOLERANCE = 1.0
DATE_FIELDS = (
    "period_start",
    "period_end",
    "invoice_date",
    "date_of_birth",
)
HOLDER_NAME_FIELDS = {
    "salary_slip": "employee_name",
    "bank_statement": "account_holder",
    "upi_statement": "account_holder",
    "id_proof": "full_name",
}


def _finding(check: str, detail: str, severity: str = "medium") -> dict[str, str]:
    return {"check": check, "severity": severity, "detail": detail}


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(str(value).replace(",", "").replace("₹", "").strip())
    except (TypeError, ValueError):
        return None


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()
    try:
        return date.fromisoformat(candidate[:10])
    except ValueError:
        pass
    for pattern in ("%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%B %Y", "%b %Y", "%m/%Y"):
        try:
            parsed = datetime.strptime(candidate, pattern).date()
            if pattern in ("%B %Y", "%b %Y", "%m/%Y"):
                return parsed.replace(day=1)
            return parsed
        except ValueError:
            continue
    return None


def _amounts_match(expected: float, actual: float) -> bool:
    tolerance = max(AMOUNT_TOLERANCE, abs(expected) * 0.01)
    return abs(expected - actual) <= tolerance


def _format_amount(value: float) -> str:
    return f"₹{value:,.2f}"


def _possible_misclassified_transaction(
    transactions: list[Any],
    difference: float,
) -> bool:
    return any(
        isinstance(transaction, dict)
        and any(
            amount is not None and abs(abs(amount) - abs(difference)) <= AMOUNT_TOLERANCE
            for amount in (_number(transaction.get("debit")), _number(transaction.get("credit")))
        )
        for transaction in transactions
    )


def _bank_statement_has_balances(data: dict[str, Any]) -> bool:
    if any(
        _number(data.get(field)) is not None
        for field in ("opening_balance", "closing_balance")
    ):
        return True
    transactions = data.get("transactions")
    return isinstance(transactions, list) and any(
        isinstance(transaction, dict)
        and _number(transaction.get("balance")) is not None
        for transaction in transactions
    )


def _check_dates(
    data: dict[str, Any],
    doc_type: str,
    today: date,
) -> list[dict[str, str]]:
    findings = []
    keys = list(DATE_FIELDS)
    if doc_type == "salary_slip":
        keys.append("month")
    for key in keys:
        value = data.get(key)
        if value is None or value == "":
            continue
        parsed = _parse_date(value)
        if parsed is None:
            findings.append(_finding("date_format", f"The {key.replace('_', ' ')} is not a parseable date."))
        elif parsed > today:
            findings.append(_finding("future_date", f"The {key.replace('_', ' ')} is in the future."))

    transactions_value = data.get("transactions")
    transactions = transactions_value if isinstance(transactions_value, list) else []
    for index, transaction in enumerate(transactions):
        if not isinstance(transaction, dict) or not transaction.get("date"):
            continue
        parsed = _parse_date(transaction["date"])
        if parsed is None:
            findings.append(_finding("transaction_date_format", f"Transaction {index + 1} has an unparseable date."))
        elif parsed > today:
            findings.append(_finding("transaction_future_date", f"Transaction {index + 1} is dated in the future."))
    return findings


def check_consistency_with_coverage(
    doc_type: str,
    data: dict[str, Any],
    today: date | None = None,
) -> tuple[list[dict[str, str]], list[str], list[str], list[dict[str, str]]]:
    if doc_type not in REQUIRED_FIELDS:
        raise ValueError("Unsupported document type.")
    current_date = today or date.today()
    findings = []
    checks_performed = ["required_fields"]
    checks_skipped: list[dict[str, str]] = []

    def skip_check(name: str, reason: str) -> None:
        checks_skipped.append({"name": name, "reason": reason})

    required_fields = REQUIRED_FIELDS[doc_type]
    if doc_type == "bank_statement" and not _bank_statement_has_balances(data):
        required_fields = [
            field for field in required_fields
            if field not in ("opening_balance", "closing_balance")
        ]
    missing_fields = [
        field for field in required_fields
        if data.get(field) is None or data.get(field) == ""
    ]
    if missing_fields:
        findings.append(
            _finding(
                "required_fields",
                f"Required fields are missing: {', '.join(missing_fields)}.",
                "low",
            )
        )

    if doc_type == "salary_slip":
        gross = _number(data.get("gross_salary"))
        deductions = _number(data.get("total_deductions"))
        net = _number(data.get("net_salary"))
        if gross is not None and deductions is not None and net is not None:
            checks_performed.append("salary_arithmetic")
            if not _amounts_match(gross - deductions, net):
                findings.append(_finding("salary_arithmetic", "Gross salary minus deductions does not match net salary."))
        else:
            skip_check("salary_arithmetic", "Gross salary, total deductions, and net salary are all needed.")
        if gross is not None and net is not None:
            checks_performed.append("salary_range")
            if net <= 0 or net > gross:
                findings.append(_finding("salary_range", "Net salary must be positive and no greater than gross salary."))
        else:
            skip_check("salary_range", "Gross salary and net salary are needed.")

    elif doc_type in ("bank_statement", "upi_statement"):
        transactions_value = data.get("transactions")
        transactions = transactions_value if isinstance(transactions_value, list) else []
        valid_transactions = all(isinstance(transaction, dict) for transaction in transactions)
        if transactions_value is not None and not isinstance(transactions_value, list):
            valid_transactions = False
            findings.append(_finding("transaction_shape", "The transaction list has an invalid structure."))
        if not valid_transactions:
            findings.extend(
                _finding("transaction_shape", f"Transaction {index + 1} has an invalid structure.")
                for index, transaction in enumerate(transactions)
                if not isinstance(transaction, dict)
            )

        for amount_key, check_name, label in (
            ("credit", "statement_credit_total", "credits"),
            ("debit", "statement_debit_total", "debits"),
        ):
            stated_total = _number(data.get(f"total_{amount_key}s"))
            if stated_total is None:
                skip_check(check_name, f"total_{amount_key}s was not extracted.")
                continue
            if transactions_value is None or not isinstance(transactions_value, list) or not valid_transactions:
                skip_check(check_name, "A complete transaction list is needed.")
                continue
            transaction_values = [
                _number(transaction.get(amount_key))
                for transaction in transactions
            ]
            if any(
                transaction.get(amount_key) is not None and value is None
                for transaction, value in zip(transactions, transaction_values, strict=True)
            ):
                skip_check(check_name, "Some transaction amounts could not be read as numbers.")
                continue
            checks_performed.append(check_name)
            transaction_total = sum(value or 0.0 for value in transaction_values)
            difference = transaction_total - stated_total
            if abs(difference) > AMOUNT_TOLERANCE:
                detail = (
                    f"Transaction {label} total {_format_amount(transaction_total)} does not match "
                    f"stated total {_format_amount(stated_total)}; difference "
                    f"{_format_amount(abs(difference))}."
                )
                if _possible_misclassified_transaction(transactions, difference):
                    detail += " Possible misclassified transaction."
                findings.append(_finding(check_name, detail))

        if doc_type == "bank_statement":
            opening = _number(data.get("opening_balance"))
            closing = _number(data.get("closing_balance"))
            credits = _number(data.get("total_credits"))
            debits = _number(data.get("total_debits"))
            has_any_balance = _bank_statement_has_balances(data)
            if all(value is not None for value in (opening, credits, debits, closing)):
                checks_performed.append("balance_reconciliation")
                if not _amounts_match(opening + credits - debits, closing):
                    findings.append(_finding("statement_arithmetic", "Opening balance plus credits minus debits does not match closing balance."))
            else:
                reason = (
                    "No opening, closing, or transaction balances were found."
                    if not has_any_balance
                    else "Opening balance, closing balance, total credits, and total debits are needed."
                )
                skip_check("balance_reconciliation", reason)
                if not has_any_balance:
                    findings.append(
                        _finding(
                            "balance_reconciliation",
                            "Balance reconciliation not possible: no balances found",
                            "low",
                        )
                    )

            running_balance = opening
            running_balance_checked = False
            for index, transaction in enumerate(transactions):
                if not isinstance(transaction, dict):
                    continue
                debit = _number(transaction.get("debit")) or 0.0
                credit = _number(transaction.get("credit")) or 0.0
                balance = _number(transaction.get("balance"))
                if running_balance is not None and balance is not None:
                    running_balance_checked = True
                    expected_balance = running_balance + credit - debit
                    if not _amounts_match(expected_balance, balance):
                        findings.append(_finding("running_balance", f"Transaction {index + 1} does not follow the previous running balance."))
                if balance is not None:
                    running_balance = balance
            if running_balance_checked:
                checks_performed.append("running_balance")
            else:
                skip_check("running_balance", "An opening or sequential transaction balances are needed.")

        period_start = _parse_date(data.get("period_start"))
        period_end = _parse_date(data.get("period_end"))
        if period_start and period_end:
            checks_performed.append("statement_period")
            if period_end <= period_start:
                findings.append(_finding("statement_period", "The statement end date must be after its start date."))
        else:
            skip_check("statement_period", "Both statement period dates are needed.")

    elif doc_type == "invoice":
        subtotal = _number(data.get("subtotal"))
        tax_amount = _number(data.get("tax_amount"))
        total = _number(data.get("total_amount"))
        if all(value is not None for value in (subtotal, tax_amount, total)):
            checks_performed.append("invoice_arithmetic")
            if not _amounts_match(subtotal + tax_amount, total):
                findings.append(_finding("invoice_arithmetic", "Subtotal plus tax does not match the invoice total."))
        else:
            skip_check("invoice_arithmetic", "Subtotal, tax amount, and total amount are all needed.")

    date_values = [
        value for key, value in data.items()
        if key in DATE_FIELDS or (doc_type == "salary_slip" and key == "month")
    ]
    transactions = data.get("transactions")
    if isinstance(transactions, list):
        date_values.extend(
            transaction.get("date")
            for transaction in transactions
            if isinstance(transaction, dict)
        )
    if any(value is not None and value != "" for value in date_values):
        checks_performed.append("date_validation")
    else:
        skip_check("date_validation", "No document or transaction dates were available to validate.")

    findings.extend(_check_dates(data, doc_type, current_date))
    return findings, missing_fields, checks_performed, checks_skipped


def check_consistency(
    doc_type: str,
    data: dict[str, Any],
    today: date | None = None,
) -> tuple[list[dict[str, str]], list[str]]:
    findings, missing_fields, _, _ = check_consistency_with_coverage(doc_type, data, today)
    return findings, missing_fields


def cross_document_name_findings(
    documents: list[dict[str, Any]],
    threshold: float,
) -> dict[int, list[dict[str, str]]]:
    groups: dict[str, list[tuple[int, str]]] = {
        "document_holder": [],
        "business_entity": [],
        "invoice_buyer": [],
    }
    for index, document in enumerate(documents):
        doc_type = document["doc_type"]
        extracted = document["extracted_data"]
        if doc_type in HOLDER_NAME_FIELDS:
            name = extracted.get(HOLDER_NAME_FIELDS[doc_type])
            if isinstance(name, str) and name.strip():
                groups["document_holder"].append((index, name.strip()))
        employer = extracted.get("employer_name")
        if doc_type == "salary_slip" and isinstance(employer, str) and employer.strip():
            groups["business_entity"].append((index, employer.strip()))
        if doc_type == "invoice":
            for field in ("seller_name", "buyer_name"):
                name = extracted.get(field)
                if isinstance(name, str) and name.strip():
                    target_group = "business_entity" if field == "seller_name" else "invoice_buyer"
                    groups[target_group].append((index, name.strip()))

    mismatches: dict[int, list[dict[str, str]]] = {}
    for group in groups.values():
        if len(group) < 2:
            continue
        baseline_index, baseline_name = group[0]
        for current_index, current_name in group[1:]:
            similarity = SequenceMatcher(None, baseline_name.casefold(), current_name.casefold()).ratio()
            if similarity < threshold:
                finding = _finding(
                    "cross_document_name",
                    "A name differs from another document of the same identity category in this request.",
                )
                mismatches.setdefault(baseline_index, []).append(finding)
                mismatches.setdefault(current_index, []).append(finding.copy())
    return mismatches
