"""
Thin wrapper around the LLM provider (Groq). EVERY module that calls an LLM
(cv_extraction, skill_gap, tailoring, career_rag answer synthesis,
interview_agent) imports `complete()` from here instead of instantiating
its own client. Keeps model choice, retries, and error handling in one place.
"""
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

_client = Groq(api_key=settings.groq_api_key)

# gpt-oss models think before answering; extra tokens keep the reply from coming back empty.
REASONING_HEADROOM = 2000


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def complete(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1500,
    json_mode: bool = False,
) -> str:
    """Single-turn completion. Returns plain text. Raises after 3 failed retries."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    is_reasoning_model = settings.llm_model.startswith("openai/gpt-oss")

    kwargs = {
        "model": settings.llm_model,
        "messages": messages,
        "max_tokens": max_tokens + (REASONING_HEADROOM if is_reasoning_model else 0),
        "temperature": 0,
    }
    if is_reasoning_model:
        kwargs["extra_body"] = {"reasoning_effort": "low"}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = _client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""