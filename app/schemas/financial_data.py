from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class FinancialDataResponse(BaseModel):
    id: str
    balance_sheet: Dict[str, Any]
    income_statement: Dict[str, Any]
    cash_flow: Dict[str, Any]
    notes: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        orm_mode = True
