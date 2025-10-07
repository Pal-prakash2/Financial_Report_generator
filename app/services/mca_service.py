from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

from app.config import get_settings


@dataclass(slots=True)
class FilingMetadata:
    company_cin: str
    srn: str
    filing_date: datetime
    document_url: str


class MCAMonitorService:
    """Placeholder service to monitor MCA portal for new filings."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def fetch_recent_filings(self, cins: Iterable[str]) -> List[FilingMetadata]:
        """Return latest filing metadata for provided CINs.

        In MVP, this method is stubbed. Integrate MCA APIs or scraping later.
        """

        # TODO: Implement actual MCA monitoring via APIs or scheduled scraping.
        return []
