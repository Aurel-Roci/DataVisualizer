from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, field_validator
from typing import Optional, List


class BloodworkMetadata(BaseModel):
    name: Optional[str] = None
    birthday: Optional[str] = None

    @field_validator('birthday')
    @classmethod
    def validate_birthday(cls, v):
        if v:
            try:
                datetime.strptime(v, "%d/%m/%Y")
            except ValueError:
                raise ValueError("Birthday must be in DD/MM/YYYY format")
        return v


@dataclass
class BloodworkResult:
    """Data class for individual bloodwork test result"""
    test_name: str
    value: float
    unit: str
    test_date: str
    reference_range: Optional[str] = None


@dataclass
class BloodworkRecord:
    """Data class for complete bloodwork record"""
    patient_name: str
    test_date: datetime
    results: List[BloodworkResult]
