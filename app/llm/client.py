"""
Thin wrapper around the Anthropic SDK. EVERY module that calls an LLM
(cv_extraction, skill_gap, tailoring, career_rag answer synthesis,
interview_agent) imports `complete()` from here instead of instantiating
its own client. Keeps model choice, retries, and error handling in one place.
"""
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

_client = Anthropic(api_key=settings.anthropic_api_key)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def complete(system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> str:
    """Single-turn completion. Returns plain text. Raises after 3 failed retries."""
    response = _client.messages.create(
        model=settings.llm_model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
