from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.financial_data import FinancialDataResponse


class FilingBase(BaseModel):
    srn: str = Field(..., example="H12345678")
    period_start: date
    period_end: date
    filing_date: date
    document_url: Optional[str] = Field(None, example="https://www.mca.gov.in/documents/xbrl")


class FilingCreate(FilingBase):
    company_id: str


class FilingResponse(FilingBase):
    id: str
    created_at: datetime
    financial_data: Optional[FinancialDataResponse]

    class Config:
        orm_mode = True
