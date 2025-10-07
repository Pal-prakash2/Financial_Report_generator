from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.parsers import IndASXBRLParser, ParsedStatementBundle
from app.services.validation_service import AccountingValidationError, ValidationService


class XBRLExtractionService:
    """High level service to parse and validate XBRL filings."""

    def __init__(
        self,
        parser: Optional[IndASXBRLParser] = None,
        validator: Optional[ValidationService] = None,
    ) -> None:
        self.parser = parser or IndASXBRLParser()
        self.validator = validator or ValidationService()

    def extract(self, file_path: str | Path) -> ParsedStatementBundle:
        bundle = self.parser.parse_document(file_path)
        try:
            self.validator.validate_balance_sheet(bundle.balance_sheet)
        except AccountingValidationError as exc:
            raise AccountingValidationError(
                f"Validation failed for {file_path}: {exc}", difference=exc.difference
            ) from exc
        return bundle
