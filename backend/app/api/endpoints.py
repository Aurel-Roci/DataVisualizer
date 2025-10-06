import os
import logging
from fastapi import UploadFile, File, HTTPException, APIRouter, Form, Depends
# from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import datetime

from ..context_manager import get_db
from ..models.bloodwork_metadata import BloodworkMetadata
from ..services.bloodwork import handle_bloodwork
from ..services.database import InfluxDBService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "message": "Blood Work Parser API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "influxdb_configured": bool(os.getenv("INFLUX_URL"))
    }


@router.post("/upload-bloodwork")
async def upload_bloodwork(db: InfluxDBService = Depends(get_db),
                           file: UploadFile = File(...),
                           birthday: str = Form(None),
                           name: Optional[str] = Form(None)):
    """Upload and parse a blood work PDF file"""
    try:
        metadata = BloodworkMetadata(name=name, birthday=birthday)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    await handle_bloodwork(db, file, metadata)


@router.get("/results")
async def get_results(
        start_date: datetime,
        end_date: datetime,
        db: InfluxDBService = Depends(get_db),
        test_names: Optional[List[str]] = None
):
    """Get blood work results for date range"""

    try:
        results = db.get_patient_tests(start_date=start_date, end_date=end_date, test_names=test_names)

        response = results.to_dict('records')

        return {
            "start_date": start_date,
            "end_date": end_date,
            "test_names": test_names,
            "results": response,
        }
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

