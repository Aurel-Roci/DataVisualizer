import logging
from typing import Dict

from fastapi import UploadFile, HTTPException

from ..models.bloodwork_metadata import BloodworkMetadata
from ..services.database import InfluxDBService
from ..services.pdf_parser import extract_pdf_data, parse_blood_work_table



logger = logging.getLogger(__name__)

async def handle_bloodwork(db: InfluxDBService,file: UploadFile, metadata: BloodworkMetadata) -> Dict:
    try:
        extracted_data = await extract_pdf_data(file, metadata.birthday)

        if not extracted_data or not extracted_data.get('tables'):
            raise HTTPException(
                status_code=400,
                detail="No table data found in PDF"
            )
        parsed_data = parse_blood_work_table(extracted_data, metadata.name)

        db.store_bloodwork_record(parsed_data)

        return {
            "filename": file.filename,
            "test_date": parsed_data.test_date,
            "name": metadata.name,
            "results": parsed_data.results,
            "message": "Blood work parsed successfully"
        }

    except Exception as e:
        logger.exception(f"Error processing file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )