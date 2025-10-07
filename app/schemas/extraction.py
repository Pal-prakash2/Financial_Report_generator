from datetime import date
from typing import Any, Dict

from pydantic import BaseModel


class ParsedStatementResponse(BaseModel):
    balance_sheet: Dict[str, float]
    income_statement: Dict[str, float]
    cash_flow: Dict[str, float]
    metadata: Dict[str, Any]

    class Config:
        schema_extra = {
            "example": {
                "balance_sheet": {"total_assets": 1.5e12, "total_equity": 6.5e11},
                "income_statement": {"revenue": 8.7e11, "profit_after_tax": 1.2e11},
                "cash_flow": {"net_cash_from_operations": 9.8e10},
                "metadata": {
                    "period_start": "2023-04-01",
                    "period_end": "2024-03-31",
                    "financial_year": "FY2023-24",
                },
            }
        }
