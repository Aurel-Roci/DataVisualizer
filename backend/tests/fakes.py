"""In-memory fakes of the application ports"""

from datetime import datetime

from app.application.ports import ExtractedReport
from app.domain.errors import StorageUnavailable
from app.domain.models import BloodworkRecord


class FakeExtractor:
    def __init__(self, report: ExtractedReport | None = None, error: Exception | None = None):
        self.report = report or ExtractedReport(tables=[], full_text="")
        self.error = error

    def extract(self, content: bytes) -> ExtractedReport:
        if self.error:
            raise self.error
        return self.report


class InMemoryRepository:
    def __init__(self, rows: list[dict] | None = None, fail: bool = False):
        self.records: list[BloodworkRecord] = []
        self.rows = rows or []
        self.fail = fail
        self.queries: list[tuple] = []

    def store(self, record: BloodworkRecord) -> None:
        if self.fail:
            raise StorageUnavailable("Failed to store results in database")
        self.records.append(record)

    def query(self, start_date: datetime, end_date: datetime, test_names: list[str] | None = None) -> list[dict]:
        if self.fail:
            raise StorageUnavailable("Failed to fetch results")
        self.queries.append((start_date, end_date, test_names))
        return self.rows
