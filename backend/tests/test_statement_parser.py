import pytest

from app.services.statement_parser import parse_statement


@pytest.mark.parametrize(
    ("date_text", "expected_date"),
    [
        ("03Sep, 2026", "2026-09-03"),
        ("03 Sep 2026", "2026-09-03"),
        ("Sept 21, 2026", "2026-09-21"),
        ("Sep 14, 2026", "2026-09-14"),
        ("2026-09-03", "2026-09-03"),
        ("03/09/2026", "2026-09-03"),
    ],
)
def test_parser_normalizes_supported_dates(date_text, expected_date):
    text = (
        f"{date_text}\n"
        "Paid to Corner Shop\n"
        "₹1,234.50\n"
        "04 Sep 2026\n"
        "Received from Maya\n"
        "₹2,000.00\n"
        "Sent ₹1,234.50\n"
        "Received ₹2,000.00"
    )

    result = parse_statement(text, "upi_statement")

    assert result.layout_matches
    assert result.transactions[0]["date"] == expected_date
    assert result.transactions[0]["debit"] == 1234.5
    assert result.transactions[0]["credit"] is None
    assert result.transactions[1]["credit"] == 2000
    assert result.transactions[1]["debit"] is None


def test_parser_extracts_amount_with_adjacent_transaction_id():
    text = (
        "03 Sep 2026\n"
        "Paid to Corner Shop\n"
        "UPI Transaction ID: ABCD123456789 ₹5,400.00\n"
        "04 Sep 2026\n"
        "Received from Maya\n"
        "UTR: XYZ123456789 ₹1,250\n"
        "Sent ₹5,400.00\n"
        "Received ₹1,250"
    )

    result = parse_statement(text, "upi_statement")

    assert result.transactions[0]["debit"] == 5400
    assert result.transactions[0]["transaction_id"] == "ABCD123456789"
    assert result.transactions[1]["credit"] == 1250
    assert result.transactions[1]["transaction_id"] == "XYZ123456789"


def test_parser_ignores_headers_and_deduplicates_identical_page_boundary_row():
    repeated = (
        "Date Description Amount\n"
        "03 Sep 2026\n"
        "Paid to Corner Shop\n"
        "UPI Ref No: ABC123456789\n"
        "₹500.00\n"
    )
    second_page = (
        "Date Description Amount\n"
        + repeated.split("Date Description Amount\n", 1)[1]
        + "04 Sep 2026\n"
        "Received from Maya\n"
        "₹700.00\n"
        "Sent ₹500.00\n"
        "Received ₹700.00"
    )
    result = parse_statement(repeated + "\f" + second_page, "upi_statement")

    assert len(result.transactions) == 2
    assert [transaction["debit"] for transaction in result.transactions] == [500, None]
    assert result.transactions[1]["credit"] == 700


def test_parser_keeps_identical_payments_with_different_ids():
    text = (
        "03 Sep 2026\n"
        "Paid to Corner Shop\n"
        "UPI Transaction ID: ABC123456789\n"
        "₹500.00\n"
        "03 Sep 2026\n"
        "Paid to Corner Shop\n"
        "UPI Transaction ID: XYZ123456789\n"
        "₹500.00\n"
        "Sent ₹1,000.00\n"
        "Received ₹0"
    )

    result = parse_statement(text, "upi_statement")

    assert len(result.transactions) == 2
    assert {transaction["transaction_id"] for transaction in result.transactions} == {
        "ABC123456789",
        "XYZ123456789",
    }
    assert result.total_debits == 1000
    assert result.total_credits == 0


def test_parser_extracts_all_month_first_transactions_across_pages():
    first_page = (
        "Sept 21, 2026\n05:19 pm\nPaid to Merchant One\nTransaction ID T123456789\n"
        "UTR No. 919949729727\nPaid by XXXXXX2836\n₹70\n"
        "Sep 14, 2026\n03:29 pm\nPaid to Merchant Two\nTransaction ID T223456789\n"
        "UTR No. 631207541247\nPaid by XXXXXX2836\n₹180\n"
        "Sep 12, 2026\n05:19 pm\nPaid to Merchant Three\nTransaction ID T323456789\n"
        "UTR No. 272354114347\nPaid by XXXXXX2836\n₹15\n"
        "Sep 11, 2026\n05:44 pm\nPaid to Merchant Four\nTransaction ID T423456789\n"
        "UTR No. 640273934869\nPaid by XXXXXX2836\n₹60\n"
        "Aug 20, 2026\n08:05 am\nPaid to Merchant Five\nTransaction ID T523456789\n"
        "UTR No. 448924223053\nPaid by XXXXXX2836\n₹30\n"
        "Aug 15, 2026\n07:51 am\nPaid to Merchant Six\nTransaction ID T623456789\n"
        "UTR No. 76114172140\nPaid by XXXXXX2836\n₹20\n"
        "Aug 13, 2026\n01:13 pm\nPaid to Merchant Seven\nTransaction ID T723456789\n"
        "UTR No. 781674916874\nPaid by XXXXXX2836\n₹10"
    )
    second_page = (
        "Jul 30, 2026\n08:32 am\nPaid to Merchant Eight\nTransaction ID T823456789\n"
        "UTR No. 172740595383\nPaid by XXXXXX2836\n₹15"
    )

    result = parse_statement(first_page + "\f" + second_page, "upi_statement")

    assert result.layout_matches
    assert len(result.transactions) == 8
    assert [transaction["date"] for transaction in result.transactions] == [
        "2026-09-21",
        "2026-09-14",
        "2026-09-12",
        "2026-09-11",
        "2026-08-20",
        "2026-08-15",
        "2026-08-13",
        "2026-07-30",
    ]
    assert [transaction["debit"] for transaction in result.transactions] == [
        70, 180, 15, 60, 30, 20, 10, 15,
    ]
    assert all(transaction["credit"] is None for transaction in result.transactions)


def test_parser_does_not_claim_a_partial_dated_layout_matches():
    text = (
        "Sep 21, 2026\nPaid to Merchant One\n₹70\n"
        "Sep 14, 2026\nPaid to Merchant Two\n₹180\n"
        "Sep 12, 2026\nCard transaction description\n₹15"
    )

    result = parse_statement(text, "upi_statement")

    assert len(result.transactions) == 2
    assert not result.layout_matches


def test_parser_rejects_impossible_dates_and_never_treats_reference_as_amount():
    result = parse_statement(
        "31 Feb 2026\n"
        "Paid to Corner Shop\n"
        "UPI Ref No: 98765432109876\n"
        "01 Mar 2026\n"
        "Received from Maya\n"
        "₹100.00\n"
        "Sent ₹0\n"
        "Received ₹100",
        "bank_statement",
    )

    assert len(result.transactions) == 1
    assert result.transactions[0]["date"] == "2026-03-01"
    assert result.transactions[0]["credit"] == 100
    assert result.total_debits == 0
    assert result.total_credits == 100
    assert result.invalid_date_count == 1
