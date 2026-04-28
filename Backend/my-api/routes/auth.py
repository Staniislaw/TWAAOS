from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database.database import SessionLocal
from database import models
from auth.jwt_handler import create_access_token
from passlib.context import CryptContext

router = APIRouter(prefix="/auth", tags=["Auth"])

class AuthRequest(BaseModel):
    username: str
    password: str

# 🔐 REGISTER
@router.post("/register")
def register(data: AuthRequest):
    db = SessionLocal()
    try:
        existing_user = db.query(models.User).filter(models.User.email == data.username).first()

        if existing_user:
            raise HTTPException(status_code=400, detail="User deja există")

        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

        hashed_password = pwd_context.hash(data.password)

        user = models.User(
            email=data.username,
            full_name=data.username,
            password_hash=hashed_password,
            role="organizer",
            is_active=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {"message": "User creat"}
    finally:
        db.close()


# 🔐 LOGIN
@router.post("/login")
def login(data: AuthRequest):
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == data.username).first()

        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

        if not user or not pwd_context.verify(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Credentiale incorecte")

        token = create_access_token({
            "sub": user.email,
            "user_id": user.id,
            "role": user.role
        })

        return {"access_token": token, "token_type": "bearer"}
    finally:
        db.close()