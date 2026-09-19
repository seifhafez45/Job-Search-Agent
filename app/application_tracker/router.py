"""HTTP endpoints for the application tracker ONLY."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.common.dependencies import get_current_user
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationOut
from app.application_tracker.service import create_application, list_applications, update_application
from app.application_tracker.reminders import find_stale_applications

router = APIRouter()


@router.post("/", response_model=ApplicationOut)
def create(payload: ApplicationCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return create_application(db, user.id, payload)


@router.get("/", response_model=list[ApplicationOut])
def list_all(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return list_applications(db, user.id)


@router.patch("/{application_id}", response_model=ApplicationOut)
def update(application_id: int, payload: ApplicationUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return update_application(db, user.id, application_id, payload)


@router.get("/stale", response_model=list[ApplicationOut])
def stale(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return find_stale_applications(list_applications(db, user.id))
