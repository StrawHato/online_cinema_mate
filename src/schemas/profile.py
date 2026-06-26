from datetime import date

from fastapi import File, Form, UploadFile
from pydantic import BaseModel, ConfigDict, field_validator

from src.database.models.accounts import GenderEnum
from src.validation.profile import (
    validate_birth_date,
    validate_image,
    validate_name,
)


class BaseProfileSchema(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    gender: GenderEnum | None = None
    date_of_birth: date | None = None
    info: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, value: str | None) -> str | None:
        if value is None:
            return value

        validate_name(value)
        return value.strip()

    @field_validator("date_of_birth")
    @classmethod
    def validate_birth(cls, value: date | None) -> date | None:
        if value is None:
            return value

        validate_birth_date(value)
        return value

    @field_validator("info")
    @classmethod
    def validate_info(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()
        if not value:
            raise ValueError("Info cannot be empty.")

        return value
