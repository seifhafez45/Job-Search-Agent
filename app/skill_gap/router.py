"""HTTP endpoint for skill-gap analysis ONLY."""
import json

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.common.dependencies import get_current_user
from app.skill_gap.service import analyze_skill_gap
from app.models.skill_gap import SkillGapReport

router = APIRouter()


class SkillGapRequest(BaseModel):
    job_title: str
    job_description: str


@router.post("/analyze")
def analyze(payload: SkillGapRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    report = analyze_skill_gap(db, user.id, payload.job_title, payload.job_description)
    return {
        "match_score": report.match_score,
        "matched_skills": json.loads(report.matched_skills or "[]"),
        "missing_skills": json.loads(report.missing_skills or "[]"),
        "fit_summary": report.fit_summary,
    }


@router.get("/history")
def analysis_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Return this user's previous skill-gap analyses, newest first."""
    reports = (
        db.query(SkillGapReport)
        .filter(SkillGapReport.user_id == user.id)
        .order_by(desc(SkillGapReport.created_at), desc(SkillGapReport.id))
        .limit(limit)
        .all()
    )
    return [
        {
            "id": report.id,
            "job_title": report.job_title,
            "job_description": report.job_description_snapshot,
            "match_score": report.match_score,
            "matched_skills": json.loads(report.matched_skills or "[]"),
            "missing_skills": json.loads(report.missing_skills or "[]"),
            "fit_summary": report.fit_summary,
            "created_at": report.created_at,
        }
        for report in reports
    ]
