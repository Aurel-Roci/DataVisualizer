import logging
import os
from datetime import datetime
from typing import Annotated

# from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile

from ..context_manager import get_db
from ..models.bloodwork_metadata import BloodworkMetadata
from ..services.bloodwork import handle_bloodwork
from ..services.database import InfluxDBService
from ..services.pdf_parser import get_max_file_size

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint - API info"""
    return {"message": "Blood Work Parser API", "version": "1.0.0", "docs": "/docs"}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "influxdb_configured": bool(os.getenv("INFLUX_URL"))}


@router.post("/upload-bloodwork")
async def upload_bloodwork(
    request: Request,
    db: InfluxDBService = Depends(get_db),
    file: UploadFile = File(...),
    birthday: str | None = Form(None),
    name: str | None = Form(None),
):
    """Upload and parse a blood work PDF file"""
    max_size = get_max_file_size()
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > max_size:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size: {max_size} bytes")

    try:
        metadata = BloodworkMetadata(name=name, birthday=birthday)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    return await handle_bloodwork(db, file, metadata)


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

        response = results.to_dict("records")

        return {
            "start_date": start_date,
            "end_date": end_date,
            "test_names": test_names,
            "results": response,
        }
    except Exception as e:
        logger.exception(f"Error fetching results: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch results") from e
