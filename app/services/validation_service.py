from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, List, Optional

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


@dataclass(slots=True)
class ValidationMessage:
    statement: str
    field: str
    period: str
    passed: bool
    difference: Decimal
    message: str


class ValidationService:
    """Apply core accounting validation rules on parsed statements."""

    def __init__(
        self,
        *,
        absolute_tolerance: Decimal = ACCOUNTING_TOLERANCE,
        relative_tolerance: Decimal = Decimal("0.01"),
    ) -> None:
        self.absolute_tolerance = absolute_tolerance
        self.relative_tolerance = relative_tolerance

    def validate_balance_sheet(self, balance_sheet: Dict[str, Decimal]) -> ValidationResult:
        total_assets = balance_sheet.get("total_assets", Decimal("0"))
        total_liabilities = balance_sheet.get("total_liabilities", Decimal("0"))
        total_equity = balance_sheet.get("total_equity", balance_sheet.get("shareholders_equity", Decimal("0")))
        difference = total_assets - (total_liabilities + total_equity)
        if not self._within_tolerance(difference, total_assets):
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

    def validate_statements(self, statements: Dict[str, Dict[str, Dict[str, Decimal]]]) -> List[ValidationMessage]:
        messages: List[ValidationMessage] = []
        balance_sheet = statements.get("balance_sheet", {})
        for period, values in self._group_by_period(balance_sheet).items():
            difference = self._balance_sheet_difference(values)
            passed = self._within_tolerance(difference, values.get("total_assets", Decimal("0")))
            message = (
                "Assets equal liabilities plus equity"
                if passed
                else "Assets do not equal liabilities plus equity"
            )
            messages.append(
                ValidationMessage(
                    statement="balance_sheet",
                    field="total_assets",
                    period=period,
                    passed=passed,
                    difference=difference,
                    message=message,
                )
            )

        income_statement = statements.get("income_statement", {})
        for period, values in self._group_by_period(income_statement).items():
            messages.extend(self._validate_income_statement_period(values, period))
        return messages

    def _validate_income_statement_period(self, values: Dict[str, Decimal], period: str) -> List[ValidationMessage]:
        messages: List[ValidationMessage] = []

        operating_revenue = values.get("operating_revenue")
        other_income = values.get("other_income")
        total_revenue = values.get("total_revenue") or values.get("total_income")
        if operating_revenue is not None and other_income is not None and total_revenue is not None:
            expected = operating_revenue + other_income
            difference = total_revenue - expected
            passed = self._within_tolerance(difference, total_revenue)
            message = (
                "Total revenue reconciles with operating revenue + other income"
                if passed
                else "Total revenue mismatch against operating revenue + other income"
            )
            messages.append(
                ValidationMessage(
                    statement="income_statement",
                    field="total_revenue",
                    period=period,
                    passed=passed,
                    difference=difference,
                    message=message,
                )
            )

        profit_before_tax = values.get("profit_before_tax")
        tax_expense = values.get("tax_expense")
        profit_after_tax = values.get("profit_after_tax")
        if (
            profit_before_tax is not None
            and tax_expense is not None
            and profit_after_tax is not None
        ):
            expected = profit_before_tax - tax_expense
            difference = profit_after_tax - expected
            passed = self._within_tolerance(difference, profit_after_tax)
            message = (
                "Profit after tax reconciles with profit before tax minus tax expense"
                if passed
                else "Profit after tax mismatch against profit before tax minus tax expense"
            )
            messages.append(
                ValidationMessage(
                    statement="income_statement",
                    field="profit_after_tax",
                    period=period,
                    passed=passed,
                    difference=difference,
                    message=message,
                )
            )

        return messages

    @staticmethod
    def _group_by_period(statement: Dict[str, Dict[str, Decimal]]) -> Dict[str, Dict[str, Decimal]]:
        grouped: Dict[str, Dict[str, Decimal]] = {}
        for field, period_values in statement.items():
            for period, value in period_values.items():
                grouped.setdefault(period, {})[field] = value
        return grouped

    def _balance_sheet_difference(self, values: Dict[str, Decimal]) -> Decimal:
        total_assets = values.get("total_assets", Decimal("0"))
        total_liabilities = values.get("total_liabilities", Decimal("0"))
        total_equity = values.get("total_equity", values.get("shareholders_equity", Decimal("0")))
        return total_assets - (total_liabilities + total_equity)

    def _within_tolerance(self, difference: Decimal, base_amount: Decimal) -> bool:
        abs_tolerance = self.absolute_tolerance
        rel_tolerance = (abs(base_amount) * self.relative_tolerance) if base_amount != 0 else Decimal("0")
        tolerance_threshold = max(abs_tolerance, rel_tolerance)
        return abs(difference) <= tolerance_threshold
