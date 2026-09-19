"""Stores skill-gap comparison results (CV vs a posting) so history persists across sessions."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class SkillGapReport(Base):
    __tablename__ = "skill_gap_reports"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_title = Column(String)
    job_description_snapshot = Column(Text)  # posting text at time of analysis
    matched_skills = Column(Text)  # JSON-encoded list
    missing_skills = Column(Text)  # JSON-encoded list
    fit_summary = Column(Text)  # LLM's qualitative verdict
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="skill_gap_reports")
