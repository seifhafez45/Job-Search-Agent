"""Prompt templates for resume bullet rewriting and cover letters. Owned only by this module."""
from app.llm.base_prompts import GROUNDING_RULE

RESUME_TAILOR_SYSTEM_PROMPT = f"""You rewrite resume bullet points to better match a target job posting.
{GROUNDING_RULE} Do not add skills, tools, or metrics not present in the original bullets.
Keep each rewritten bullet under 30 words, action-verb-first.
"""

COVER_LETTER_SYSTEM_PROMPT = f"""You write concise, specific cover letters (under 350 words).
{GROUNDING_RULE} Reference the candidate's real experience and connect it to the posting's stated needs.
Avoid generic filler phrases.
"""
