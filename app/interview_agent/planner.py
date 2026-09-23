"""
Builds the initial day-by-day plan (agent's PLANNING step). Pulls skill gaps from
Memory so the plan is grounded in the user's actual data rather than generic advice.
Deliberately does not depend on career_rag: RAG-grounded planning is a possible
later enhancement, not a dependency of the core agent loop.
"""
import json

from sqlalchemy.orm import Session

from app.llm.client import complete
from app.memory.memory_store import get_user_memory
from app.interview_agent.prompts import PLAN_GENERATION_PROMPT


def build_plan(db: Session, user_id: int, target_role: str, days: int) -> dict:
    memory = get_user_memory(db, user_id)

    user_prompt = (
        f"TARGET ROLE: {target_role}\nDAYS: {days}\n"
        f"KNOWN SKILL GAPS: {memory.known_missing_skills}"
    )
    raw = complete(PLAN_GENERATION_PROMPT, user_prompt)
    return json.loads(raw)
