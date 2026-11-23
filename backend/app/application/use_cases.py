"""Use cases: application logic written against ports only (no FastAPI, camelot or Influx)"""

import logging
from datetime import datetime

from ..domain.errors import InvalidDateRange, InvalidReport
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


class GetResults:
    """Read stored results for a date range"""

    def __init__(self, repository: BloodworkRepository):
        self._repository = repository

    def execute(self, start_date: datetime, end_date: datetime, test_names: list[str] | None = None) -> list[dict]:
        """Blocking (DB query): call from a worker thread in async code"""
        if start_date > end_date:
            raise InvalidDateRange("start_date must not be after end_date")
        return self._repository.query(start_date, end_date, test_names)
