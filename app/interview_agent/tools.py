"""
Callable 'tools' the agent's planning/branching logic invokes at runtime:
generating the next mock question and persisting answers. Kept separate from
planner.py (initial plan) and scorer.py (grading) since this is the
runtime-execution surface, not planning or scoring itself.
"""
import json

from sqlalchemy.orm import Session

from app.llm.client import complete
from app.models.practice_session import PracticeAnswer
from app.interview_agent.prompts import QUESTION_GENERATION_PROMPT


def generate_question(topic: str, focus_areas: list[str], target_role: str) -> str:
    user_prompt = f"ROLE: {target_role}\nTOPIC: {topic}\nFOCUS AREAS: {focus_areas}"
    raw = complete(QUESTION_GENERATION_PROMPT, user_prompt)
    return json.loads(raw)["question"]


def save_answer(db: Session, session_id: int, day_number: int, question: str,
                 user_answer: str, score: float, feedback: str) -> PracticeAnswer:
    answer = PracticeAnswer(
        session_id=session_id, day_number=day_number, question=question,
        user_answer=user_answer, score=score, feedback=feedback,
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer
