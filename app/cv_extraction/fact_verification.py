import json

from extraction import client


ALLOWED_STATUSES = {
    "supported",
    "needs_review",
    "not_found",
}

BATCH_SIZE = 4


def get_profile_claims(profile):
    """Convert the extracted profile into individual claims."""

    claims = []

    for field, value in profile.items():

        if value is None or value == "":
            continue

        if isinstance(value, list):
            for item in value:
                if isinstance(item, str) and item.strip():
                    claims.append({
                        "field": field,
                        "claim": item.strip(),
                    })

        elif isinstance(value, str) and value.strip():
            claims.append({
                "field": field,
                "claim": value.strip(),
            })

    return claims


def verify_batch(cv_text, claims):
    """Verify a small batch of claims against the original CV."""

    prompt = f"""
Verify the following CV claims using only the original CV text.

CV TEXT:
<cv_text>
{cv_text}
</cv_text>

CLAIMS TO VERIFY:
{json.dumps(claims, ensure_ascii=False)}

For every claim, return:
- field
- claim
- status: supported, needs_review, or not_found
- evidence: exact quote from the CV, or null
- reason: a short explanation

Rules:
1. Do not invent facts or evidence.
2. Keep every claim unchanged.
3. Use supported only when the CV clearly supports the claim.
4. Use needs_review for partial or ambiguous evidence.
5. Use not_found when no supporting evidence exists.
6. Return one valid JSON object only.
7. Include every input claim exactly once.

Required format:
{{
  "results": [
    {{
      "field": "skills",
      "claim": "Python",
      "status": "supported",
      "evidence": "Python",
      "reason": "Explicitly mentioned in the CV."
    }}
  ]
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
        max_tokens=2000,
    )

    message = response.choices[0].message
    result = message.content

    if not result or not result.strip():
        raise ValueError(
            "The verification model returned an empty response. "
            f"Finish reason: {response.choices[0].finish_reason}"
        )

    result = result.strip()

    if result.startswith("```"):
        lines = result.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        result = "\n".join(lines).strip()

        if result.lower().startswith("json"):
            result = result[4:].strip()

    try:
        verification = json.loads(result)

    except json.JSONDecodeError as error:
        raise ValueError(
            "The verification model returned invalid JSON."
        ) from error

    if not isinstance(verification, dict):
        raise ValueError(
            "The verification response must be a JSON object."
        )

    results = verification.get("results")

    if not isinstance(results, list):
        raise ValueError(
            "The verification response must contain a results list."
        )

    return results


def verify_profile_facts(cv_text, profile):
    """
    Verify extracted CV claims in small batches and check evidence quotes.
    """

    if not cv_text or not cv_text.strip():
        raise ValueError("The original CV text is empty.")

    claims = get_profile_claims(profile)

    if not claims:
        return {"results": []}

    original_text = " ".join(cv_text.split()).casefold()

    checked_results = []

    for start in range(0, len(claims), BATCH_SIZE):

        batch = claims[start:start + BATCH_SIZE]

        try:
            results = verify_batch(cv_text, batch)

        except Exception as error:
            # Preserve the other batches if one batch fails.
            for claim_data in batch:
                checked_results.append({
                    **claim_data,
                    "status": "needs_review",
                    "evidence": None,
                    "reason": (
                        "Automatic verification failed: "
                        f"{str(error)}"
                    ),
                    "evidence_check": "not_checked",
                })

            continue

        returned_claims = {
            (item.get("field"), item.get("claim")): item
            for item in results
            if isinstance(item, dict)
        }

        for claim_data in batch:

            key = (
                claim_data["field"],
                claim_data["claim"],
            )

            item = returned_claims.get(key)

            if item is None:
                checked_results.append({
                    **claim_data,
                    "status": "needs_review",
                    "evidence": None,
                    "reason": "The model did not return this claim.",
                    "evidence_check": "not_checked",
                })
                continue

            status = item.get("status")

            if status not in ALLOWED_STATUSES:
                status = "needs_review"

            evidence = item.get("evidence")

            if status == "supported":

                if not isinstance(evidence, str) or not evidence.strip():
                    status = "needs_review"
                    evidence_check = "missing_evidence"

                else:
                    normalized_evidence = " ".join(
                        evidence.split()
                    ).casefold()

                    if normalized_evidence in original_text:
                        evidence_check = "quote_found"
                    else:
                        status = "needs_review"
                        evidence_check = "quote_not_found"

            else:
                evidence_check = "not_applicable"

            checked_results.append({
                "field": claim_data["field"],
                "claim": claim_data["claim"],
                "status": status,
                "evidence": evidence,
                "reason": item.get("reason", ""),
                "evidence_check": evidence_check,
            })

    return {
        "results": checked_results
    }