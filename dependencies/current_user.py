from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from dependencies.auth_guard import get_current_user_from_token
from models.user import AppUser


def get_current_active_user(
    token_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
) -> AppUser:
    user = db.query(AppUser).filter(AppUser.id_user == token_user["user_id"]).first()

    if user is None or user.email != token_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.credential is None or not user.credential.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
