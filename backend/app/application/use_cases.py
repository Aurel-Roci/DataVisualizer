"""Use cases: application logic written against ports only (no FastAPI, camelot or Influx)"""

import logging

from ..domain.errors import InvalidReport
from ..domain.models import BloodworkRecord
from ..domain.parsing import extract_test_date, parse_tables
from .ports import BloodworkRepository, ReportExtractor

logger = logging.getLogger(__name__)


class UploadBloodwork:
    """Extract a report, parse its results and store them"""

    def __init__(self, extractor: ReportExtractor, repository: BloodworkRepository):
        self._extractor = extractor
        self._repository = repository

    def execute(self, content: bytes, patient_name: str, birthday: str | None = None) -> BloodworkRecord:
        """Blocking (PDF extraction and the DB write): call from a worker thread in async code"""
        report = self._extractor.extract(content)
        if not report.tables:
            raise InvalidReport("No table data found in PDF")

        test_date = extract_test_date(report.full_text, birthday)
        record = parse_tables(report.tables, patient_name, test_date)

        self._repository.store(record)
        return record
