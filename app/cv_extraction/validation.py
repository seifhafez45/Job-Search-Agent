from datetime import date
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)


class WorkExperienceData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


class EducationData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    end_date: Optional[date] = None


class SkillData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    proficiency: Optional[str] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Skill name cannot be empty.")

        return value


class CVProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None

    experiences: list[WorkExperienceData] = Field(
        default_factory=list
    )

    education: list[EducationData] = Field(
        default_factory=list
    )

    skills: list[SkillData] = Field(
        default_factory=list
    )

    @field_validator(
        "full_name",
        "headline",
        "summary",
        "location",
    )
    @classmethod
    def clean_optional_text(cls, value):
        if value is None:
            return None

        value = value.strip()

        return value or None


def validate_profile(data: dict):
    try:
        profile = CVProfile.model_validate(data)

        return profile.model_dump(), []

    except ValidationError as error:
        return None, error.errors()
