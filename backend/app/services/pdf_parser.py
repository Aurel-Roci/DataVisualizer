import io
import logging
import re
import tempfile
from datetime import datetime

import pdfplumber
from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from ..core.config import get_settings
from ..domain.models import BloodworkRecord, BloodworkResult

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
    """Parse blood work tables and extract test results"""

    date = extracted_data["date"]
    tables = extracted_data["tables"]

    blood_results = []

    # Process each table
    for table_idx, table in enumerate(tables):
        df = table.df  # Get the pandas DataFrame
        table_as_lists = df.values.tolist()  # Convert to list of lists
        # Row contents are medical data: only counts at INFO, contents at DEBUG
        logger.info(f"Parsing table {table_idx}: {len(table_as_lists)} rows")
        logger.debug(f"Parsing report: {table.parsing_report}")
        logger.debug(f"Table {table_idx} rows: {table_as_lists}")

        # Find the header row (usually contains 'REZULTATI' and 'VLERAT REFERUESE')
        header_row_idx = find_header_row(table_as_lists)

        if header_row_idx is None:
            logger.warning(f"No header found in table {table_idx + 1}")
            header_row_idx = 0

        # Process data rows (after header)
        for row_idx in range(header_row_idx + 1, len(table_as_lists)):
            row = table_as_lists[row_idx]
            if not row or len(row) < 2:
                continue

            test_result = parse_test_row(row, date)
            if test_result:
                blood_results.append(test_result)

    return BloodworkRecord(patient_name=name, test_date=date, results=blood_results)


def find_header_row(table: list[list]) -> int | None:
    """Find the row that contains the table headers"""
    for i, row in enumerate(table):
        if row and len(row) >= 2:
            # Look for header indicators
            row_text = " ".join([cell or "" for cell in row]).upper()
            if "REZULTATI" in row_text or "VLERAT REFERUESE" in row_text:
                return i
    return None


def parse_test_row(row: list[str], date: str) -> BloodworkResult | None:
    """Parse a single test result row"""
    logger.debug(f"Parsing row: {row}")
    try:
        clean_row = [cell.strip() if cell else "" for cell in row]

        if len(clean_row) < 2 or not any(clean_row):
            return None

        meaningful_cells = [cell for cell in clean_row if cell.strip()]
        if len(meaningful_cells) <= 1:
            logger.debug(f"Skipping row with only {len(meaningful_cells)} meaningful cell(s): {clean_row}")
            return None

        all_parts = []
        for cell in clean_row:
            if cell:
                # Split by newlines and add to all_parts
                cell_parts = cell.split("\n")
                for part in cell_parts:
                    part = part.strip()
                    if part:
                        all_parts.append(part)

        # Drop the row index (digit-only cells before the test name). Digit-only
        # cells after the name are integer results (e.g. Platelets 308), so keep them.
        filtered_parts = list(all_parts)
        while filtered_parts and filtered_parts[0].isdigit():
            filtered_parts.pop(0)

        if len(filtered_parts) < 2:
            logger.debug(f"Not enough data in first cell after filtering: {filtered_parts}")
            return None
        logger.debug(f"Parsing test result row: {filtered_parts}")
        # The structure is typically:
        # [test_name_with_number, value, reference_range, ...]
        # Find the test name (first non-empty cell)
        test_name = filtered_parts[0]
        test_name = test_name.replace("*", "").strip()
        value = None
        reference_range = ""

        for part in filtered_parts[1:]:
            # Try to extract a numeric value
            if value is None:
                # Look for a number at the start of the part
                number_match = re.match(r"^(\d+\.?\d*)", part)
                if number_match:
                    try:
                        value = float(number_match.group(1))
                        value_str = number_match.group(1)
                        # Everything after the number could be reference info
                        remaining = part[len(value_str) :].strip()
                        if remaining:
                            reference_range = remaining
                        continue
                    except ValueError:
                        pass

            # If we already found a value, collect remaining parts as reference range
            if value is not None:
                if reference_range:
                    reference_range += " " + part
                else:
                    reference_range = part

            # If no value found, return None
        if value is None:
            logger.debug(f"No numeric value found in parts: {filtered_parts}")
            return None

        # Extract unit from reference range if possible
        unit = extract_unit_from_range(reference_range)

        result = BloodworkResult(
            test_name=test_name,
            value=value,
            unit=unit,
            reference_range=reference_range,
            test_date=date,
        )

        logger.debug(f"Parsed: {test_name} = {value} {unit}")
        return result

    except Exception as e:
        logger.warning(f"Error parsing row {row}: {e}")
        return None


def extract_unit_from_range(reference_range: str) -> str:
    """Extract unit from reference range string"""
    if not reference_range:
        return ""

    # Common units in blood work
    units = [
        "%",
        "mg/dL",
        "mg/dl",
        "U/L",
        "g/dL",
        "g/dl",
        "mmol/L",
        "μg/dL",
        "ng/mL",
        "mL/min",
    ]

    for unit in units:
        if unit in reference_range:
            return unit

    # Count-style units as printed in reports, e.g. x10³/uL, x106/uL, 10^3/µL
    # (checked first: "10³/uL" would otherwise be seen as plain "uL")
    count_match = re.search(r"x?10[^\s/]{0,3}/[a-zA-Zμµ]{1,3}", reference_range)
    if count_match:
        return count_match.group(0)

    # Standalone units without a slash
    for unit in ("fL", "pg"):
        if re.search(rf"\b{unit}\b", reference_range):
            return unit

    # Other compound units such as mEq/L, g/24h. Plain words (e.g.
    # "Normal", "max") are not units, so anything without a "/" is ignored.
    unit_match = re.search(r"[a-zA-Zμµ]{1,6}/[a-zA-Zμµ]{1,6}\d*", reference_range)
    if unit_match:
        return unit_match.group(0)

    return ""


def _parse_date(date_str: str) -> datetime | None:
    """Parse a DD/MM/YYYY string, returning None if it is not a real date"""
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        return None


def extract_test_date(text: str, user_bday: str | None) -> str:
    """Extract the test date (DD/MM/YYYY in the PDF) and return it as YYYY-MM-DD.

    Prefers the date on the 'DATA ...' label (e.g. 'DATA E ANALIZËS: 02/09/2025'),
    then falls back to the first date that is not the patient's birthday, and
    finally to today's date.
    """
    candidates = []

    labelled = re.search(r"DATA[^\n:]*:\s*(\d{2}/\d{2}/\d{4})", text or "", re.IGNORECASE)
    if labelled:
        candidates.append(labelled.group(1))
    candidates.extend(re.findall(r"\b(\d{2}/\d{2}/\d{4})\b", text or ""))

    for date_str in candidates:
        if date_str == user_bday:
            continue
        if date_obj := _parse_date(date_str):
            return date_obj.strftime("%Y-%m-%d")

    logger.warning("Could not find test date, using current date")
    return datetime.now().strftime("%Y-%m-%d")
