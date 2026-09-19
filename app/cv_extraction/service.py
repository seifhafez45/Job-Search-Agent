"""
Orchestrates Phase 2: file -> text (parser.py) -> structured JSON (LLM) -> Profile rows (DB)
-> memory refresh. This is the module every other feature depends on transitively.
"""
import json

from sqlalchemy.orm import Session

from app.common.exceptions import ExtractionError
from app.llm.client import complete
from app.models.profile import Profile, WorkExperience, Education, Skill
from app.storage.resume_storage import save_resume_file
from app.cv_extraction.parser import extract_text
from app.cv_extraction.prompts import CV_EXTRACTION_SYSTEM_PROMPT


def process_resume_upload(db: Session, user_id: int, filename: str, content: bytes) -> Profile:
    file_path = save_resume_file(user_id, filename, content)
    raw_text = extract_text(content, filename)

    raw_json = complete(CV_EXTRACTION_SYSTEM_PROMPT, raw_text)
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise ExtractionError(f"LLM did not return valid JSON: {e}")

    profile = db.query(Profile).filter(Profile.user_id == user_id).first() or Profile(user_id=user_id)
    profile.full_name = data.get("full_name")
    profile.headline = data.get("headline")
    profile.summary = data.get("summary")
    profile.location = data.get("location")
    profile.resume_file_path = file_path
    profile.raw_resume_text = raw_text
    profile.experiences = [WorkExperience(**e) for e in data.get("experiences", [])]
    profile.education = [Education(**e) for e in data.get("education", [])]
    profile.skills = [Skill(**s) for s in data.get("skills", [])]

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
