"""Domain models: plain data, no framework or storage dependencies"""

from dataclasses import dataclass


@dataclass
class BloodworkResult:
    """Data class for individual bloodwork test result"""

    test_name: str
    value: float
    unit: str
    test_date: str  # ISO date, YYYY-MM-DD
    reference_range: str | None = None


@dataclass
class BloodworkRecord:
    """Data class for complete bloodwork record"""

    patient_name: str
    test_date: str  # ISO date, YYYY-MM-DD
    results: list[BloodworkResult]
