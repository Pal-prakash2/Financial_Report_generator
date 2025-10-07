from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, Optional

from app.utils.constants import ACCOUNTING_TOLERANCE


class AccountingValidationError(ValueError):
    """Raised when an accounting identity is violated beyond tolerance."""

    def __init__(self, message: str, *, difference: Decimal) -> None:
        super().__init__(message)
        self.difference = difference


@dataclass(slots=True)
class ValidationResult:
    is_valid: bool
    difference: Decimal
    message: Optional[str] = None


class ValidationService:
    """Apply core accounting validation rules on parsed statements."""

    def __init__(self, *, tolerance: Decimal = ACCOUNTING_TOLERANCE) -> None:
        self.tolerance = tolerance

    def validate_balance_sheet(self, balance_sheet: Dict[str, Decimal]) -> ValidationResult:
        total_assets = balance_sheet.get("total_assets", Decimal("0"))
        total_liabilities = balance_sheet.get("total_liabilities", Decimal("0"))
        total_equity = balance_sheet.get("total_equity", Decimal("0"))
        difference = total_assets - (total_liabilities + total_equity)
        if abs(difference) > self.tolerance:
            message = (
                "Balance sheet does not balance. "
                f"Assets={total_assets}, Liabilities+Equity={total_liabilities + total_equity}, "
                f"diff={difference}"
            )
            raise AccountingValidationError(message, difference=difference)
        return ValidationResult(is_valid=True, difference=difference)

    @staticmethod
    def validate_required_fields(data: Dict[str, Decimal], required_fields: Iterable[str]) -> ValidationResult:
        missing = [field for field in required_fields if field not in data]
        if missing:
            message = f"Missing required fields: {', '.join(missing)}"
            raise AccountingValidationError(message, difference=Decimal("0"))
        return ValidationResult(is_valid=True, difference=Decimal("0"))
