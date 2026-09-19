"""Thin orchestration: validate filters, call the API client. No HTTP-framework code here."""
from app.job_search.filters import normalize_filters
from app.job_search.job_api_client import fetch_postings
from app.schemas.job import JobPosting


def search_jobs(keyword: str, location: str | None, remote: bool | None, date_posted: str | None) -> list[JobPosting]:
    filters = normalize_filters(keyword, location, remote, date_posted)
    return fetch_postings(**filters)
