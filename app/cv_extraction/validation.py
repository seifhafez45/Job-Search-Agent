"""
Validation and normalization of LLM extraction output.

Converts untrusted LLM data into an ExtractedProfile.
All fields match the existing SQLAlchemy models:
Profile, WorkExperience, Education, Skill.

No LLM or database access here.
"""

import re
from datetime import date, datetime
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)

from app.common.exceptions import ExtractionError


MAX_EXPERIENCES = 30
MAX_EDUCATION = 15
MAX_SKILLS = 100

MAX_SKILL_NAME_LEN = 100

_NULL_WORDS = {
    "null",
    "none",
    "n/a",
    "na",
    "-",
    "--",
    "unknown",
}

_PRESENT_WORDS = {
    "present",
    "current",
    "currently",
    "now",
    "ongoing",
    "today",
    "to date",
    "till date",
}

_DATE_FORMATS = (
    "%b %Y",
    "%B %Y",
    "%m/%Y",
    "%Y/%m",
)


def _clean_str(value: Any) -> str | None:
    """
    Clean string values.

    Returns None for empty or invalid values.
    """

    if value is None or isinstance(value, (dict, list, bool)):
        return None

    text = str(value).replace("\x00", "").strip()

    if not text:
        return None

    if text.lower() in _NULL_WORDS:
        return None

    return text


def parse_date(value: Any) -> date | None:
    """
    Normalize different date formats into datetime.date.

    Supported examples:
        2023
        2023-05
        2023-05-15
        May 2023
        May 15, 2023
        05/2023

    Present/current dates return None.
    Invalid dates return None.
    """

    if isinstance(value, datetime):
        result = value.date()

    elif isinstance(value, date):
        result = value

    else:
        text = _clean_str(value)

        if text is None:
            return None

        if text.lower() in _PRESENT_WORDS:
            return None

        result = None

        # ISO-like formats: YYYY, YYYY-MM, YYYY-MM-DD
        match = re.fullmatch(
            r"(\d{4})(?:-(\d{1,2})(?:-(\d{1,2}))?)?",
            text,
        )

        if match:
            year = int(match.group(1))
            month = int(match.group(2) or 1)
            day = int(match.group(3) or 1)

            try:
                result = date(year, month, day)
            except ValueError:
                return None

        else:
            # Other supported formats
            for fmt in _DATE_FORMATS:
                try:
                    result = datetime.strptime(text, fmt).date()
                    break
                except ValueError:
                    continue

            # Additional common format
            if result is None:
                try:
                    result = datetime.strptime(
                        text,
                        "%B %d, %Y",
                    ).date()
                except ValueError:
                    return None

    # Prevent unrealistic dates.
    current_year = datetime.now().year

    if not 1950 <= result.year <= current_year + 10:
        return None

    return result


CleanStr = Annotated[
    str | None,
    BeforeValidator(_clean_str),
]

OptDate = Annotated[
    date | None,
    BeforeValidator(parse_date),
]


class BaseExtractionModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )


class ExperienceIn(BaseExtractionModel):
    company: CleanStr = None
    title: CleanStr = None
    start_date: OptDate = None
    end_date: OptDate = None
    description: CleanStr = None


class EducationIn(BaseExtractionModel):
    institution: CleanStr = None
    degree: CleanStr = None
    field_of_study: CleanStr = None
    end_date: OptDate = None


class SkillIn(BaseExtractionModel):
    name: CleanStr = None
    proficiency: CleanStr = None


class ExtractedProfile(BaseExtractionModel):

    full_name: CleanStr = None
    headline: CleanStr = None
    summary: CleanStr = None
    location: CleanStr = None

    experiences: list[ExperienceIn] = Field(
        default_factory=list
    )

    education: list[EducationIn] = Field(
        default_factory=list
    )

    skills: list[SkillIn] = Field(
        default_factory=list
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_shape(cls, data: Any) -> Any:
        """
        Normalize inconsistent LLM output before validation.
        """

        if not isinstance(data, dict):
            raise ValueError(
                "The extraction result must be a JSON object."
            )

        data = dict(data)

        # Support singular "experience" as a fallback.
        if "experiences" not in data and "experience" in data:
            data["experiences"] = data["experience"]

        # Ensure list fields are always lists.
        for key in ("experiences", "education", "skills"):

            value = data.get(key)

            if not isinstance(value, list):
                data[key] = []

        # Support skills returned as strings.
        data["skills"] = [
            {"name": skill}
            if isinstance(skill, str)
            else skill
            for skill in data["skills"]
        ]

        # Ignore invalid list items.
        for key in ("experiences", "education", "skills"):

            data[key] = [
                item
                for item in data[key]
                if isinstance(item, dict)
            ]

        return data

    @model_validator(mode="after")
    def finalize_data(self) -> "ExtractedProfile":

        # Remove completely empty experiences.
        self.experiences = [
            experience
            for experience in self.experiences
            if (
                experience.company
                or experience.title
                or experience.description
            )
        ]

        # Remove completely empty education entries.
        self.education = [
            education
            for education in self.education
            if (
                education.institution
                or education.degree
                or education.field_of_study
            )
        ]

        # Remove empty and duplicate skills.
        unique_skills = []
        seen_skills = set()

        for skill in self.skills:

            if not skill.name:
                continue

            if len(skill.name) > MAX_SKILL_NAME_LEN:
                continue

            key = skill.name.casefold()

            if key in seen_skills:
                continue

            seen_skills.add(key)
            unique_skills.append(skill)

        self.skills = unique_skills

        # Apply maximum limits.
        self.experiences = self.experiences[:MAX_EXPERIENCES]
        self.education = self.education[:MAX_EDUCATION]
        self.skills = self.skills[:MAX_SKILLS]

        return self

    def is_empty(self) -> bool:
        """
        Check whether the extraction contains any useful information.
        """

        return not (
            self.full_name
            or self.headline
            or self.summary
            or self.location
            or self.experiences
            or self.education
            or self.skills
        )


def validate_extracted(data: Any) -> ExtractedProfile:
    """
    Validate and normalize extracted CV data.

    Raises:
        ExtractionError: if the result is invalid or empty.
    """

    try:

        profile = ExtractedProfile.model_validate(data)

    except ValidationError as exc:

        raise ExtractionError(
            "The extracted CV data did not match the expected structure."
        ) from exc

    if profile.is_empty():

        raise ExtractionError(
            "No profile information could be extracted from the CV."
        )

    return profile
