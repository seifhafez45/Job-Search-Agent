"""CRUD for application tracking. Plain DB logic, no AI. Reminder logic lives in reminders.py."""
from sqlalchemy.orm import Session

from app.models.application import Application
from app.schemas.application import ApplicationCreate, ApplicationUpdate


def create_application(db: Session, user_id: int, payload: ApplicationCreate) -> Application:
    application = Application(user_id=user_id, **payload.dict())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def list_applications(db: Session, user_id: int) -> list[Application]:
    return db.query(Application).filter(Application.user_id == user_id).all()


def update_application(db: Session, user_id: int, application_id: int, payload: ApplicationUpdate) -> Application:
    application = db.query(Application).filter(
        Application.id == application_id, Application.user_id == user_id
    ).first()
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(application, field, value)
    db.commit()
    db.refresh(application)
    return application
