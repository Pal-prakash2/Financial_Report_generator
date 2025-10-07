from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.session import SessionLocal
from app.models import Company
from app.schemas.company import CompanyCreate


def create_company(payload: CompanyCreate) -> Company:
    with SessionLocal() as session:
        company = Company(**payload.dict())
        session.add(company)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            raise ValueError("Company with same CIN already exists") from exc
        session.refresh(company)
        return company


def get_company_by_cin(cin: str) -> Optional[Company]:
    with SessionLocal() as session:
        stmt = select(Company).where(Company.cin == cin)
        return session.scalar(stmt)
