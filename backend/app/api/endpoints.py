import logging
import os
from datetime import datetime

# from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

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
    birthday: str = Form(None),
    name: str | None = Form(None),
):
    """Upload and parse a blood work PDF file"""
    max_size = get_max_file_size()
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > max_size:
        raise HTTPException(
            status_code=413, detail=f"File too large. Maximum size: {max_size} bytes"
        )

    try:
        metadata = BloodworkMetadata(name=name, birthday=birthday)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    await handle_bloodwork(db, file, metadata)


@router.get("/results")
async def get_results(
    start_date: datetime,
    end_date: datetime,
    db: InfluxDBService = Depends(get_db),
    test_names: list[str] | None = None,
):
    """Get blood work results for date range"""

    try:
        results = db.get_patient_tests(
            start_date=start_date, end_date=end_date, test_names=test_names
        )

        response = results.to_dict("records")

        return {
            "start_date": start_date,
            "end_date": end_date,
            "test_names": test_names,
            "results": response,
        }
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
