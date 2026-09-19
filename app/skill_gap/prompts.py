"""Prompt template for CV-vs-posting comparison. Owned only by this module."""
from app.llm.base_prompts import JSON_ONLY_INSTRUCTION, GROUNDING_RULE

SKILL_GAP_SYSTEM_PROMPT = f"""You are a career advisor comparing a candidate's confirmed profile
against a job posting. {GROUNDING_RULE}
Return JSON: {{"matched_skills": [str], "missing_skills": [str], "fit_summary": str}}.
{JSON_ONLY_INSTRUCTION}
"""
