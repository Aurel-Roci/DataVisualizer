from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, field_validator

DEFAULT_PATIENT_NAME = "unknown"


class BloodworkMetadata(BaseModel):
    name: str = DEFAULT_PATIENT_NAME
    birthday: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def default_blank_name(cls, v):
        """Influx drops a None tag silently, so always tag records with a patient"""
        if v is None or not str(v).strip():
            return DEFAULT_PATIENT_NAME
        return str(v).strip()

    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, v):
        if v:
            try:
                datetime.strptime(v, "%d/%m/%Y")
            except ValueError:
                raise ValueError("Birthday must be in DD/MM/YYYY format") from None
        return v


@dataclass
class BloodworkResult:
    """Data class for individual bloodwork test result"""

    test_name: str
    value: float
    unit: str
    test_date: str
    reference_range: str | None = None


@dataclass
class BloodworkRecord:
    """Data class for complete bloodwork record"""

    patient_name: str
    test_date: datetime
    results: list[BloodworkResult]
