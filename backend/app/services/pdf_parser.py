import io
import logging
import tempfile

import pdfplumber
from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from ..core.config import get_settings
from ..domain.models import BloodworkRecord
from ..domain.parsing import extract_test_date, parse_tables

logger = logging.getLogger(__name__)

UPLOAD_CHUNK_SIZE = 64 * 1024


async def read_upload_limited(file: UploadFile, max_size: int) -> bytes:
    """Read an upload in chunks, aborting as soon as it exceeds max_size"""
    chunks = []
    total = 0
    while chunk := await file.read(UPLOAD_CHUNK_SIZE):
        total += len(chunk)
        if total > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {max_size} bytes",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _extract_pdf_sync(file_content: bytes, user_bday: str | None) -> dict:
    """Blocking PDF extraction (camelot + pdfplumber); run in a worker thread"""
    import camelot

    # Camelot needs a real file path; the upload stream is already consumed
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(file_content)
        tmp.flush()
        tables = camelot.read_pdf(
            tmp.name,
            pages="all",
            line_scale=25,
            joint_tol=10,
            line_tol=8,
            threshold_blocksize=25,
            threshold_constant=-5,
            iterations=3,
            resolution=720,
        )
    logger.info(f"Camelot found {len(tables)} table(s)")

    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        # Text from every page, so a date missing from page 1 can still be found
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    return {
        "full_text": full_text,
        "tables": tables,
        "date": extract_test_date(full_text, user_bday),
    }


async def extract_pdf_data(file: UploadFile, user_bday: str | None) -> dict:
    """Extract structured data from a PDF using camelot and pdfplumber"""

    try:
        file_content = await read_upload_limited(file, get_settings().max_file_size)
        # Extension and content-type are client-controlled; check the file itself
        if not file_content.lstrip().startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="File is not a valid PDF")
        logger.info(f"Processing upload, size: {len(file_content)} bytes")

        result = await run_in_threadpool(_extract_pdf_sync, file_content, user_bday)

        logger.info("Successfully extracted structured data from PDF")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")
        raise Exception("Could not extract text from PDF") from e


def parse_blood_work_table(extracted_data: dict, name: str) -> BloodworkRecord:
    """Convert camelot tables to plain rows and parse them with the domain rules"""
    tables_as_lists = []
    for table_idx, table in enumerate(extracted_data["tables"]):
        rows = table.df.values.tolist()
        # Row contents are medical data: only counts at INFO, contents at DEBUG
        logger.info(f"Parsing table {table_idx}: {len(rows)} rows")
        logger.debug(f"Parsing report: {table.parsing_report}")
        logger.debug(f"Table {table_idx} rows: {rows}")
        tables_as_lists.append(rows)

    return parse_tables(tables_as_lists, name, extracted_data["date"])
