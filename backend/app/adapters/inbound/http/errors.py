"""Map domain errors to HTTP responses (the only place that knows both)"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ....domain.errors import (
    BloodworkError,
    ExtractionFailed,
    FileTooLarge,
    InvalidDateRange,
    InvalidReport,
    StorageUnavailable,
)

_STATUS_BY_ERROR: dict[type[BloodworkError], int] = {
    InvalidReport: 400,
    InvalidDateRange: 400,
    FileTooLarge: 413,
    StorageUnavailable: 503,
    ExtractionFailed: 500,
}


def _status_for(error: BloodworkError) -> int:
    for error_type, status in _STATUS_BY_ERROR.items():
        if isinstance(error, error_type):
            return status
    return 500


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(BloodworkError)
    async def handle_bloodwork_error(_: Request, exc: BloodworkError) -> JSONResponse:
        status = _status_for(exc)
        detail = f"Error processing file: {exc}" if isinstance(exc, ExtractionFailed) else str(exc)
        return JSONResponse(status_code=status, content={"detail": detail})
