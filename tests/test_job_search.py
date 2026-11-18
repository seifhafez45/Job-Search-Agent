from app.job_search.filters import dedupe, _looks_remote
from app.schemas.job import JobPosting  # عدّل المسار


def make_job(title="Dev", company="Acme", description="", **kw):
    return JobPosting(
        external_id=kw.get("external_id", "1"),
        title=title,
        company=company,
        location="UK",
        remote=False,
        url="https://example.com",
        description=description,
        posted_date="2026-10-08T00:00:00Z",
    )


def test_dedupe_same_job_different_company_spelling():
    desc = "Machine Learning Engineer remote role at an AI startup"
    jobs = [
        make_job("ML Engineer", "Ocho People", desc, external_id="1"),
        make_job("ML Engineer", "Ocho", desc, external_id="2"),
    ]
    assert len(dedupe(jobs)) == 1


def test_dedupe_keeps_different_jobs():
    jobs = [
        make_job("Backend Dev", "A", "python backend"),
        make_job("Data Scientist", "A", "python data"),
    ]
    assert len(dedupe(jobs)) == 2


def test_remote_detected():
    assert _looks_remote(make_job(description="Fully remote UK role")) is True


def test_hybrid_is_not_remote():
    job = make_job(description="Belfast Hybrid, 3 days per week in the office, remote tools")
    assert _looks_remote(job) is False


def test_search_matches_returns_and_persists_scored_jobs(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app import models  # noqa: F401 - register all mapped models
    from app.database import Base
    from app.job_search import router
    from app.job_search.filters import JobMatchFilters
    from app.models.job_match import JobMatch
    from app.models.profile import Profile
    from app.models.user import User

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    monkeypatch.setattr(router, "get_user_memory", lambda db, user_id: object())
    monkeypatch.setattr(router, "search_jobs", lambda filters: [
        make_job("AI Engineer", description="Python and machine learning", external_id="42")
    ])
    monkeypatch.setattr(
        router,
        "compare_profile_to_jobs",
        lambda memory, jobs: {
            "42": {
                "match_score": 91,
                "matched_skills": ["Python"],
                "missing_skills": ["Kubernetes"],
                "fit_summary": "Strong fit.",
            }
        },
    )

    with Session(engine) as db:
        user = User(email="match@example.com", hashed_password="unused")
        db.add(user)
        db.commit()
        profile = Profile(user_id=user.id, resume_file_path="cv.pdf", headline="AI Engineer")
        db.add(profile)
        db.commit()

        results = router.search_matches(
            filters=JobMatchFilters(keyword="AI Engineer"),
            db=db,
            user=user,
        )

        saved = db.query(JobMatch).filter_by(user_id=user.id).one()
        assert len(results) == 1
        assert results[0].match_score == 91
        assert results[0].match_record_id == saved.id
        assert saved.match_score == 91
        assert saved.title == "AI Engineer"
