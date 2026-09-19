"""Prompt templates for each agent step: plan generation, question generation, answer scoring."""
from app.llm.base_prompts import JSON_ONLY_INSTRUCTION

PLAN_GENERATION_PROMPT = f"""You are an interview-prep coach. Build a day-by-day study plan
for the given target role and number of days, using the candidate's known skill gaps and any
relevant study resources provided. Each day should have a topic and 2-3 focus areas.
Return JSON: {{"days": [{{"day_number": int, "topic": str, "focus_areas": [str]}}]}}.
{JSON_ONLY_INSTRUCTION}
"""

QUESTION_GENERATION_PROMPT = f"""Generate one realistic interview question for the given day's
topic and focus areas, appropriate to the target role. Return JSON: {{"question": str}}.
{JSON_ONLY_INSTRUCTION}
"""

ANSWER_SCORING_PROMPT = f"""Score the candidate's mock interview answer from 0-10 and give
brief, specific, constructive feedback. Return JSON: {{"score": float, "feedback": str}}.
{JSON_ONLY_INSTRUCTION}
"""
