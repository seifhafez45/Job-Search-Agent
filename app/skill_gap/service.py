"""Skill-gap orchestration: build prompt -> call LLM -> parse and validate -> retry once on bad JSON."""
import asyncio
import json
import logging
import re

from pydantic import ValidationError

from app.llm.client import complete
from app.schemas.skill_gap import SkillGapRequest, SkillGapResult
from app.skill_gap.prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 2


class SkillGapError(Exception):
    """Raised when the LLM response can't be turned into a valid result."""


def _parse(raw: str) -> SkillGapResult:
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    return SkillGapResult(**json.loads(cleaned))


async def analyze_skill_gap(req: SkillGapRequest) -> SkillGapResult:
    user_prompt = build_user_prompt(req.profile, req.job)

    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        raw = await asyncio.to_thread(
            complete,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=1500,
            json_mode=True,
        )
        try:
            return _parse(raw)
        except (json.JSONDecodeError, ValidationError, TypeError) as e:
            last_error = e
            logger.warning(
                "skill_gap attempt %d failed to parse: %s | raw (first 500 chars): %s",
                attempt, e, raw[:500],
            )

    raise SkillGapError(f"LLM returned invalid output: {last_error}")