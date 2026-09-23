"""
Shared test fixtures. mock_llm patches app.llm.client.complete so tests never
hit the real Anthropic API — set .return_value (a string) or .side_effect
(e.g. a list of strings for successive calls) on it per-test. db_session gives
an isolated in-memory SQLite session with all models' tables created.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # noqa: F401 — registers every table on Base.metadata


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_llm(monkeypatch):
    calls = []

    class _MockComplete:
        return_value = "{}"
        side_effect = None

        def __call__(self, system_prompt, user_prompt, max_tokens=1500):
            calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
            if self.side_effect is not None:
                if isinstance(self.side_effect, list):
                    return self.side_effect[len(calls) - 1]
                return self.side_effect(system_prompt, user_prompt)
            return self.return_value

    mock = _MockComplete()
    mock.calls = calls
    monkeypatch.setattr("app.llm.client.complete", mock)
    monkeypatch.setattr("app.interview_agent.planner.complete", mock)
    monkeypatch.setattr("app.interview_agent.tools.complete", mock)
    monkeypatch.setattr("app.interview_agent.scorer.complete", mock)
    try:
        # career_rag.service pulls in sentence_transformers (heavy ML dep) via
        # its embedder import chain; skip patching it when that's not installed
        # so agent-only tests don't need career_rag's dependencies at all.
        monkeypatch.setattr("app.career_rag.service.complete", mock)
    except (ImportError, ModuleNotFoundError):
        pass
    return mock
