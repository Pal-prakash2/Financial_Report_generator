"""Date helpers for Indian financial years."""

from datetime import date


def financial_year_for(target_date: date) -> str:
    """Return FY label (e.g., FY2023-24) based on Indian Apr-Mar financial year."""

    start_year = target_date.year
    if target_date.month < 4:
        start_year -= 1
    end_year = start_year + 1
    return f"FY{start_year}-{str(end_year)[-2:]}"
