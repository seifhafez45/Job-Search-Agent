"""HTTP endpoint for semantic job search ONLY (stretch feature, Phase 7)."""
from fastapi import APIRouter, Depends

from app.common.dependencies import get_current_user
from app.schemas.job import JobPosting
from app.job_rag.service import semantic_search

router = APIRouter()


@router.get("/search", response_model=list[JobPosting])
def search(query: str, user=Depends(get_current_user)):
    return semantic_search(query)
