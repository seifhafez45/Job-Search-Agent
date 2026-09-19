"""
Shared FastAPI dependencies used by MULTIPLE routers (e.g. get_current_user).
Feature-specific dependencies stay inside that feature's own module.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.service import decode_access_token
from app.models.user import User


def get_current_user(token: str, db: Session = Depends(get_db)) -> User:
    """Validates JWT, returns the User row. Raises 401 if invalid/expired."""
    user_id = decode_access_token(token)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user
