"""Service layer exports."""

__all__ = [
    "ExcelExporter",
    "MCAMonitorService",
    "ValidationService",
    "AccountingValidationError",
    "XBRLExtractionService",
]


def __getattr__(name: str):  # pragma: no cover - runtime convenience
    if name == "ExcelExporter":
        from app.services.excel_service import ExcelExporter

        return ExcelExporter
    if name == "MCAMonitorService":
        from app.services.mca_service import MCAMonitorService

        return MCAMonitorService
    if name == "ValidationService":
        from app.services.validation_service import ValidationService

        return ValidationService
    if name == "AccountingValidationError":
        from app.services.validation_service import AccountingValidationError

        return AccountingValidationError
    if name == "XBRLExtractionService":
        from app.services.xbrl_service import XBRLExtractionService

        return XBRLExtractionService
    raise AttributeError(name)
