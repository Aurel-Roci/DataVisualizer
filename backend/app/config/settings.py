"""Central application settings, read once from the environment (and .env)"""

import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv


def _parse_extensions(raw: str) -> frozenset[str]:
    """'pdf, .PDF' -> {'pdf'}: lowercase, no leading dot"""
    return frozenset(ext.strip().lower().lstrip(".") for ext in raw.split(",") if ext.strip())


def _parse_list(raw: str) -> tuple[str, ...]:
    """'a, b,' -> ('a', 'b')"""
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    # InfluxDB
    influxdb_host: str | None
    influxdb_token: str | None = field(repr=False)  # keep secrets out of logs/tracebacks
    influxdb_database: str
    # API
    api_host: str
    api_port: int
    log_level: str
    cors_origins: tuple[str, ...]
    default_patient_name: str
    # Uploads
    max_file_size: int
    allowed_extensions: frozenset[str]

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            influxdb_host=os.getenv("INFLUXDB_HOST"),
            influxdb_token=os.getenv("INFLUXDB_TOKEN"),
            influxdb_database=os.getenv("INFLUXDB_DATABASE", "bloodwork"),
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            cors_origins=_parse_list(os.getenv("CORS_ORIGINS", "http://localhost:5173")),
            default_patient_name=os.getenv("DEFAULT_PATIENT_NAME", "").strip() or "unknown",
            max_file_size=int(os.getenv("MAX_FILE_SIZE", "10485760")),  # 10MB
            allowed_extensions=_parse_extensions(os.getenv("ALLOWED_EXTENSIONS", "pdf")),
        )


@lru_cache
def get_settings() -> Settings:
    """Load .env and build the settings once; call get_settings.cache_clear() in tests"""
    load_dotenv()
    return Settings.from_env()
