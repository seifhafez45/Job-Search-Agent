"""HTTP endpoint for structured job search ONLY (Phase 3 — the fast, no-AI-risk win)."""
from fastapi import APIRouter, Depends

from app.common.dependencies import get_current_user
from app.schemas.job import JobPosting
from app.job_search.service import search_jobs

router = APIRouter()


@router.get("/search", response_model=list[JobPosting])
def search(keyword: str, location: str | None = None, remote: bool | None = None,
           date_posted: str | None = None, user=Depends(get_current_user)):
    return search_jobs(keyword, location, remote, date_posted)
