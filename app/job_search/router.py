"""
HTTP layer only: parse query params into JobSearchFilters, call the service,
map errors to HTTP status codes. No business logic here.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
import re
import json

from app.common.exceptions import ExternalAPIError
from app.common.dependencies import get_current_user
from app.database import get_db
from app.job_search.filters import JobMatchFilters, JobSearchFilters
from app.job_search.service import search_jobs
from app.models.profile import Profile
from app.models.job_match import JobMatch
from app.memory.memory_store import get_user_memory
from app.schemas.job import JobPosting
from app.skill_gap.service import compare_profile_to_jobs

router = APIRouter(tags=["job-search"])

COUNTRY_ALIASES = {
    "gb": ("uk", "united kingdom", "great britain", "england", "scotland", "wales"),
    "us": ("us", "usa", "united states", "america"),
    "au": ("australia",),
    "ca": ("canada",),
    "in": ("india",),
    "de": ("germany",),
    "fr": ("france",),
    "nl": ("netherlands",),
    "nz": ("new zealand",),
    "za": ("south africa",),
    "sg": ("singapore",),
    "br": ("brazil",),
    "it": ("italy",),
    "pl": ("poland",),
}


def _cv_location_for_market(location: str | None, country: str) -> str | None:
    """Don't send a CV location to an unrelated Adzuna country market."""
    if not location:
        return None
    aliases = COUNTRY_ALIASES.get(country.lower())
    if aliases and any(alias in location.casefold() for alias in aliases):
        return location
    return None


def _cv_search_keywords(headline: str | None, skills: list) -> list[str]:
    # CV headlines often contain several specialties separated by bars/commas,
    # and PDF extraction can remove the space in "AI/ML Engineer".
    role = (headline or "").split("|", 1)[0].split(",", 1)[0].strip()
    role = re.sub(r"\bAI\s*/\s*ML\s*Engineer\b", "AI Engineer", role, flags=re.I)
    role = re.sub(r"\s+", " ", role).strip()
    candidates = [role] if role else []
    candidates.extend(skill.name for skill in skills[:3])
    return list(dict.fromkeys(value.strip() for value in candidates if len(value.strip()) >= 2))

# بستقبل الطلب من المستخدم عبر البحث 

@router.get("/search", response_model=list[JobPosting])
#التاكد من صحة اليانات المستخدم باعتها 
def search(filters: JobSearchFilters = Depends()):
    try:
        #لو سليمة بيبعتها ل الدالة دة الموجودة في ال service 
        return search_jobs(filters)
    except ExternalAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/matches", response_model=list[JobPosting])
def search_matches(
    filters: JobMatchFilters = Depends(),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Search jobs and rank each posting against the authenticated user's uploaded CV."""
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if not profile or not profile.resume_file_path:
        raise HTTPException(status_code=409, detail="Upload a CV before requesting job matches")
    memory = get_user_memory(db, user.id)

    search_keywords = [filters.keyword.strip()] if filters.keyword else _cv_search_keywords(
        profile.headline, profile.skills
    )
    if not search_keywords:
        raise HTTPException(
            status_code=422,
            detail="The CV needs a job headline or skills. You can also provide a search keyword.",
        )
    search_filters = JobSearchFilters(
        keyword=search_keywords[0],
        location=filters.location or _cv_location_for_market(profile.location, filters.country),
        remote=filters.remote,
        date_posted=filters.date_posted,
        country=filters.country,
        full_time=filters.full_time,
        page=filters.page,
        results_per_page=filters.results_per_page,
    )

    postings = []
    try:
        for keyword in search_keywords:
            postings = search_jobs(search_filters.model_copy(update={"keyword": keyword}))
            if postings or filters.keyword:
                break
    except ExternalAPIError as e:
        raise HTTPException(status_code=502, detail=str(e))

    try:
        comparisons = compare_profile_to_jobs(memory, postings)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        raise HTTPException(status_code=502, detail=f"Job match scoring failed: {e}") from e

    for posting in postings:
        comparison = comparisons.get(posting.external_id, {})
        posting.match_score = comparison.get("match_score", 0)
        posting.strengths = comparison.get("matched_skills", [])
        posting.weaknesses = comparison.get("missing_skills", [])
        posting.fit_summary = comparison.get("fit_summary", "Scoring was unavailable for this job.")

    records = [
        JobMatch(
            user_id=user.id,
            profile_id=profile.id,
            external_id=posting.external_id,
            title=posting.title,
            company=posting.company,
            location=posting.location,
            url=posting.url,
            job_description_snapshot=posting.description,
            match_score=int(posting.match_score or 0),
            strengths=json.dumps(posting.strengths, ensure_ascii=False),
            weaknesses=json.dumps(posting.weaknesses, ensure_ascii=False),
            fit_summary=posting.fit_summary,
            search_keyword=search_filters.keyword,
            search_country=search_filters.country,
            is_remote=posting.remote,
        )
        for posting in postings
    ]
    try:
        db.add_all(records)
        db.commit()
        for posting, record in zip(postings, records):
            posting.match_record_id = record.id
    except Exception:
        db.rollback()
        raise

    return sorted(postings, key=lambda posting: posting.match_score or 0, reverse=True)


@router.get("/matches/history")
def match_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Return this user's previously scored jobs, newest first."""
    records = (
        db.query(JobMatch)
        .filter(JobMatch.user_id == user.id)
        .order_by(desc(JobMatch.created_at), desc(JobMatch.id))
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "external_id": row.external_id,
            "title": row.title,
            "company": row.company,
            "location": row.location,
            "url": row.url,
            "description": row.job_description_snapshot,
            "match_score": row.match_score,
            "strengths": json.loads(row.strengths or "[]"),
            "weaknesses": json.loads(row.weaknesses or "[]"),
            "fit_summary": row.fit_summary,
            "search_keyword": row.search_keyword,
            "search_country": row.search_country,
            "remote": row.is_remote,
            "created_at": row.created_at,
        }
        for row in records
    ]
