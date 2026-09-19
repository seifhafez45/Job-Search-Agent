"""Scores a single mock answer ONLY. No branching/decision logic here — see state.py for that."""
import json

from app.llm.client import complete
from app.interview_agent.prompts import ANSWER_SCORING_PROMPT


def score_answer(question: str, user_answer: str) -> dict:
    user_prompt = f"QUESTION: {question}\nCANDIDATE ANSWER: {user_answer}"
    raw = complete(ANSWER_SCORING_PROMPT, user_prompt)
    return json.loads(raw)  # {"score": float, "feedback": str}
