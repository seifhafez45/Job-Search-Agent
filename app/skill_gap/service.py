"""
Orchestrates Phase 4a: pulls profile from Memory, compares against a posting
via LLM, persists a SkillGapReport row. This is the ONLY module that writes
to the skill_gap_reports table.
"""
import json

from sqlalchemy.orm import Session

from app.llm.client import complete
from app.memory.memory_store import get_user_memory
from app.models.skill_gap import SkillGapReport
from app.skill_gap.prompts import SKILL_GAP_SYSTEM_PROMPT


def analyze_skill_gap(db: Session, user_id: int, job_title: str, job_description: str) -> SkillGapReport:
    memory = get_user_memory(db, user_id)
    user_prompt = f"CANDIDATE PROFILE:\n{memory.profile.json()}\n\nJOB POSTING:\n{job_description}"

    raw_json = complete(SKILL_GAP_SYSTEM_PROMPT, user_prompt)
    result = json.loads(raw_json)

    report = SkillGapReport(
        user_id=user_id,
        job_title=job_title,
        job_description_snapshot=job_description,
        matched_skills=json.dumps(result["matched_skills"]),
        missing_skills=json.dumps(result["missing_skills"]),
        fit_summary=result["fit_summary"],
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
