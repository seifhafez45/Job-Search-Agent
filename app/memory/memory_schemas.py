"""
Typed shape of 'memory' the rest of the app reads — a read-optimized bundle
of persistent facts about the user, assembled from several tables.
This is NOT a new DB table; it's a composed view over existing ones.
"""
from pydantic import BaseModel

from app.schemas.profile import ProfileOut


class UserMemory(BaseModel):
    profile: ProfileOut
    known_missing_skills: list[str] = []       # rolled up from SkillGapReport history
    practice_history_summary: str | None = None  # rolled up from PracticeSession/PracticeAnswer
