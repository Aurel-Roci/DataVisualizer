"""Real report layouts. The PDFs hold patient data, so they are not in the repo:
point SAMPLE_PDF_DIR at a folder containing the files below (default ~/Downloads/analyza)."""

import os
from pathlib import Path

import pytest

from app.adapters.outbound.pdf_camelot import CamelotReportExtractor
from app.application.use_cases import UploadBloodwork

from .fakes import InMemoryRepository

SAMPLE_DIR = Path(os.getenv("SAMPLE_PDF_DIR", "~/Downloads/analyza")).expanduser()

# file -> (number of results, test date)
SAMPLES = {
    "2026-03-14/ROCI AUREL-197802.pdf": (45, "2026-03-14"),
    "2025-09-01/chol.pdf": (17, "2025-09-02"),
}


@pytest.mark.parametrize(("relative_path", "expected"), SAMPLES.items())
def test_sample_pdf(relative_path, expected):
    path = SAMPLE_DIR / relative_path
    if not path.exists():
        pytest.skip(f"sample PDF not available: {path}")

    repository = InMemoryRepository()
    record = UploadBloodwork(CamelotReportExtractor(), repository).execute(path.read_bytes(), "test")

    assert (len(record.results), record.test_date) == expected
    assert repository.records == [record]


def test_integer_results_keep_their_value():
    path = SAMPLE_DIR / "2026-03-14/ROCI AUREL-197802.pdf"
    if not path.exists():
        pytest.skip(f"sample PDF not available: {path}")

    record = UploadBloodwork(CamelotReportExtractor(), InMemoryRepository()).execute(path.read_bytes(), "test")
    values = {r.test_name: r.value for r in record.results}
    assert values["Platelets (PLT)"] == 308.0
    assert values["Densiteti Urinare (SG)"] == 1012.0
    assert values["Albumin Urine"] == 1.0
