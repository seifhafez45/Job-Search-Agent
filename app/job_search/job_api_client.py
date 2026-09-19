"""
ONLY module that talks to the external job-board API (HTTP calls, auth headers,
pagination, response parsing into JobPosting). No filtering/business logic here.
"""
import requests

from app.config import settings
from app.common.exceptions import ExternalAPIError
from app.schemas.job import JobPosting


def fetch_postings(keyword: str, location: str | None, remote: bool | None, date_posted: str | None) -> list[JobPosting]:
    params = {"q": keyword, "location": location, "remote": remote, "date_posted": date_posted}
    try:
        resp = requests.get(
            f"{settings.job_api_base_url}/search",
            params={k: v for k, v in params.items() if v is not None},
            headers={"Authorization": f"Bearer {settings.job_api_key}"},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ExternalAPIError(f"Job API request failed: {e}")

    return [JobPosting(**item) for item in resp.json().get("results", [])]
