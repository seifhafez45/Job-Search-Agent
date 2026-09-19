"""Application tracker table (Normal software, Phase 1/7). No AI logic here."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_title = Column(String)
    company = Column(String)
    job_url = Column(String)
    status = Column(String, default="saved")  # saved -> applied -> interviewing -> offer/rejected
    tailored_resume_path = Column(String, nullable=True)
    cover_letter_text = Column(Text, nullable=True)
    applied_at = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="applications")
