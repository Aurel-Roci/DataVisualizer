"""FastAPI dependencies: assemble use cases from the adapters built at startup (see main.py)"""

from fastapi import Request

from ....application.ports import BloodworkRepository, ReportExtractor
from ....application.use_cases import GetResults, UploadBloodwork


def get_repository(request: Request) -> BloodworkRepository:
    return request.app.state.repository


def get_extractor(request: Request) -> ReportExtractor:
    return request.app.state.extractor


def get_upload_use_case(request: Request) -> UploadBloodwork:
    return UploadBloodwork(extractor=get_extractor(request), repository=get_repository(request))


def get_results_use_case(request: Request) -> GetResults:
    return GetResults(repository=get_repository(request))
