"""Domain models: plain data, no framework or storage dependencies"""

from dataclasses import dataclass
from datetime import datetime


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
