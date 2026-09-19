"""HTTP endpoint for resume/cover-letter tailoring ONLY."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.common.dependencies import get_current_user
from app.tailoring.service import tailor_application

router = APIRouter()


class TailorRequest(BaseModel):
    application_id: int
    job_description: str


@router.post("/generate")
def generate(payload: TailorRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    application = tailor_application(db, user.id, payload.application_id, payload.job_description)
    return {"cover_letter": application.cover_letter_text}
