from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, field_validator


class BloodworkMetadata(BaseModel):
    name: str | None = None
    birthday: str | None = None

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

    patient_name: str | None
    test_date: datetime
    results: list[BloodworkResult]
