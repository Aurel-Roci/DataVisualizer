import io
import logging
import tempfile

import pdfplumber

from ..application.ports import ExtractedReport
from ..domain.errors import ExtractionFailed, InvalidReport

logger = logging.getLogger(__name__)


class CamelotReportExtractor:
    """ReportExtractor port implementation using camelot (tables) and pdfplumber (text)"""

    def extract(self, content: bytes) -> ExtractedReport:
        # Extension and content-type are client-controlled; check the file itself
        if not content.lstrip().startswith(b"%PDF-"):
            raise InvalidReport("File is not a valid PDF")
        logger.info(f"Processing upload, size: {len(content)} bytes")

        try:
            report = self._extract(content)
        except Exception as e:
            logger.warning(f"PDF extraction failed: {e}")
            raise ExtractionFailed("Could not extract text from PDF") from e

        logger.info("Successfully extracted structured data from PDF")
        return report

    @staticmethod
    def _extract(content: bytes) -> ExtractedReport:
        import camelot

        # Camelot needs a real file path
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
            tmp.write(content)
            tmp.flush()
            camelot_tables = camelot.read_pdf(
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
        logger.info(f"Camelot found {len(camelot_tables)} table(s)")

        tables = []
        for table_idx, table in enumerate(camelot_tables):
            rows = table.df.values.tolist()
            # Row contents are medical data: only counts at INFO, contents at DEBUG
            logger.info(f"Parsing table {table_idx}: {len(rows)} rows")
            logger.debug(f"Parsing report: {table.parsing_report}")
            logger.debug(f"Table {table_idx} rows: {rows}")
            tables.append(rows)

        with pdfplumber.open(io.BytesIO(content)) as pdf:
            # Text from every page, so a date missing from page 1 can still be found
            full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        return ExtractedReport(tables=tables, full_text=full_text)
