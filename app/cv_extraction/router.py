"""HTTP endpoint for resume upload ONLY. Delegates all logic to service.py."""
from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.common.dependencies import get_current_user
from app.schemas.profile import ProfileOut
from app.cv_extraction.service import process_resume_upload

router = APIRouter()


@router.post("/upload", response_model=ProfileOut)
async def upload_resume(file: UploadFile, db: Session = Depends(get_db), user=Depends(get_current_user)):
    content = await file.read()
    profile = process_resume_upload(db, user.id, file.filename, content)
    return ProfileOut.from_orm(profile)
