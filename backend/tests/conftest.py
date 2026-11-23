import pytest

from app.application.ports import ExtractedReport
from app.config.settings import get_settings
from app.main import app

from .fakes import FakeExtractor, InMemoryRepository

# One results table in the layout the parser expects: header row, then index/name/value/range rows
SAMPLE_TABLE = [
    ["REZULTATI", "VLERAT REFERUESE"],
    ["1", "Glukoza*", "91.7", "74 - 106 mg/dL"],
    ["2", "Platelets (PLT)*", "308", "140 -400 x10³/uL"],
]
SAMPLE_TEXT = "EMRI: TEST\nDATA E ANALIZËS : 14/03/2026 07:27:49\nMOSHA : 29/08/1993"


@pytest.fixture(autouse=True)
def fresh_settings(monkeypatch):
    """Settings are cached; clear around every test so env overrides apply"""
    get_settings.cache_clear()
    yield monkeypatch
    get_settings.cache_clear()


@pytest.fixture
def repository():
    return InMemoryRepository()


@pytest.fixture
def extractor():
    return FakeExtractor(ExtractedReport(tables=[SAMPLE_TABLE], full_text=SAMPLE_TEXT))


@pytest.fixture
def client_app(repository, extractor):
    """The real FastAPI app with fakes in place of the Influx and Camelot adapters"""
    app.state.repository = repository
    app.state.extractor = extractor
    return app
