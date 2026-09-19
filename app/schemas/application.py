"""Pydantic shapes for the application tracker API."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    job_title: str
    company: str
    job_url: Optional[str] = None
    status: str = "saved"


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    applied_at: Optional[datetime] = None


class ApplicationOut(BaseModel):
    id: int
    job_title: str
    company: str
    status: str
    applied_at: Optional[datetime] = None

    class Config:
        from_attributes = True
