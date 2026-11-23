"""Ports: what the application needs from the outside world. Adapters implement these."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from ..domain.models import BloodworkRecord


@dataclass(frozen=True)
class ExtractedReport:
    """Raw content pulled out of a report file"""

    tables: list[list[list[str]]]  # per table: rows of cell text
    full_text: str


class ReportExtractor(Protocol):
    def extract(self, content: bytes) -> ExtractedReport:
        """Read tables and text from a report file.

        Raises InvalidReport if the content is not a report file, ExtractionFailed if it cannot be read.
        """
        ...


class BloodworkRepository(Protocol):
    def store(self, record: BloodworkRecord) -> None:
        """Persist a record. Raises StorageUnavailable on failure."""
        ...

    def query(self, start_date: datetime, end_date: datetime, test_names: list[str] | None = None) -> list[dict]:
        """Stored rows for a date range (end_date inclusive of the whole day), newest first.

        Raises StorageUnavailable on failure.
        """
        ...
