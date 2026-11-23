"""Ports: what the application needs from the outside world. Adapters implement these."""

from dataclasses import dataclass
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
