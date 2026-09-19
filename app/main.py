"""
App entrypoint. ONLY job: create the FastAPI app, mount each feature router,
wire startup/shutdown hooks. No business logic lives here.
"""
from fastapi import FastAPI

from app.common.logging_config import configure_logging
from app.auth.router import router as auth_router
from app.cv_extraction.router import router as cv_router
from app.job_search.router import router as job_search_router
from app.skill_gap.router import router as skill_gap_router
from app.tailoring.router import router as tailoring_router
from app.career_rag.router import router as career_rag_router
from app.job_rag.router import router as job_rag_router
from app.interview_agent.router import router as interview_agent_router
from app.application_tracker.router import router as tracker_router

configure_logging()

app = FastAPI(title="Personal Job Search & Application Agent")

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(cv_router, prefix="/cv", tags=["cv-extraction"])
app.include_router(job_search_router, prefix="/jobs", tags=["job-search"])
app.include_router(skill_gap_router, prefix="/skill-gap", tags=["skill-gap"])
app.include_router(tailoring_router, prefix="/tailoring", tags=["tailoring"])
app.include_router(career_rag_router, prefix="/career-resources", tags=["career-rag"])
app.include_router(job_rag_router, prefix="/jobs/semantic", tags=["job-rag-stretch"])
app.include_router(interview_agent_router, prefix="/interview-prep", tags=["interview-agent"])
app.include_router(tracker_router, prefix="/applications", tags=["application-tracker"])


@app.get("/health")
def health():
    return {"status": "ok"}
