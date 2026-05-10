from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from database import models

router = APIRouter(prefix="/users", tags=["Users"])

DbSession = Annotated[Session, Depends(get_db)]

@router.get("/")
def get_users(db: DbSession) -> list[dict]:
    users = db.query(models.User).all()
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": str(u.created_at),
        }
        for u in users
    ]

@router.get("/{user_id}", responses={404: {"description": "Userul nu există"}})
def get_user(user_id: int, db: DbSession) -> dict | None:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Userul nu există!")
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": str(user.created_at),
    }