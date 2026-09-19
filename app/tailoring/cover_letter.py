"""Cover letter generation ONLY."""
from app.llm.client import complete
from app.tailoring.prompts import COVER_LETTER_SYSTEM_PROMPT


def generate_cover_letter(profile_summary: str, job_title: str, company: str, job_description: str) -> str:
    user_prompt = (
        f"CANDIDATE SUMMARY:\n{profile_summary}\n\n"
        f"TARGET ROLE: {job_title} at {company}\n\nJOB POSTING:\n{job_description}"
    )
    return complete(COVER_LETTER_SYSTEM_PROMPT, user_prompt)
