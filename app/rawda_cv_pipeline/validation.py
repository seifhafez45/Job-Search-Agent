import re
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)


class CVProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    education: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)

    @field_validator("name", "email", "phone")
    @classmethod
    def clean_optional_text(cls, value):
        if value is None:
            return None

        value = value.strip()

        return value or None

    @field_validator(
        "education",
        "skills",
        "experience",
        "projects",
        "certifications",
    )
    @classmethod
    def clean_lists(cls, values):
        cleaned = []

        for value in values:
            if not isinstance(value, str):
                raise ValueError(
                    "Each item must be a string."
                )

            value = value.strip()

            if value:
                cleaned.append(value)

        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if value is None:
            return None

        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        if not re.match(pattern, value):
            raise ValueError("Invalid email format.")

        return value


def validate_profile(data: dict):
    try:
        profile = CVProfile.model_validate(data)

        return profile.model_dump(), []

    except ValidationError as error:
        return None, error.errors()
