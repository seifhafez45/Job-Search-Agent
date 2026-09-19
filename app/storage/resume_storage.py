"""
Raw file storage for uploaded resumes (PDF/DOCX). ONLY job: save/retrieve/delete
the physical file. Text extraction logic lives in cv_extraction/parser.py, not here.
Swap this module's internals for S3 later without touching any caller.
"""
import os
import uuid

from app.config import settings


def save_resume_file(user_id: int, filename: str, content: bytes) -> str:
    """Saves raw bytes to disk, returns the stored file path."""
    os.makedirs(settings.resume_storage_path, exist_ok=True)
    ext = os.path.splitext(filename)[1]
    stored_name = f"{user_id}_{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.resume_storage_path, stored_name)
    with open(path, "wb") as f:
        f.write(content)
    return path


def read_resume_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def delete_resume_file(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)
