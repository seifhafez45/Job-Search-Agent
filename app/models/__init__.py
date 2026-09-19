"""
Import all models here so Alembic autogenerate and Base.metadata.create_all()
can discover every table in one place.
"""
from app.models.user import User
from app.models.profile import Profile, WorkExperience, Education, Skill
from app.models.application import Application
from app.models.skill_gap import SkillGapReport
from app.models.practice_session import PracticeSession, PracticeAnswer
