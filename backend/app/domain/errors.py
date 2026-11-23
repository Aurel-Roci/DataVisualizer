"""Domain errors. Adapters translate these (e.g. to HTTP status codes); the core never knows how."""


class BloodworkError(Exception):
    """Base class for all expected, domain-level failures"""


class InvalidReport(BloodworkError):
    """The uploaded content is not a usable blood work report"""


class FileTooLarge(BloodworkError):
    """The upload exceeds the configured size limit"""

    def __init__(self, max_size: int):
        super().__init__(f"File too large. Maximum size: {max_size} bytes")
        self.max_size = max_size


class ExtractionFailed(BloodworkError):
    """The report could not be read (corrupt or unsupported PDF)"""


class StorageUnavailable(BloodworkError):
    """The results could not be stored"""


class InvalidDateRange(BloodworkError):
    """The requested date range is not valid"""
