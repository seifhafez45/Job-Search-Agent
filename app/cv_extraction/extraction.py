"""
Extract structured profile data from raw CV text.

This module is the only cv_extraction module
that communicates with the LLM.

Uses the shared app.llm.client.complete() function.

No file parsing and no database access here.
"""

import json
import logging
import re

from typing import Any

from app.common.exceptions import (
    ExternalAPIError,
    ExtractionError,
)

from app.cv_extraction.errors import EmptyCVError

from app.cv_extraction.prompts import (
    CV_EXTRACTION_SYSTEM_PROMPT,
)

from app.cv_extraction.validation import (
    ExtractedProfile,
    validate_extracted,
)

from app.llm.client import complete


logger = logging.getLogger(__name__)


MAX_OUTPUT_TOKENS = 4000

MAX_CV_CHARS = 40_000

MAX_ATTEMPTS = 2

USE_JSON_MODE = True


def parse_json_response(raw: str | None) -> dict[str, Any]:
    """
    Parse a JSON object from the LLM response.

    Handles:
        - Empty responses
        - Markdown code fences
        - Extra text around JSON
        - Invalid JSON
        - Non-object JSON responses
    """

    if raw is None or not raw.strip():

        raise ExtractionError(
            "The model returned an empty response."
        )

    text = raw.strip()

    # Remove Markdown code fences.
    fenced = re.match(
        r"^```[a-zA-Z]*\s*\n?(.*?)\n?```\s*$",
        text,
        flags=re.DOTALL,
    )

    if fenced:
        text = fenced.group(1).strip()

    # First attempt: parse the complete response.
    try:

        parsed = json.loads(text)

        if isinstance(parsed, dict):
            return parsed

        raise ExtractionError(
            "The model response was not a JSON object."
        )

    except json.JSONDecodeError:
        pass

    # Second attempt: find a JSON object inside extra text.
    decoder = json.JSONDecoder()

    for index, char in enumerate(text):

        if char != "{":
            continue

        try:

            parsed, _ = decoder.raw_decode(
                text[index:]
            )

        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict):
            return parsed

    raise ExtractionError(
        "The model did not return a valid JSON object."
    )


def extract_profile(cv_text: str) -> ExtractedProfile:
    """
    Extract and validate a structured profile from CV text.

    Pipeline:
        Raw CV text
            ↓
        Prepare prompt
            ↓
        Shared LLM client
            ↓
        JSON parsing
            ↓
        Pydantic validation
            ↓
        ExtractedProfile

    Raises:
        EmptyCVError
        ExternalAPIError
        ExtractionError
    """

    # 1. Validate input text.
    text = (cv_text or "").strip()

    if not text:

        raise EmptyCVError(
            "No readable text was extracted from the CV."
        )

    # 2. Limit input length.
    if len(text) > MAX_CV_CHARS:

        logger.warning(
            "CV text truncated from %d to %d characters",
            len(text),
            MAX_CV_CHARS,
        )

        text = text[:MAX_CV_CHARS]

    # 3. Prepare CV content.
    # Remove our closing/opening delimiters from the input.
    text = (
        text.replace("</cv_text>", "")
        .replace("<cv_text>", "")
    )

    user_prompt = (
        "<cv_text>\n"
        f"{text}\n"
        "</cv_text>"
    )

    # 4. Prepare LLM request options.
    options = {
        "max_tokens": MAX_OUTPUT_TOKENS,
    }

    if USE_JSON_MODE:

        options["response_format"] = {
            "type": "json_object"
        }

    last_error = None

    # 5. Call LLM and validate response.
    for attempt in range(1, MAX_ATTEMPTS + 1):

        try:

            raw = complete(
                CV_EXTRACTION_SYSTEM_PROMPT,
                user_prompt,
                **options,
            )

        except Exception as exc:

            logger.exception(
                "LLM call failed during CV extraction"
            )

            raise ExternalAPIError(
                "The AI service failed to process the CV. "
                "Please try again."
            ) from exc

        try:

            extracted_data = parse_json_response(raw)

            validated_profile = validate_extracted(
                extracted_data
            )

            return validated_profile

        except ExtractionError as exc:

            last_error = exc

            logger.warning(
                "CV extraction attempt %d/%d failed: %s",
                attempt,
                MAX_ATTEMPTS,
                exc,
            )

    # 6. All attempts failed.
    raise ExtractionError(
        "The CV could not be converted into a valid profile. "
        "Please try again."
    ) from last_error
