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


class ProfileCreateRequestSchema(BaseProfileSchema):
    avatar: UploadFile | None = None

    @classmethod
    def from_form(
        cls,
        first_name: str | None = Form(None),
        last_name: str | None = Form(None),
        gender: GenderEnum | None = Form(None),
        date_of_birth: date | None = Form(None),
        info: str | None = Form(None),
        avatar: UploadFile | None = File(None),
    ) -> "ProfileCreateRequestSchema":
        return cls(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=date_of_birth,
            info=info,
            avatar=avatar,
        )

    @field_validator("avatar")
    @classmethod
    def validate_avatar(cls, value: UploadFile | None) -> UploadFile | None:
        if value is None:
            return value

        validate_image(value)
        return value


class ProfileUpdateRequestSchema(ProfileCreateRequestSchema):
    pass
