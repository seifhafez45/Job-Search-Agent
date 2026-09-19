"""Auth identity table. Holds login credentials only — profile data lives in profile.py."""
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    profile = relationship("Profile", back_populates="user", uselist=False)
    applications = relationship("Application", back_populates="user")
    skill_gap_reports = relationship("SkillGapReport", back_populates="user")
    practice_sessions = relationship("PracticeSession", back_populates="user")
