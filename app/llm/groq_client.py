"""
Scoped alternative to app/llm/client.py's complete(), used ONLY by
interview_agent and career_rag's service.py — not the shared client every
other teammate's feature depends on. Lets this part of the app run against
Groq's free tier instead of a paid Anthropic key, without touching anyone
else's code. Same function signature as app/llm/client.py's complete() so
it's a drop-in replacement for the files that import it.
"""
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

_client = Groq(api_key=settings.groq_api_key)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def complete(system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> str:
    """Single-turn completion. Returns plain text. Raises after 3 failed retries."""
    response = _client.chat.completions.create(
        model=settings.groq_model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content
