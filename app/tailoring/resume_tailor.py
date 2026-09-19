"""Resume bullet rewriting ONLY. Cover letter generation lives in cover_letter.py."""
from app.llm.client import complete
from app.tailoring.prompts import RESUME_TAILOR_SYSTEM_PROMPT


def tailor_bullets(experience_bullets: list[str], job_description: str) -> list[str]:
    user_prompt = (
        f"JOB POSTING:\n{job_description}\n\n"
        f"ORIGINAL BULLETS:\n" + "\n".join(f"- {b}" for b in experience_bullets)
        + "\n\nRewrite each bullet, one per line, same order."
    )
    raw = complete(RESUME_TAILOR_SYSTEM_PROMPT, user_prompt)
    return [line.strip("- ").strip() for line in raw.splitlines() if line.strip()]
