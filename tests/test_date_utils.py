from datetime import date

from app.utils.date import financial_year_for


def test_financial_year_for_before_april():
    assert financial_year_for(date(2024, 3, 31)) == "FY2023-24"


def test_financial_year_for_after_april():
    assert financial_year_for(date(2024, 4, 1)) == "FY2024-25"
