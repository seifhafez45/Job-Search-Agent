# ============================================================
# الملف ده: مكان نصوص الـ prompt بتاعة الـ skill_gap
#
# فايدته:
# - كل نصوص الـ prompt في مكان واحد
# - لو جودة الرد قلّت، تعدّل هنا بس من غير ما تلمس الكود
#
# بيعمل إيه:
# - SYSTEM_PROMPT: بيشرح للـ LLM دوره وقواعد الرد (JSON بس، من غير اختراع مهارات)
# - compress_description: بيضغط وصف الوظيفة الطويل بذكاء،
#   بيحتفظ بفقرات المتطلبات والمهارات وبيشيل الكلام العام (benefits, about us)
# - build_user_prompt: بيحوّل الـ profile والوظيفة لنص مقروء للـ LLM
#
# مفيش فيه استدعاء للـ LLM ولا منطق خاص بالـ API، نصوص وتنسيق بس.
# ============================================================
"""All prompt text for skill-gap analysis. Edit prompts here only; no LLM calls live in this file."""
import html
import re

from app.schemas.job import JobPosting
from app.schemas.profile import ProfileOut

SYSTEM_PROMPT = """You are an expert technical recruiter and career coach.
Compare the candidate profile with the job posting and identify the skill gap.

Rules:
- Base your analysis ONLY on the provided profile and job text. Never invent skills or experience.
- match_score: integer 0-100 (100 = perfect fit).
- strengths: skills/experience the candidate has that the job requires.
- missing_skills: skills the job requires that the candidate lacks (most important first).
- recommendations: 2-4 short, actionable learning suggestions to close the gap.
- reasoning: 1-2 sentences explaining the score.
- Return ONLY a valid JSON object, no markdown, no extra text.

JSON format:
{
  "match_score": 0,
  "strengths": [],
  "missing_skills": [],
  "recommendations": [],
  "reasoning": ""
}"""

MAX_DESC_CHARS = 6000

# كلمات بتدل إن الفقرة فيها متطلبات حقيقية
REQUIREMENT_HINTS = (
    "require", "qualification", "skill", "experience", "must", "responsibilit",
    "you will", "what you", "nice to have", "preferred", "tech stack",
    "proficien", "knowledge", "familiar", "degree", "years",
)

# كلمات بتدل إن الفقرة كلام عام مش مهم للمقارنة
NOISE_HINTS = (
    "equal opportunity", "we offer", "benefits", "about us", "insurance",
    "vacation", "apply now", "disclaimer", "our mission", "perks",
)


def _clean(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def _split_blocks(text: str) -> list[str]:
    blocks = [b.strip() for b in text.split("\n") if b.strip()]
    # لو النص جاي فقرة واحدة طويلة، نقسمه لجمل
    if len(blocks) <= 2:
        blocks = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    return blocks


def _score_block(block: str, index: int) -> int:
    lowered = block.lower()
    score = sum(2 for h in REQUIREMENT_HINTS if h in lowered)
    score -= sum(2 for h in NOISE_HINTS if h in lowered)
    if index == 0:
        score += 1  # أول فقرة غالباً ملخص الوظيفة
    return score


def compress_description(text: str, max_chars: int = MAX_DESC_CHARS) -> str:
    """يرجّع الوصف كامل لو قصير، أو أهم الفقرات بنفس ترتيبها الأصلي لو طويل."""
    cleaned = _clean(text)
    if len(cleaned) <= max_chars:
        return cleaned

    blocks = _split_blocks(cleaned)
    ranked = sorted(range(len(blocks)), key=lambda i: (-_score_block(blocks[i], i), i))

    chosen: set[int] = set()
    used = 0
    for i in ranked:
        cost = len(blocks[i]) + 1
        if used + cost > max_chars:
            continue
        chosen.add(i)
        used += cost

    if not chosen:  # فقرة واحدة أطول من الحد
        return cleaned[:max_chars]

    return "\n".join(blocks[i] for i in sorted(chosen))


def _format_profile(profile: ProfileOut) -> str:
    skills = ", ".join(s.name for s in profile.skills) or "N/A"

    experiences = "\n".join(
        f"- {e.title or 'N/A'} at {e.company or 'N/A'}: {e.description or ''}".strip()
        for e in profile.experiences
    ) or "N/A"

    education = "\n".join(
        f"- {ed.degree or ''} {ed.field_of_study or ''} at {ed.institution or ''}".strip()
        for ed in profile.education
    ) or "N/A"

    return (
        f"Headline: {profile.headline or 'N/A'}\n"
        f"Summary: {profile.summary or 'N/A'}\n"
        f"Skills: {skills}\n"
        f"Experience:\n{experiences}\n"
        f"Education:\n{education}"
    )


def build_user_prompt(profile: ProfileOut, job: JobPosting) -> str:
    return (
        "CANDIDATE PROFILE:\n"
        f"{_format_profile(profile)}\n\n"
        "JOB POSTING:\n"
        f"Title: {job.title}\n"
        f"Company: {job.company}\n"
        f"Description: {compress_description(job.description)}"
    )