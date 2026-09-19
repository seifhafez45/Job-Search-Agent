"""HTTP endpoint for skill-gap analysis ONLY."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.common.dependencies import get_current_user
from app.skill_gap.service import analyze_skill_gap

router = APIRouter()


class SkillGapRequest(BaseModel):
    job_title: str
    job_description: str


@router.post("/analyze")
def analyze(payload: SkillGapRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    report = analyze_skill_gap(db, user.id, payload.job_title, payload.job_description)
    return {
        "matched_skills": report.matched_skills,
        "missing_skills": report.missing_skills,
        "fit_summary": report.fit_summary,
    }
