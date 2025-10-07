from decimal import Decimal

import pytest

from app.services.validation_service import AccountingValidationError, ValidationService


def test_validate_balance_sheet_passes_within_tolerance():
    service = ValidationService(tolerance=Decimal("100"))
    balance_sheet = {
        "total_assets": Decimal("1000"),
        "total_liabilities": Decimal("600"),
        "total_equity": Decimal("400"),
    }

    result = service.validate_balance_sheet(balance_sheet)

    assert result.is_valid is True
    assert result.difference == Decimal("0")


def test_validate_balance_sheet_raises_when_out_of_balance():
    service = ValidationService(tolerance=Decimal("10"))
    balance_sheet = {
        "total_assets": Decimal("1000"),
        "total_liabilities": Decimal("500"),
        "total_equity": Decimal("400"),
    }

    with pytest.raises(AccountingValidationError) as exc:
        service.validate_balance_sheet(balance_sheet)

    assert "Balance sheet does not balance" in str(exc.value)
