from datetime import datetime

import pytest

from app.adapters.outbound.influx_repository import InfluxBloodworkRepository
from app.config.settings import Settings
from app.domain.errors import StorageUnavailable
from app.domain.models import BloodworkRecord, BloodworkResult


class FailingClient:
    def __init__(self, error: Exception):
        self.error = error

    def write(self, points):
        raise self.error

    def query(self, *args, **kwargs):
        raise self.error


@pytest.fixture
def repo():
    repo = InfluxBloodworkRepository(host="http://x", token="t", database="d")
    return repo


def record():
    result = BloodworkResult(test_name="Glukoza", value=1.0, unit="", reference_range="1-2", test_date="2026-01-01")
    return BloodworkRecord(patient_name="Ada", test_date="2026-01-01", results=[result])


def test_missing_table_means_no_results(repo):
    repo.client = FailingClient(Exception("table 'bloodwork.public.bloodwork' not found"))
    assert repo.query(datetime(2026, 1, 1), datetime(2026, 1, 2)) == []


def test_other_query_errors_still_fail(repo):
    repo.client = FailingClient(Exception("connection refused"))
    with pytest.raises(StorageUnavailable, match="Failed to fetch results"):
        repo.query(datetime(2026, 1, 1), datetime(2026, 1, 2))


def test_schema_conflict_has_clear_message(repo):
    repo.client = FailingClient(Exception("expected tag, got field reference_range"))
    with pytest.raises(StorageUnavailable, match="different schema"):
        repo.store(record())


def test_other_write_errors_keep_generic_message(repo):
    repo.client = FailingClient(Exception("connection refused"))
    with pytest.raises(StorageUnavailable, match="Failed to store results in database"):
        repo.store(record())


def test_cors_origins_parsed(fresh_settings):
    fresh_settings.setenv("CORS_ORIGINS", "http://a.com, http://b.com,")
    assert Settings.from_env().cors_origins == ("http://a.com", "http://b.com")
