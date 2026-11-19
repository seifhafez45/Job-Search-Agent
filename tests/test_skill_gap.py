import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app import models  # noqa: F401 - register all mapped models
from app.skill_gap import service


def test_analyze_skill_gap_persists_score_and_skill_lists(monkeypatch):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    monkeypatch.setattr(
        service,
        "compare_profile_to_job",
        lambda *args, **kwargs: {
            "match_score": 82,
            "matched_skills": ["Python"],
            "missing_skills": ["Kubernetes"],
            "fit_summary": "Strong backend experience.",
        },
    )

    with Session(engine) as db:
        report = service.analyze_skill_gap(
            db,
            user_id=7,
            job_title="Backend Engineer",
            job_description="Build APIs with Python and Kubernetes.",
        )

        saved = db.get(service.SkillGapReport, report.id)
        assert saved is not None
        assert saved.match_score == 82
        assert json.loads(saved.matched_skills) == ["Python"]
        assert json.loads(saved.missing_skills) == ["Kubernetes"]
        assert saved.fit_summary == "Strong backend experience."


def test_compare_profile_to_jobs_parses_results_and_clamps_score(monkeypatch):
    class Profile:
        def model_dump_json(self):
            return '{"skills":["Python"]}'

    class Memory:
        profile = Profile()

    class Job:
        external_id = "job-1"
        title = "Backend Engineer"
        description = "  Build\nPython APIs  "

    monkeypatch.setattr(
        service,
        "complete",
        lambda *args, **kwargs: json.dumps(
            {
                "results": [
                    {
                        "external_id": "job-1",
                        "match_score": 140,
                        "matched_skills": ["Python"],
                        "missing_skills": [],
                        "fit_summary": "Good fit.",
                    }
                ]
            }
        ),
    )

    result = service.compare_profile_to_jobs(Memory(), [Job()])

    assert result["job-1"]["match_score"] == 100
    assert result["job-1"]["matched_skills"] == ["Python"]
    assert result["job-1"]["missing_skills"] == []
