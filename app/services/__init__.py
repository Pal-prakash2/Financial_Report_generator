"""Service layer exports."""

__all__ = [
    "ExcelExporter",
    "ExcelGenerator",
    "MCAMonitorService",
    "ValidationService",
    "AccountingValidationError",
    "XBRLExtractionService",
    "XBRLParserService",
    "XBRLParseResult",
    "ValidationMessage",
]


def __getattr__(name: str):  # pragma: no cover - runtime convenience
    if name == "ExcelExporter":
        from app.services.excel_service import ExcelExporter

        return ExcelExporter
    if name == "ExcelGenerator":
        from app.services.excel_generator import ExcelGenerator

        return ExcelGenerator
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
    if name == "XBRLParserService":
        from app.services.xbrl_parser import XBRLParserService

        return XBRLParserService
    if name == "XBRLParseResult":
        from app.services.xbrl_parser import XBRLParseResult

        return XBRLParseResult
    if name == "ValidationMessage":
        from app.services.validation_service import ValidationMessage

        return ValidationMessage
    raise AttributeError(name)
