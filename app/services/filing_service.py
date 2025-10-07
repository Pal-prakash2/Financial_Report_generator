from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Filing


def get_latest_filing(company_id: str) -> Optional[Filing]:
    with SessionLocal() as session:
        stmt = (
            select(Filing)
            .where(Filing.company_id == company_id)
            .order_by(Filing.period_end.desc())
        )
        return session.scalars(stmt).first()
