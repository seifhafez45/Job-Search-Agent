"""Cover letter generation ONLY."""
import json
import logging

import requests
from pydantic import BaseModel, ConfigDict, field_validator
from app.config import settings
from app.llm.client import complete
from app.tailoring.prompts import (
    CRITIQUE_SYSTEM_PROMPT,
    DRAFT_SYSTEM_PROMPT,
    RESEARCH_COMPANY_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)



class CoverLetterCritique(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: int
    issues: list[str]
    unsupported_claims: list[str]

    @field_validator("score")
    @classmethod
    def validate_score(cls, score: int) -> int:
        if not 1 <= score <= 10:
            raise ValueError("Score must be from 1 to 10.")
        return score

def _web_search(query: str, n: int = 4) -> list[dict]:
    r = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": settings.tavily_api_key,
            "query": query,
            "max_results": n,
            "search_depth": "basic",
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("results", [])


def research_company(company: str, job_title: str) -> str:
    """Search the web, then have the LLM distill only what the results support."""


    try:
        results = _web_search(f"{company} company overview products mission")
        results += _web_search(f"{company} recent news announcements 2026", n=3)
        if not results:
            return ""

        sources = "\n\n".join(
            f"[{i}] {r['title']} ({r['url']})\n{r['content'][:800]}"
            for i, r in enumerate(results, 1)
        )
        user_prompt =(f"Company: {company}\nCandidate role: {job_title}\n\nSOURCES:\n{sources}\n\n"
                "Write a brief of at most 200 words: what the company does, recent "
                "news/launches, mission/values, and anything relevant to this role. "
                "Cite source numbers like [2] after each fact.")
        return complete(RESEARCH_COMPANY_SYSTEM_PROMPT,user_prompt,
            max_tokens=1500,
        ).replace("UNRELIABLE", "")
    except requests.RequestException:
        logger.warning("Company research web search failed for %s", company, exc_info=True)
        return ""

def draft_cover_letter(summary, job_title, company, job_description,
                       company_brief, bullets, previous=None, feedback=None) -> str:
    user_prompt = (
        f"Role: {job_title} at {company}\n\nJob description:\n{job_description}\n\n"
        f"Company brief:\n{company_brief or '(none available)'}\n\n"
        f"Candidate summary:\n{summary}\n\nCandidate achievements:\n"
        + "\n".join(f"- {b}" for b in bullets)
    )
    if previous and feedback:
        user_prompt += (
            f"\n\nPrevious draft:\n{previous}\n\n"
            f"Reviewer feedback to address:\n{json.dumps(feedback['issues'], indent=2)}\n"
            "Rewrite the letter fixing these issues."
        )
    return complete(DRAFT_SYSTEM_PROMPT, user_prompt, max_tokens=1500)


def critique_cover_letter(letter, job_title, company, job_description,
                          company_brief, summary, bullets) -> dict:
    user_prompt = (
            f"Evaluate this cover letter for {job_title} at {company}.\n\n"
            f"LETTER:\n{letter}\n\nJOB DESCRIPTION:\n{job_description}\n\n"
            f"COMPANY BRIEF:\n{company_brief or '(none)'}\n\n"
            f"CANDIDATE FACTS:\n{summary}\n" + "\n".join(f"- {b}" for b in bullets) +
            "\n\nScore 1-10 overall on: fit to requirements, specificity, accurate use "
            "of company facts, no claims unsupported by candidate facts, no cliches, "
            "length/tone.\n"
            'Return JSON: {"score": <int>, "issues": [<specific actionable strings>], '
            '"unsupported_claims": [<strings>]}'
        )
    raw = complete(
        CRITIQUE_SYSTEM_PROMPT,
        user_prompt,
        max_tokens=1500,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "cover_letter_critique",
                "strict": True,
                "schema": CoverLetterCritique.model_json_schema(),
            },
        },
    )
    critique = CoverLetterCritique.model_validate_json(raw)

    return {
        "score": critique.score,
        "issues": critique.issues + [
            f"Remove or fix unsupported claim: {claim}"
            for claim in critique.unsupported_claims
        ],
    }


def generate_cover_letter_with_critique(summary, job_title, company,
                                        job_description, bullets , max_revisions=3 ,pass_score =8):
    brief = research_company(company, job_title)
    letter = draft_cover_letter(summary, job_title, company, job_description, brief, bullets)

    for _ in range(max_revisions):
        critique = critique_cover_letter(
            letter, job_title, company, job_description, brief, summary, bullets
        )
        if critique["score"] >= pass_score and not critique["issues"]:
            break
        letter = draft_cover_letter(
            summary, job_title, company, job_description, brief, bullets,
            previous=letter, feedback=critique,
        )
    return letter, brief
