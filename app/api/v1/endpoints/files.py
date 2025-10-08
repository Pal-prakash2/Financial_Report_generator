from __future__ import annotations

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Final

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.services.excel_generator import ExcelGenerator
from app.services.validation_service import ValidationService
from app.services.xbrl_parser import XBRLParserService

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS: Final[set[str]] = {".xml", ".xbrl"}
MAX_FILE_SIZE_BYTES: Final[int] = 15 * 1024 * 1024  # 15 MB ceiling


@router.post("/xbrl-to-excel", summary="Convert an uploaded XBRL file into an Excel workbook")
async def convert_xbrl_to_excel(file: UploadFile = File(...)) -> StreamingResponse:
    filename = file.filename or "uploaded.xbrl"
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .xml or .xbrl files are supported")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds maximum size of 15 MB")

    parser = XBRLParserService()
    validator = ValidationService()
    excel_generator = ExcelGenerator()

    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp:
        tmp.write(contents)
        temp_path = Path(tmp.name)

    try:
        parse_result = parser.parse(temp_path)
        validation_messages = validator.validate_statements(parse_result.statements)
        workbook_stream = excel_generator.generate(parse_result, validation_messages)
    except ValueError as exc:
        logger.exception("Failed to parse XBRL document")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - unexpected runtime errors
        logger.exception("Unexpected error when processing XBRL upload")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to process XBRL file") from exc
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            logger.debug("Temporary file cleanup failed for %s", temp_path)
        await file.close()

    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    output_filename = f"xbrl-export-{timestamp}.xlsx"
    headers = {"Content-Disposition": f"attachment; filename={output_filename}"}
    return StreamingResponse(
        workbook_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
