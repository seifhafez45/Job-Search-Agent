# ============================================================
# الملف ده: حساب نسبة التطابق (match_score) لنتايج البحث
#
# فايدته:
# - بيخلّي كل وظيفة في نتايج /jobs/search ليها رقم يبيّن ملاءمتها للـ profile
# - بيوضّح ليه (matched_skills / missing_skills / match_reason)
#
# بيعمل إيه:
# 1. بيحسب تقدير سريع بالكلمات المفتاحية لكل الوظايف (fallback، فمفيش null أبداً)
# 2. بيبعت أول 10 وظايف للـ LLM في call واحد (batch) عشان الـ rate limit
# 3. بيعمل cache بسيط عشان نفس الوظيفة والـ profile ما يتبعتوش مرتين
# 4. بيرتّب النتايج من الأعلى تطابقاً للأقل
#
# مفيش فيه HTTP ولا كلام مع Adzuna، ده شغل router.py و service.py.
# ============================================================
"""Attach a profile-vs-job match score to search results (LLM batch with keyword fallback)."""
import asyncio
import hashlib
import json
import re

from groq import APIError
from pydantic import BaseModel, Field, ValidationError

from app.llm.client import complete
from app.schemas.job import JobPosting
from app.schemas.profile import ProfileOut
from app.skill_gap.prompts import compress_description

MAX_JOBS_FOR_LLM = 10
DESC_CHARS = 800

SYSTEM_PROMPT = """You are a strict job-matching evaluator.
Compare the candidate profile with each job posting.

Rules:
- Base your judgment ONLY on the provided profile and job text. Never invent skills.
- match_score: integer 0-100 (100 = perfect fit).
- matched_skills: skills the job requires that the candidate has.
- missing_skills: skills the job requires that the candidate lacks.
- reason: one short sentence explaining the score.
- Return ONLY a valid JSON object, no markdown, no extra text.

JSON format:
{"results": [{"id": "<job id>", "match_score": 0, "matched_skills": [], "missing_skills": [], "reason": ""}]}"""


class MatchItem(BaseModel):
    id: str
    match_score: int = Field(..., ge=0, le=100)
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    reason: str = ""


class MatchBatch(BaseModel):
    results: list[MatchItem]


_cache: dict[str, MatchItem] = {}


def _profile_key(profile: ProfileOut) -> str:
    return hashlib.sha1(profile.model_dump_json().encode()).hexdigest()[:12]


def _profile_brief(profile: ProfileOut) -> str:
    skills = ", ".join(s.name for s in profile.skills) or "N/A"
    return (
        f"Headline: {profile.headline or 'N/A'}\n"
        f"Summary: {profile.summary or 'N/A'}\n"
        f"Skills: {skills}"
    )


def _build_prompt(profile: ProfileOut, jobs: list[JobPosting]) -> str:
    items = [
        {
            "id": j.external_id,
            "title": j.title,
            "company": j.company,
            "description": compress_description(j.description, DESC_CHARS),
        }
        for j in jobs
    ]
    return (
        f"CANDIDATE PROFILE:\n{_profile_brief(profile)}\n\n"
        f"JOBS:\n{json.dumps(items, ensure_ascii=False)}"
    )


def _parse(raw: str) -> list[MatchItem]:
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return MatchBatch(**json.loads(cleaned)).results


def _apply_fallback(job: JobPosting, skill_names: list[str]) -> None:
    text = f"{job.title} {job.description}".lower()
    hits = [s for s in skill_names if s.lower() in text]
    job.match_score = min(100, len(hits) * 20)
    job.matched_skills = hits
    job.missing_skills = []
    job.match_reason = "Keyword-based estimate"


def _apply_item(job: JobPosting, item: MatchItem) -> None:
    job.match_score = item.match_score
    job.matched_skills = item.matched_skills
    job.missing_skills = item.missing_skills
    job.match_reason = item.reason


async def attach_matches(jobs: list[JobPosting], profile: ProfileOut) -> list[JobPosting]:
    skill_names = [s.name for s in profile.skills]
    for job in jobs:
        _apply_fallback(job, skill_names)

    key = _profile_key(profile)
    top = jobs[:MAX_JOBS_FOR_LLM]
    pending = [j for j in top if f"{key}:{j.external_id}" not in _cache]

    if pending:
        try:
            raw = await asyncio.to_thread(
                complete, _build_prompt(profile, pending), SYSTEM_PROMPT, 2500, True
            )
            for item in _parse(raw):
                _cache[f"{key}:{item.id}"] = item
        except (APIError, json.JSONDecodeError, ValidationError) as e:
            print(f"[job_search.matching] LLM failed, using keyword fallback: {e}")

    for job in top:
        item = _cache.get(f"{key}:{job.external_id}")
        if item:
            _apply_item(job, item)

    return sorted(jobs, key=lambda j: j.match_score or 0, reverse=True)