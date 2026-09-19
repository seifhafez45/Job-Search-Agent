"""Pydantic request/response shapes for the profile API. Mirrors models/profile.py but decoupled from the ORM."""
from datetime import date
from typing import Optional
from pydantic import BaseModel


class WorkExperienceOut(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class EducationOut(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    end_date: Optional[date] = None

    class Config:
        from_attributes = True


class SkillOut(BaseModel):
    name: str
    proficiency: Optional[str] = None

    class Config:
        from_attributes = True


class ProfileOut(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    experiences: list[WorkExperienceOut] = []
    education: list[EducationOut] = []
    skills: list[SkillOut] = []

    class Config:
        from_attributes = True
