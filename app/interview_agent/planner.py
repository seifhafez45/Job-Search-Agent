"""
Builds the initial day-by-day plan (agent's PLANNING step). Pulls skill gaps from
Memory and relevant study resources from career_rag, so the plan is grounded in
the user's actual data rather than generic advice.
"""
import json

from sqlalchemy.orm import Session

from app.llm.client import complete
from app.memory.memory_store import get_user_memory
from app.career_rag.retriever import retrieve_relevant_chunks
from app.interview_agent.prompts import PLAN_GENERATION_PROMPT


def build_plan(db: Session, user_id: int, target_role: str, days: int) -> dict:
    memory = get_user_memory(db, user_id)
    resource_hints = retrieve_relevant_chunks(f"interview prep for {target_role}", top_k=3)

    user_prompt = (
        f"TARGET ROLE: {target_role}\nDAYS: {days}\n"
        f"KNOWN SKILL GAPS: {memory.known_missing_skills}\n"
        f"RELEVANT RESOURCE EXCERPTS:\n" + "\n---\n".join(resource_hints)
    )
    raw = complete(PLAN_GENERATION_PROMPT, user_prompt)
    return json.loads(raw)
