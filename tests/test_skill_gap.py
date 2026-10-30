"""
Tests for app/skill_gap/service.py. The LLM is mocked, so no API key or network is needed
for the calls themselves (the app still loads settings from .env on import).

Run:  python -m pytest tests/test_skill_gap.py -v
"""
import asyncio
import json
from types import SimpleNamespace

import pytest

from app.skill_gap import service
from app.skill_gap.service import SkillGapError, analyze_skill_gap

# ----------------------------------------------------------------------------
# IMPORTANT: keep this payload in sync with SkillGapResult in app/schemas/skill_gap.py.
# If the success tests fail with a ValidationError, rename/add the fields here.
# ----------------------------------------------------------------------------
VALID_RESULT = {
    "match_score": 72,
    "matched_skills": ["Python", "FastAPI"],
    "missing_skills": ["Docker", "AWS"],
    "recommendations": ["Learn Docker basics", "Deploy a small app on AWS"],
}


@pytest.fixture
def fake_request(monkeypatch):
    """analyze_skill_gap only reads req.profile and req.job, so a stub is enough."""
    monkeypatch.setattr(service, "build_user_prompt", lambda profile, job: "USER PROMPT")
    return SimpleNamespace(profile=None, job=None)


def _mock_llm(monkeypatch, replies):
    """Replace service.complete with a fake that returns `replies` one by one."""
    calls = []
    queue = list(replies)

    def fake_complete(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return queue.pop(0)

    monkeypatch.setattr(service, "complete", fake_complete)
    return calls


def _run(req):
    return asyncio.run(analyze_skill_gap(req))


# ---------------------------- _parse ----------------------------

def test_parse_plain_json():
    result = service._parse(json.dumps(VALID_RESULT))
    assert result.model_dump()["match_score"] == VALID_RESULT["match_score"]


def test_parse_strips_markdown_fences():
    raw = "```json\n" + json.dumps(VALID_RESULT) + "\n```"
    assert service._parse(raw) is not None


def test_parse_rejects_non_json():
    with pytest.raises(json.JSONDecodeError):
        service._parse("this is not json")


# ---------------------------- analyze_skill_gap ----------------------------

def test_success_on_first_attempt(monkeypatch, fake_request):
    calls = _mock_llm(monkeypatch, [json.dumps(VALID_RESULT)])
    result = _run(fake_request)
    assert result is not None
    assert len(calls) == 1


def test_retries_once_then_succeeds(monkeypatch, fake_request):
    calls = _mock_llm(monkeypatch, ["not json at all", json.dumps(VALID_RESULT)])
    result = _run(fake_request)
    assert result is not None
    assert len(calls) == 2


def test_wrong_shape_triggers_retry(monkeypatch, fake_request):
    """Valid JSON that doesn't match SkillGapResult must be retried, not crash."""
    calls = _mock_llm(monkeypatch, ["{}", json.dumps(VALID_RESULT)])
    assert _run(fake_request) is not None
    assert len(calls) == 2


def test_non_object_json_triggers_retry(monkeypatch, fake_request):
    """A JSON list used to raise TypeError and bypass the retry."""
    calls = _mock_llm(monkeypatch, ["[1, 2, 3]", json.dumps(VALID_RESULT)])
    assert _run(fake_request) is not None
    assert len(calls) == 2


def test_raises_skill_gap_error_after_all_attempts(monkeypatch, fake_request):
    calls = _mock_llm(monkeypatch, ["bad", "still bad"])
    with pytest.raises(SkillGapError):
        _run(fake_request)
    assert len(calls) == service.MAX_ATTEMPTS


# ---------------------------- regression: LLM call arguments ----------------------------

def test_llm_called_with_keyword_args_in_json_mode(monkeypatch, fake_request):
    """
    complete() takes (system_prompt, user_prompt, ...). Passing them positionally in the
    wrong order silently swapped the prompts, so we assert explicit keyword arguments.
    """
    calls = _mock_llm(monkeypatch, [json.dumps(VALID_RESULT)])
    _run(fake_request)

    kwargs = calls[0]["kwargs"]
    assert kwargs["system_prompt"] == service.SYSTEM_PROMPT
    assert kwargs["user_prompt"] == "USER PROMPT"
    assert kwargs["json_mode"] is True