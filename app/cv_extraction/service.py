"""
Orchestrates Phase 2: file -> text (parser.py) -> validated profile (extraction.py)
-> Profile rows (DB). Coordinates only; parsing, LLM calls and validation live in
their own modules.

Order matters: everything that can fail cheaply (parsing, LLM, validation) runs
BEFORE anything is written, so a bad upload never leaves orphan files or touches
the user's existing profile.
"""
import logging
from pathlib import Path

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cv_extraction.errors import ProfileConflictError
from app.cv_extraction.extraction import extract_profile
from app.cv_extraction.parser import extract_text
from app.models.profile import Education, Profile, Skill, WorkExperience
from app.storage.resume_storage import save_resume_file

logger = logging.getLogger(__name__)


def process_resume_upload(db: Session, user_id: int, filename: str, content: bytes) -> Profile:
    # 1. Cheap, side-effect-free steps first.
    raw_text = extract_text(content, filename)       # parser.py
    extracted = extract_profile(raw_text)            # extraction.py (LLM + validation)

    # 2. Only now write the file to storage.
    new_path = save_resume_file(user_id, filename, content)

    old_path = None
    try:
        # One profile per user (also enforced by unique(user_id)).
        profile = (
            db.query(Profile)
            .filter(Profile.user_id == user_id)
            .with_for_update()
            .first()
        )
        if profile is None:
            profile = Profile(user_id=user_id)
        old_path = profile.resume_file_path

        profile.full_name = extracted.full_name
        profile.headline = extracted.headline
        profile.summary = extracted.summary
        profile.location = extracted.location
        profile.resume_file_path = new_path
        profile.raw_resume_text = raw_text

        # delete-orphan cascade removes the previous rows when the lists are replaced.
        profile.experiences = [WorkExperience(**e.model_dump()) for e in extracted.experiences]
        profile.education = [Education(**e.model_dump()) for e in extracted.education]
        profile.skills = [Skill(**s.model_dump()) for s in extracted.skills]

        db.add(profile)
        db.commit()
    except IntegrityError as exc:
        # Two simultaneous first uploads for the same user.
        db.rollback()
        _delete_file_quietly(new_path)
        raise ProfileConflictError("A profile upload is already in progress for this user.") from exc
    except Exception:
        db.rollback()
        _delete_file_quietly(new_path)
        raise

    # 3. Committed: the previous resume file is no longer referenced.
    if old_path and old_path != new_path:
        _delete_file_quietly(old_path)

    db.refresh(profile)
    return profile


def _delete_file_quietly(path: str | None) -> None:
    """Best-effort cleanup; a leftover file must never turn into an API error."""
    if not path:
        return
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        logger.warning("Could not delete resume file %s", path)
