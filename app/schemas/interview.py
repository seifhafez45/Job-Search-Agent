"""Pydantic shapes for the interview-prep agent's API surface."""
from typing import Optional
from pydantic import BaseModel


class StartPlanRequest(BaseModel):
    target_role: str
    days: int = 5


class AnswerSubmission(BaseModel):
    session_id: int
    day_number: int
    question: str
    user_answer: str


class ScoredFeedback(BaseModel):
    score: float
    feedback: str
    next_action: str  # "repeat_topic" | "advance" | "nudge_break"
