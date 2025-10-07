"""Helpers for Indian currency formats (Lakhs, Crores) and conversions."""

from decimal import Decimal, InvalidOperation
from typing import Optional, Union

Number = Union[int, float, Decimal, str]

UNIT_MULTIPLIERS = {
    "INR": Decimal(1),
    "RUPEES": Decimal(1),
    "LAKHS": Decimal(1_00_000),
    "CRORES": Decimal(1_00_00_000),
}


def _to_decimal(value: Number) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        sanitized = value.replace(",", "").strip()
        try:
            return Decimal(sanitized)
        except InvalidOperation as exc:  # pragma: no cover - defensive
            raise ValueError(f"Unable to parse numeric value from '{value}'") from exc
    raise TypeError(f"Unsupported numeric type: {type(value)!r}")


def parse_indian_currency(value: Number, unit: str | None = None) -> Decimal:
    """Parse a numeric value expressed in Lakhs/Crores into absolute rupees."""

    magnitude = _to_decimal(value)
    if unit is None:
        return magnitude
    multiplier = UNIT_MULTIPLIERS.get(unit.upper())
    if multiplier is None:
        raise ValueError(f"Unknown unit '{unit}'. Supported units: {', '.join(UNIT_MULTIPLIERS)}")
    return magnitude * multiplier


def format_in_crores(value: Number) -> str:
    amount = _to_decimal(value) / UNIT_MULTIPLIERS["CRORES"]
    return f"{amount:.2f} Cr"


def format_in_lakhs(value: Number) -> str:
    amount = _to_decimal(value) / UNIT_MULTIPLIERS["LAKHS"]
    return f"{amount:.2f} L"


def normalize_to_abs(value: Optional[Number], unit: Optional[str]) -> Optional[Decimal]:
    if value is None:
        return None
    return parse_indian_currency(value, unit)
