from datetime import date

import pytest

from app.services.consistency import check_consistency, cross_document_name_findings

TODAY = date(2025, 1, 1)


@pytest.mark.parametrize(
    ("doc_type", "data"),
    [
        (
            "salary_slip",
            {
                "employee_name": "Asha Rao", "employer_name": "Acme", "month": "December 2024",
                "gross_salary": 50000, "total_deductions": 5000, "net_salary": 45000,
            },
        ),
        (
            "bank_statement",
            {
                "account_holder": "Asha Rao", "period_start": "2024-12-01", "period_end": "2024-12-31",
                "opening_balance": 1000, "total_credits": 5000, "total_debits": 2000,
                "closing_balance": 4000, "transactions": [{"debit": 2000, "credit": 5000, "balance": 4000}],
            },
        ),
        (
            "upi_statement",
            {
                "account_holder": "Asha Rao", "period_start": "2024-12-01", "period_end": "2024-12-31",
                "total_credits": 5000, "total_debits": 2000,
                "transactions": [{"debit": 2000, "credit": 5000}],
            },
        ),
        (
            "invoice",
            {
                "seller_name": "Acme", "buyer_name": "Asha Rao", "invoice_number": "A-1",
                "invoice_date": "2024-12-31", "subtotal": 1000, "tax_amount": 180, "total_amount": 1180,
            },
        ),
        (
            "id_proof",
            {"full_name": "Asha Rao", "id_type": "PAN", "id_number_masked": "******1234", "date_of_birth": "1990-01-01"},
        ),
    ],
)
def test_valid_document_consistency(doc_type, data):
    findings, missing = check_consistency(doc_type, data, today=TODAY)
    assert findings == []
    assert missing == []


@pytest.mark.parametrize(
    ("doc_type", "data", "expected_check"),
    [
        (
            "salary_slip",
            {"employee_name": "A", "employer_name": "B", "month": "2024-12", "gross_salary": 50000, "total_deductions": 5000, "net_salary": 40000},
            "salary_arithmetic",
        ),
        (
            "bank_statement",
            {"account_holder": "A", "period_start": "2024-12-01", "period_end": "2024-12-31", "opening_balance": 1000, "total_credits": 5000, "total_debits": 2000, "closing_balance": 5000},
            "statement_arithmetic",
        ),
        (
            "invoice",
            {"seller_name": "A", "buyer_name": "B", "invoice_number": "1", "invoice_date": "2024-12-01", "subtotal": 1000, "tax_amount": 100, "total_amount": 1200},
            "invoice_arithmetic",
        ),
        (
            "id_proof",
            {"full_name": "A", "id_type": "PAN", "id_number_masked": "******1234", "date_of_birth": "2030-01-01"},
            "future_date",
        ),
    ],
)
def test_invalid_document_consistency(doc_type, data, expected_check):
    findings, _ = check_consistency(doc_type, data, today=TODAY)
    assert expected_check in {finding["check"] for finding in findings}


def test_currency_tolerance_accepts_one_unit_and_one_percent():
    salary = {
        "employee_name": "A", "employer_name": "B", "month": "2024-12",
        "gross_salary": 10000, "total_deductions": 1000, "net_salary": 9090,
    }
    findings, _ = check_consistency("salary_slip", salary, today=TODAY)
    assert "salary_arithmetic" not in {finding["check"] for finding in findings}


def test_currency_tolerance_rejects_difference_over_one_percent():
    invoice = {
        "seller_name": "A", "buyer_name": "B", "invoice_number": "1",
        "invoice_date": "2024-12-01", "subtotal": 10000, "tax_amount": 1000,
        "total_amount": 11200,
    }
    findings, _ = check_consistency("invoice", invoice, today=TODAY)
    assert "invoice_arithmetic" in {finding["check"] for finding in findings}


def test_net_salary_must_not_exceed_gross_even_within_tolerance():
    salary = {
        "employee_name": "A", "employer_name": "B", "month": "2024-12",
        "gross_salary": 10000, "total_deductions": 0, "net_salary": 10000.5,
    }
    findings, _ = check_consistency("salary_slip", salary, today=TODAY)
    assert "salary_range" in {finding["check"] for finding in findings}


