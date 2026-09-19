"""
Memory read/write layer (the 'Memory' pillar in the architecture).
Every feature that needs persistent user context (skill_gap, tailoring,
interview_agent) calls get_user_memory() instead of querying multiple
tables itself — this is the ONE place that assembles memory.
"""
import json

from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.models.skill_gap import SkillGapReport
from app.models.practice_session import PracticeSession
from app.memory.memory_schemas import UserMemory
from app.schemas.profile import ProfileOut


def get_user_memory(db: Session, user_id: int) -> UserMemory:
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()

    missing_skills: set[str] = set()
    for report in db.query(SkillGapReport).filter(SkillGapReport.user_id == user_id).all():
        missing_skills.update(json.loads(report.missing_skills or "[]"))

    sessions = db.query(PracticeSession).filter(PracticeSession.user_id == user_id).all()
    practice_summary = f"{len(sessions)} interview-prep session(s) so far" if sessions else None

    return UserMemory(
        profile=ProfileOut.from_orm(profile) if profile else ProfileOut(),
        known_missing_skills=sorted(missing_skills),
        practice_history_summary=practice_summary,
    )
