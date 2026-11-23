from datetime import datetime

import pytest

from app.application.ports import ExtractedReport
from app.application.use_cases import GetResults, UploadBloodwork
from app.domain.errors import ExtractionFailed, InvalidDateRange, InvalidReport, StorageUnavailable

from .fakes import FakeExtractor, InMemoryRepository


def test_upload_parses_and_stores(extractor, repository):
    record = UploadBloodwork(extractor, repository).execute(b"pdf", "Ada")

    assert repository.records == [record]
    assert record.patient_name == "Ada"
    assert record.test_date == "2026-03-14"
    assert [(r.test_name, r.value) for r in record.results] == [("Glukoza", 91.7), ("Platelets (PLT)", 308.0)]


def test_upload_skips_birthday_date_without_label(repository):
    report = ExtractedReport(
        tables=[[["REZULTATI", "x"], ["Glukoza", "5", "mg/dL"]]], full_text="29/08/1993 02/09/2025"
    )
    record = UploadBloodwork(FakeExtractor(report), repository).execute(b"pdf", "Ada", "29/08/1993")
    assert record.test_date == "2025-09-02"


def test_upload_without_tables_is_invalid_and_not_stored(repository):
    with pytest.raises(InvalidReport):
        UploadBloodwork(FakeExtractor(), repository).execute(b"pdf", "Ada")
    assert repository.records == []


def test_upload_propagates_extraction_failure(repository):
    with pytest.raises(ExtractionFailed):
        UploadBloodwork(FakeExtractor(error=ExtractionFailed("bad")), repository).execute(b"pdf", "Ada")


def test_upload_propagates_storage_failure(extractor):
    with pytest.raises(StorageUnavailable):
        UploadBloodwork(extractor, InMemoryRepository(fail=True)).execute(b"pdf", "Ada")


def test_get_results_returns_repository_rows():
    repo = InMemoryRepository(rows=[{"test_name": "a"}])
    start, end = datetime(2026, 1, 1), datetime(2026, 1, 31)
    assert GetResults(repo).execute(start, end, ["a"]) == [{"test_name": "a"}]
    assert repo.queries == [(start, end, ["a"])]


def test_get_results_rejects_inverted_range():
    with pytest.raises(InvalidDateRange):
        GetResults(InMemoryRepository()).execute(datetime(2026, 2, 1), datetime(2026, 1, 1))
