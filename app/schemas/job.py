"""Pydantic shapes for job-search results, shared by job_search/ and job_rag/ so both return one consistent shape."""
from typing import Optional
from pydantic import BaseModel


class JobPosting(BaseModel):
    external_id: str
    title: str
    company: str
    location: Optional[str] = None
    remote: Optional[bool] = None
    url: str
    description: str
    posted_date: Optional[str] = None
    match_score: Optional[float] = None  # populated only by job_rag semantic search
