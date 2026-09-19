"""
Shared prompt fragments (tone/style rules, JSON-output instructions) reused
across multiple feature-specific prompts.py files, so tone stays consistent
without copy-pasting the same instructions everywhere.
"""

JSON_ONLY_INSTRUCTION = (
    "Respond with ONLY valid JSON. No preamble, no markdown code fences, no explanation."
)

GROUNDING_RULE = (
    "Use ONLY facts explicitly present in the provided context. "
    "Never invent employers, dates, skills, or achievements not present in the source material."
)
