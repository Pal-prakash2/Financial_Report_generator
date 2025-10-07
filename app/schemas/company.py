from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CompanyBase(BaseModel):
    name: str = Field(..., example="Reliance Industries Limited")
    cin: str = Field(..., min_length=10, max_length=21, example="L17110MH1973PLC019786")
    nse_symbol: Optional[str] = Field(None, example="RELIANCE")
    industry: Optional[str] = Field(None, example="Conglomerate")


class CompanyCreate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
