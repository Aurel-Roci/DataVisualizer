import pytest

from app.domain.errors import ExtractionFailed, InvalidReport

from . import asgi_client
from .fakes import FakeExtractor, InMemoryRepository

PDF = b"%PDF-1.4 fake"


def test_upload_ok(client_app, repository):
    status, body = asgi_client.upload(client_app, "report.pdf", PDF, {"name": " Ada "})

    assert status == 200
    assert body["name"] == "Ada"
    assert body["test_date"] == "2026-03-14"
    assert [r["test_name"] for r in body["results"]] == ["Glukoza", "Platelets (PLT)"]
    assert repository.records[0].patient_name == "Ada"


def test_upload_name_defaults_when_missing(client_app):
    _, body = asgi_client.upload(client_app, "REPORT.PDF", PDF)
    assert body["name"] == "unknown"


@pytest.mark.parametrize("filename", ["notes.txt", "noextension"])
def test_upload_rejects_wrong_extension(client_app, filename):
    status, body = asgi_client.upload(client_app, filename, PDF)
    assert (status, body["detail"]) == (400, "Only PDF files are supported")


def test_upload_rejects_invalid_birthday(client_app):
    status, _ = asgi_client.upload(client_app, "r.pdf", PDF, {"birthday": "1993-08-29"})
    assert status == 400


def test_upload_too_large(client_app, fresh_settings):
    fresh_settings.setenv("MAX_FILE_SIZE", "10")
    status, body = asgi_client.upload(client_app, "r.pdf", PDF)
    assert (status, body["detail"]) == (413, "File too large. Maximum size: 10 bytes")


def test_allowed_extensions_are_configurable(client_app, fresh_settings):
    fresh_settings.setenv("ALLOWED_EXTENSIONS", "pdf,report")
    status, _ = asgi_client.upload(client_app, "x.report", PDF)
    assert status == 200


@pytest.mark.parametrize(
    ("error", "status", "detail"),
    [
        (InvalidReport("File is not a valid PDF"), 400, "File is not a valid PDF"),
        (
            ExtractionFailed("Could not extract text from PDF"),
            500,
            "Error processing file: Could not extract text from PDF",
        ),
    ],
)
def test_extractor_errors_are_mapped(client_app, error, status, detail):
    client_app.state.extractor = FakeExtractor(error=error)
    assert asgi_client.upload(client_app, "r.pdf", PDF) == (status, {"detail": detail})


def test_upload_storage_failure_is_503(client_app):
    client_app.state.repository = InMemoryRepository(fail=True)
    status, body = asgi_client.upload(client_app, "r.pdf", PDF)
    assert (status, body["detail"]) == (503, "Failed to store results in database")


def test_results_ok(client_app):
    client_app.state.repository = InMemoryRepository(rows=[{"test_name": "a", "reference_range": None}])
    status, body = asgi_client.get(client_app, "/results", "start_date=2026-01-01&end_date=2026-01-31&test_names=a")
    assert status == 200
    assert body["results"] == [{"test_name": "a", "reference_range": None}]
    assert body["test_names"] == ["a"]


def test_results_inverted_range_is_400(client_app):
    status, body = asgi_client.get(client_app, "/results", "start_date=2026-02-01&end_date=2026-01-01")
    assert (status, body["detail"]) == (400, "start_date must not be after end_date")


def test_results_storage_failure_is_503(client_app):
    client_app.state.repository = InMemoryRepository(fail=True)
    status, _ = asgi_client.get(client_app, "/results", "start_date=2026-01-01&end_date=2026-01-31")
    assert status == 503
