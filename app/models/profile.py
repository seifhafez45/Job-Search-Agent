"""
Structured profile tables — the output of Phase 2 (CV extraction) and the
single source every downstream feature (search, tailoring, skill-gap, agent) reads from.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Date
from sqlalchemy.orm import relationship

from app.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String)
    headline = Column(String)
    summary = Column(Text)
    location = Column(String)
    resume_file_path = Column(String)  # pointer to raw file in storage/resume_storage.py
    raw_resume_text = Column(Text)  # extracted text kept for re-processing/audit

    user = relationship("User", back_populates="profile")
    experiences = relationship("WorkExperience", back_populates="profile", cascade="all, delete-orphan")
    education = relationship("Education", back_populates="profile", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="profile", cascade="all, delete-orphan")


class WorkExperience(Base):
    __tablename__ = "work_experiences"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    company = Column(String)
    title = Column(String)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    description = Column(Text)

    profile = relationship("Profile", back_populates="experiences")


class Education(Base):
    __tablename__ = "education"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    institution = Column(String)
    degree = Column(String)
    field_of_study = Column(String)
    end_date = Column(Date, nullable=True)

    profile = relationship("Profile", back_populates="education")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    name = Column(String, nullable=False)
    proficiency = Column(String, nullable=True)  # e.g. "confirmed", "self-rated"

    profile = relationship("Profile", back_populates="skills")
