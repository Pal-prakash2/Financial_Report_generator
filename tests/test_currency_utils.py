from decimal import Decimal

import pytest

from app.utils.currency import format_in_crores, format_in_lakhs, parse_indian_currency


def test_parse_indian_currency_lakhs():
    result = parse_indian_currency("1,234.5", "Lakhs")
    assert result == Decimal("123450000")


def test_format_in_crores():
    output = format_in_crores(Decimal("250000000"))
    assert output == "25.00 Cr"


def test_unknown_unit_raises():
    with pytest.raises(ValueError):
        parse_indian_currency(10, "Million")
