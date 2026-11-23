import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.concurrency import run_in_threadpool

from ..application.use_cases import UploadBloodwork
from ..context_manager import get_db
from ..core.config import get_settings
from ..domain.errors import FileTooLarge
from ..models.bloodwork_metadata import BloodworkMetadata
from ..services.database import InfluxDBService
from ..services.pdf_parser import CamelotReportExtractor

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_CHUNK_SIZE = 64 * 1024


def get_upload_use_case(db: InfluxDBService = Depends(get_db)) -> UploadBloodwork:
    return UploadBloodwork(extractor=CamelotReportExtractor(), repository=db)


async def read_upload_limited(file: UploadFile, max_size: int) -> bytes:
    """Read an upload in chunks, aborting as soon as it exceeds max_size"""
    chunks = []
    total = 0
    while chunk := await file.read(UPLOAD_CHUNK_SIZE):
        total += len(chunk)
        if total > max_size:
            raise FileTooLarge(max_size)
        chunks.append(chunk)
    return b"".join(chunks)


@router.get("/")
async def root():
    """Root endpoint - API info"""
    return {"message": "Blood Work Parser API", "version": "1.0.0", "docs": "/docs"}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "influxdb_configured": bool(get_settings().influxdb_host)}


@router.post("/upload-bloodwork")
async def upload_bloodwork(
    request: Request,
    use_case: UploadBloodwork = Depends(get_upload_use_case),
    file: UploadFile = File(...),
    birthday: str | None = Form(None),
    name: str | None = Form(None),
):
    """Upload and parse a blood work PDF file"""
    settings = get_settings()
    max_size = settings.max_file_size
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > max_size:
        raise FileTooLarge(max_size)

    try:
        metadata = BloodworkMetadata(name=name, birthday=birthday)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    extension = (file.filename or "").rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else ""
    if extension not in settings.allowed_extensions:
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await read_upload_limited(file, max_size)
    record = await run_in_threadpool(use_case.execute, content, metadata.name, metadata.birthday)

    return {
        "filename": file.filename,
        "test_date": record.test_date,
        "name": metadata.name,
        "results": record.results,
        "message": "Blood work parsed successfully",
    }


@router.get("/results")
async def get_results(
    start_date: datetime,
    end_date: datetime,
    db: InfluxDBService = Depends(get_db),
    test_names: Annotated[list[str] | None, Query()] = None,
):
    """Get blood work results for date range (end_date is inclusive of the whole day)"""
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must not be after end_date")

    try:
        results = db.get_patient_tests(start_date=start_date, end_date=end_date, test_names=test_names)

        # pandas 3 fills missing strings with NaN (not None), which is not JSON serializable
        response = results.astype(object).where(results.notna(), None).to_dict("records")

        return {
            "start_date": start_date,
            "end_date": end_date,
            "test_names": test_names,
            "results": response,
        }
    except Exception as e:
        logger.exception(f"Error fetching results: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch results") from e
