import pdfplumber
import io
import re
import os
from fastapi import HTTPException, UploadFile
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from ..models.bloodwork_metadata import BloodworkResult, BloodworkRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def extract_pdf_data(file: UploadFile, user_bday: str) -> Dict:
    """Extract structured data from PDF using pdfplumber"""

    try:
        # File size (10MB limit)
        max_size = int(os.getenv("MAX_FILE_SIZE", "10485760"))

        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {max_size} bytes"
            )
        logger.info(f"Processing file: {file.filename}, size: {len(file_content)} bytes")

        import camelot
        tables = camelot.read_pdf(file.file, pages='all',
                                  line_scale=25,
                                  joint_tol=10,
                                  line_tol=8,
                                  threshold_blocksize=25,
                                  threshold_constant=-5,
                                  iterations=3,
                                  resolution=720)
        logger.info(f"CAMELOT table {tables}")

        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            # Get the first page for all text metadata
            page = pdf.pages[0]
        full_text = page.extract_text()
        result = {
            'full_text': full_text,
            'tables': tables,
            'date': extract_test_date(full_text, user_bday),
        }

        logger.info("Successfully extracted structured data using pdfplumber")
        return result

    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")
        raise Exception("Could not extract text from PDF")


def parse_blood_work_table(extracted_data: Dict, name: str) -> BloodworkRecord:
    """Parse blood work tables and extract test results"""

    date = extracted_data['date']
    tables = extracted_data['tables']

    blood_results = []

    # Process each table
    for table_idx, table in enumerate(tables):
        df = table.df  # Get the pandas DataFrame
        table_as_lists = df.values.tolist()  # Convert to list of lists
        logger.info(f"Parsing report: {table.parsing_report}")
        logger.info(f"Parsing table {table_idx}: {table_as_lists}")
        # logger.info(f"Processing table {table_idx + 1} with {len(table_as_lists)} rows")

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

    return BloodworkRecord(patient_name=name,test_date=date, results=blood_results)


def find_header_row(table: List[List]) -> Optional[int]:
    """Find the row that contains the table headers"""
    for i, row in enumerate(table):
        if row and len(row) >= 2:
            # Look for header indicators
            row_text = ' '.join([cell or '' for cell in row]).upper()
            if 'REZULTATI' in row_text or 'VLERAT REFERUESE' in row_text:
                return i
    return None


def parse_test_row(row: List[str], date: str) -> BloodworkResult | None:
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
                cell_parts = cell.split('\n')
                for part in cell_parts:
                    part = part.strip()
                    if part:
                        all_parts.append(part)

        # Remove leading number if present
        filtered_parts = []
        for part in all_parts:
            part = part.strip()
            if part:
                if part.isdigit():
                    continue
                filtered_parts.append(part)

        if len(filtered_parts) < 2:
            logger.debug(f"Not enough data in first cell after filtering: {filtered_parts}")
            return None
        logger.debug(f"Parsing test result row: {filtered_parts}")
        # The structure is typically:
        # [test_name_with_number, value, reference_range, ...]
        # Find the test name (first non-empty cell)
        test_name = filtered_parts[0]
        test_name = test_name.replace('*', '').strip()
        value = None
        reference_range = ""

        for i, part in enumerate(filtered_parts[1:], 1):
            # Try to extract a numeric value
            if not value:
                # Look for a number at the start of the part
                import re
                number_match = re.match(r'^(\d+\.?\d*)', part)
                if number_match:
                    try:
                        value = float(number_match.group(1))
                        value_str = number_match.group(1)
                        # Everything after the number could be reference info
                        remaining = part[len(value_str):].strip()
                        if remaining:
                            reference_range = remaining
                        continue
                    except ValueError:
                        pass

            # If we already found a value, collect remaining parts as reference range
            if value:
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

        logger.info(f"Parsed: {test_name} = {value} {unit}")
        return result

    except Exception as e:
        logger.warning(f"Error parsing row {row}: {e}")
        return None


def extract_unit_from_range(reference_range: str) -> str:
    """Extract unit from reference range string"""
    if not reference_range:
        return ""

    # Common units in blood work
    units = ['%', 'mg/dL', 'mg/dl', 'U/L', 'g/dL', 'g/dl', 'mmol/L', 'μg/dL', 'ng/mL', 'mL/min']

    for unit in units:
        if unit in reference_range:
            return unit

    # Look for other patterns
    unit_match = re.search(r'([a-zA-Z/μ]+)', reference_range)
    if unit_match:
        return unit_match.group(1)

    return ""


def extract_test_date(text: str, user_bday: str) -> str:
    """Extract date in DD/MM/YYYY format from text"""

    date_match = None
    date_pattern = r'\b(\d{2}/\d{2}/\d{4})\b'
    dates = re.findall(date_pattern, text)

    for date_str in dates:
        if date_str != user_bday:
            date_match = date_str

    if date_match is None:
        logger.warning("Could not find test date, using current date")
        return datetime.now().strftime("%d/%m/%Y")

    if isinstance(date_match, str):
        date_obj = datetime.strptime(date_match, '%d/%m/%Y')
    else:
        date_obj = date_match

    return date_obj.strftime('%Y-%m-%d')



def extract_name(text: str) -> str:
    """Extract date from 'DATA E ANALIZËS' field"""
    date_pattern = r'DATA .*\s*:\s*(\d{2}/\d{2}/\d{4})'
    match = re.search(date_pattern, text)

    if match:
        return match.group(1)  # Returns just the date part (02/09/2025)
    else:
        logger.warning("Could not find test date, using current date")
        return datetime.now().strftime("%d/%m/%Y")
