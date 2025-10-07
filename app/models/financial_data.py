import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class FinancialData(Base):
    __tablename__ = "financial_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filing_id = Column(UUID(as_uuid=True), ForeignKey("filings.id"), nullable=False, unique=True)
    balance_sheet = Column(JSON, nullable=False)
    income_statement = Column(JSON, nullable=False)
    cash_flow = Column(JSON, nullable=False)
    notes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    filing = relationship("Filing", back_populates="financial_data")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<FinancialData {self.filing_id}>"
