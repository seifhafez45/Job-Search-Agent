"""
Interview-prep agent's persistence layer: study plan sessions + individual Q&A scored answers.
The Agent (interview_agent/) reads and writes here; this file defines shape only, no logic.
"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_role = Column(String)
    plan_json = Column(Text)  # the day-by-day plan produced by the agent
    current_day = Column(Integer, default=1)
    current_day_attempts = Column(Integer, default=0)  # resets to 0 on advance; caps repeat_topic loops
    status = Column(String, default="active")  # active | completed | abandoned
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="practice_sessions")
    answers = relationship("PracticeAnswer", back_populates="session", cascade="all, delete-orphan")


class PracticeAnswer(Base):
    __tablename__ = "practice_answers"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("practice_sessions.id"), nullable=False)
    day_number = Column(Integer)
    question = Column(Text)
    user_answer = Column(Text)
    score = Column(Float)  # e.g. 0-10, set by interview_agent/scorer.py
    feedback = Column(Text)

    session = relationship("PracticeSession", back_populates="answers")
