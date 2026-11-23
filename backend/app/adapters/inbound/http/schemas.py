from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from ....config.settings import get_settings


class BloodworkMetadata(BaseModel):
    name: str = Field(default="", validate_default=True)
    birthday: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def default_blank_name(cls, v):
        """Influx drops a None tag silently, so always tag records with a patient"""
        if v is None or not str(v).strip():
            # One configurable default, so blank-named uploads (e.g. a backfill) share one series
            return get_settings().default_patient_name
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
