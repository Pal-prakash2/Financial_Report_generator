from decimal import Decimal

import pytest

from app.services.validation_service import AccountingValidationError, ValidationMessage, ValidationService


def test_validate_balance_sheet_passes_within_tolerance():
    service = ValidationService()
    balance_sheet = {
        "total_assets": Decimal("1000"),
        "total_liabilities": Decimal("600"),
        "total_equity": Decimal("400"),
    }

    result = service.validate_balance_sheet(balance_sheet)

    assert result.is_valid is True
    assert result.difference == Decimal("0")


def test_validate_balance_sheet_raises_when_out_of_balance():
    service = ValidationService()
    balance_sheet = {
        "total_assets": Decimal("1000"),
        "total_liabilities": Decimal("500"),
        "total_equity": Decimal("400"),
    }

    with pytest.raises(AccountingValidationError) as exc:
        service.validate_balance_sheet(balance_sheet)

    assert "Balance sheet does not balance" in str(exc.value)


def test_validate_statements_income_statement_checks():
    service = ValidationService()
    statements = {
        "balance_sheet": {
            "total_assets": {"FY2024": Decimal("1000")},
            "total_liabilities": {"FY2024": Decimal("600")},
            "total_equity": {"FY2024": Decimal("400")},
        },
        "income_statement": {
            "operating_revenue": {"FY2024": Decimal("900")},
            "other_income": {"FY2024": Decimal("100")},
            "total_revenue": {"FY2024": Decimal("1000")},
            "profit_before_tax": {"FY2024": Decimal("150")},
            "tax_expense": {"FY2024": Decimal("30")},
            "profit_after_tax": {"FY2024": Decimal("120")},
        },
    }

    messages = service.validate_statements(statements)

    revenue_message = next(msg for msg in messages if msg.field == "total_revenue")
    assert revenue_message.passed is True

    pat_message = next(msg for msg in messages if msg.field == "profit_after_tax")
    assert pat_message.passed is True


def test_validate_statements_flags_failures():
    service = ValidationService()
    statements = {
        "balance_sheet": {
            "total_assets": {"FY2024": Decimal("1000")},
            "total_liabilities": {"FY2024": Decimal("400")},
            "total_equity": {"FY2024": Decimal("400")},
        },
        "income_statement": {
            "operating_revenue": {"FY2024": Decimal("900")},
            "other_income": {"FY2024": Decimal("100")},
            "total_revenue": {"FY2024": Decimal("1200")},  # mismatch
        },
    }

    messages = service.validate_statements(statements)

    imbalance_message = next(msg for msg in messages if msg.statement == "balance_sheet")
    assert imbalance_message.passed is False

    revenue_message = next(msg for msg in messages if msg.field == "total_revenue")
    assert revenue_message.passed is False
