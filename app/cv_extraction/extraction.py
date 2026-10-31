import json

from app.llm.client import complete
from app.common.exceptions import ExtractionError
from app.cv_extraction.prompts import CV_EXTRACTION_SYSTEM_PROMPT


def parse_json_response(result: str) -> dict:
    """Safely parse JSON from the LLM response."""

    if not result or not result.strip():
        raise ExtractionError("The model returned an empty response.")

    result = result.strip()

    # Remove Markdown code fences
    if result.startswith("```"):
        lines = result.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        result = "\n".join(lines).strip()

        if result.lower().startswith("json"):
            result = result[4:].strip()

    # Try parsing the complete response
    try:
        data = json.loads(result)

        if isinstance(data, dict):
            return data

    except json.JSONDecodeError:
        pass

    # Try extracting JSON if extra text exists
    decoder = json.JSONDecoder()

    for index, character in enumerate(result):
        if character == "{":
            try:
                data, _ = decoder.raw_decode(result[index:])

                if isinstance(data, dict):
                    return data

            except json.JSONDecodeError:
                continue

    raise ExtractionError("The model did not return a valid JSON object.")


def extract_profile(cv_text: str) -> dict:
    """Extract structured profile information from CV text."""

    if not cv_text or not cv_text.strip():
        raise ExtractionError("No readable text was extracted from the CV.")

    try:
        response = complete(
            CV_EXTRACTION_SYSTEM_PROMPT,
            cv_text,
            max_tokens=3000,
        )

    except Exception as e:
        raise ExtractionError(f"LLM extraction failed: {e}")

    profile = parse_json_response(response)

    expected_fields = {
        "full_name": None,
        "headline": None,
        "summary": None,
        "location": None,
        "experiences": [],
        "education": [],
        "skills": [],
    }

    # Reject unexpected fields
    unexpected = set(profile) - set(expected_fields)

    if unexpected:
        raise ExtractionError(
            f"Unexpected fields returned by LLM: {unexpected}"
        )

    # Add missing fields
    for field, default in expected_fields.items():
        profile.setdefault(field, default)

    return profile
