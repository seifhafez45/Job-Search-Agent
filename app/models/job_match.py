"""Persist a user's CV-to-job match result for later review."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func

from app.database import Base


class JobMatch(Base):
    __tablename__ = "job_matches"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False, index=True)
    external_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    company = Column(String)
    location = Column(String)
    url = Column(Text)
    job_description_snapshot = Column(Text)
    match_score = Column(Integer, nullable=False)
    strengths = Column(Text, nullable=False, default="[]")
    weaknesses = Column(Text, nullable=False, default="[]")
    fit_summary = Column(Text)
    search_keyword = Column(String)
    search_country = Column(String)
    is_remote = Column(Boolean, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