def test_missing_required_fields_are_reported():
    findings, missing = check_consistency("id_proof", {"full_name": "A"}, today=TODAY)
    assert set(missing) == {"id_type", "id_number_masked", "date_of_birth"}
    assert findings[0]["check"] == "required_fields"


def test_statement_transaction_totals_match():
    data = {
        "account_holder": "Asha Rao",
        "period_start": "2024-12-01",
        "period_end": "2024-12-31",
        "total_credits": 500,
        "total_debits": 150,
        "transactions": [
            {"credit": 200, "debit": None},
            {"credit": 300, "debit": None},
            {"credit": None, "debit": 150},
        ],
    }

    findings, _ = check_consistency("upi_statement", data, today=TODAY)

    assert not {"statement_credit_total", "statement_debit_total"}.intersection(
        finding["check"] for finding in findings
    )


def test_statement_total_mismatch_identifies_possible_misclassified_transaction():
    data = {
        "account_holder": "Asha Rao",
        "period_start": "2024-12-01",
        "period_end": "2024-12-31",
        "total_credits": 150,
        "total_debits": 0,
        "transactions": [{"description": "Paid to shop", "debit": 150, "credit": None}],
    }

    findings, _ = check_consistency("upi_statement", data, today=TODAY)

    finding = next(item for item in findings if item["check"] == "statement_credit_total")
    assert finding["severity"] == "medium"
    assert "₹150.00" in finding["detail"]
    assert "difference ₹150.00" in finding["detail"]
    assert "possible misclassified transaction" in finding["detail"].lower()


def test_upi_statement_does_not_require_or_check_balances():
    data = {
        "account_holder": "Asha Rao",
        "period_start": "2024-12-01",
        "period_end": "2024-12-31",
        "total_credits": 0,
        "total_debits": 0,
        "transactions": [],
    }

    findings, missing = check_consistency("upi_statement", data, today=TODAY)

    assert missing == []
    assert not any(finding["check"] == "balance_reconciliation" for finding in findings)


def test_bank_statement_without_balances_gets_low_severity_notice_not_missing_fields():
    data = {
        "account_holder": "Asha Rao",
        "period_start": "2024-12-01",
        "period_end": "2024-12-31",
        "total_credits": 0,
        "total_debits": 0,
        "transactions": [],
    }

    findings, missing = check_consistency("bank_statement", data, today=TODAY)

    assert "opening_balance" not in missing
    assert "closing_balance" not in missing
    balance_finding = next(item for item in findings if item["check"] == "balance_reconciliation")
    assert balance_finding["severity"] == "low"
    assert balance_finding["detail"] == "Balance reconciliation not possible: no balances found"


def test_bank_statement_with_one_balance_still_reports_the_other_as_missing():
    data = {
        "account_holder": "Asha Rao",
        "period_start": "2024-12-01",
        "period_end": "2024-12-31",
        "opening_balance": 1000,
        "total_credits": 0,
        "total_debits": 0,
        "transactions": [],
    }

    _, missing = check_consistency("bank_statement", data, today=TODAY)

    assert missing == ["closing_balance"]


def test_cross_document_holder_names_flag_mismatch():
    documents = [
        {"doc_type": "salary_slip", "extracted_data": {"employee_name": "Asha Rao"}},
        {"doc_type": "id_proof", "extracted_data": {"full_name": "Maya Shah"}},
    ]
    findings = cross_document_name_findings(documents, threshold=0.82)
    assert set(findings) == {0, 1}


def test_cross_document_business_names_flag_mismatch():
    documents = [
        {"doc_type": "salary_slip", "extracted_data": {"employer_name": "Acme Finance"}},
        {"doc_type": "invoice", "extracted_data": {"seller_name": "Northwind Traders"}},
    ]
    findings = cross_document_name_findings(documents, threshold=0.82)
    assert set(findings) == {0, 1}
