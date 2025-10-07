from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.config import get_settings
from app.schemas import CompanyCreate, CompanyResponse, ParsedStatementResponse
from app.services.company_service import create_company, get_company_by_cin
from app.services.validation_service import AccountingValidationError
from app.services.xbrl_service import XBRLExtractionService

router = APIRouter()


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def register_company(payload: CompanyCreate) -> CompanyResponse:
    try:
        company = create_company(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CompanyResponse.from_orm(company)


@router.get("/{cin}", response_model=CompanyResponse)
def get_company(cin: str) -> CompanyResponse:
    company = get_company_by_cin(cin)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return CompanyResponse.from_orm(company)


@router.post(
    "/{cin}/filings/preview",
    response_model=ParsedStatementResponse,
    summary="Upload an MCA XBRL filing and preview standardized statements.",
)
def preview_filing(cin: str, file: UploadFile = File(...)) -> ParsedStatementResponse:
    company = get_company_by_cin(cin)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    if not file.filename.lower().endswith(".xml") and not file.filename.lower().endswith(".xbrl"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only XBRL/XML files are supported")

    settings = get_settings()
    parser_service = XBRLExtractionService()
    target_dir = Path(settings.data_dir) / "uploads" / company.cin
    target_dir.mkdir(parents=True, exist_ok=True)

    tmp_path: Path | None = None
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix, dir=target_dir) as tmp:
        contents = file.file.read()
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        assert tmp_path is not None
        bundle = parser_service.extract(tmp_path)
    except AccountingValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    finally:
        try:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)
        except OSError:
            pass

    return ParsedStatementResponse(
        balance_sheet={k: float(v) for k, v in bundle.balance_sheet.items()},
        income_statement={k: float(v) for k, v in bundle.income_statement.items()},
        cash_flow={k: float(v) for k, v in bundle.cash_flow.items()},
        metadata=bundle.metadata,
    )
