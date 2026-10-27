"""
Builds the initial personalized interview-preparation plan.

The planner combines:
- persistent user memory
- historical skill gaps
- previous interview performance

Deliberately does not depend on career_rag: RAG-grounded planning is a
possible later enhancement, not a dependency of the core agent loop. This
allows the generated plan to adapt to the individual user instead of
producing generic interview preparation advice.
"""

import json

from sqlalchemy.orm import Session

from app.llm.client import complete
from app.memory.context_builder import get_user_memory_context
from app.interview_agent.prompts import PLAN_GENERATION_PROMPT


def build_plan(
    db: Session,
    user_id: int,
    target_role: str,
    days: int,
) -> dict:
    """
    Generate a personalized interview-preparation plan.

    Persistent memory gives the planner historical context (recurring
    skill gaps, past weak answers) to personalize the plan.
    """

    memory_context = get_user_memory_context(
        db=db,
        user_id=user_id,
    )

    user_prompt = f"""
TARGET ROLE: {target_role}
AVAILABLE DAYS: {days}

{memory_context}

Generate a personalized interview-preparation plan for this candidate.
"""

    raw = complete(
        PLAN_GENERATION_PROMPT,
        user_prompt,
    )

    return json.loads(raw)
