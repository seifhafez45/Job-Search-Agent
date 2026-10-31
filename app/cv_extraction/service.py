from sqlalchemy.orm import Session

from app.common.exceptions import ExtractionError
from app.models.profile import (
    Profile,
    WorkExperience,
    Education,
    Skill,
)
from app.storage.resume_storage import save_resume_file

from app.cv_extraction.parser import extract_text
from app.cv_extraction.extraction import extract_profile
from app.cv_extraction.validation import validate_profile


def process_resume_upload(
    db: Session,
    user_id: int,
    filename: str,
    content: bytes,
) -> Profile:

    # 1. Extract raw text from the uploaded file
    try:
        raw_text = extract_text(content, filename)

    except Exception as e:
        raise ExtractionError(f"CV parsing failed: {e}")

    # 2. Extract structured data using the LLM
    extracted_data = extract_profile(raw_text)

    # 3. Validate extracted data using Pydantic
    data, errors = validate_profile(extracted_data)

    if errors:
        raise ExtractionError(
            f"CV validation failed: {errors}"
        )

    # 4. Save the original resume file
    try:
        file_path = save_resume_file(
            user_id,
            filename,
            content,
        )

    except Exception as e:
        raise ExtractionError(
            f"Could not save resume file: {e}"
        )

    # 5. Get existing profile or create a new one
    profile = (
        db.query(Profile)
        .filter(Profile.user_id == user_id)
        .first()
    )

    if profile is None:
        profile = Profile(user_id=user_id)

    # 6. Update main profile information
    profile.full_name = data["full_name"]
    profile.headline = data["headline"]
    profile.summary = data["summary"]
    profile.location = data["location"]

    profile.resume_file_path = file_path
    profile.raw_resume_text = raw_text

    # 7. Update related database records
    profile.experiences = [
        WorkExperience(**item)
        for item in data["experiences"]
    ]

    profile.education = [
        Education(**item)
        for item in data["education"]
    ]

    profile.skills = [
        Skill(**item)
        for item in data["skills"]
    ]

    # 8. Save changes to database
    try:
        db.add(profile)
        db.commit()
        db.refresh(profile)

    except Exception:
        db.rollback()
        raise

    return profile
