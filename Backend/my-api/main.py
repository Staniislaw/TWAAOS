from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from auth.jwt_handler import create_access_token
from auth.google_auth import get_google_auth_url, get_google_token, get_google_user
from routes import protected,users,events
from pydantic import BaseModel
from database.database import engine, SessionLocal
from database import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Lab03 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(protected.router)
app.include_router(users.router)
app.include_router(events.router)



class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/")
def root():
    return {"message": "API functional!"}

@app.post("/token")
def login(data: LoginRequest):
    if data.username == "admin" and data.password == "admin123":
        token = create_access_token({"sub": data.username})
        return {"access_token": token, "token_type": "bearer"}
    return {"error": "Credentiale incorecte"}

@app.get("/auth/google")
def google_login():
    url = get_google_auth_url()
    return RedirectResponse(url)

@app.get("/auth/callback")
async def google_callback(code: str):
    token_data = await get_google_token(code)
    access_token_google = token_data.get("access_token")
    user_info = await get_google_user(access_token_google)

    db = SessionLocal()
    try:
        user = db.query(models.User).filter(
            models.User.email == user_info.get("email")
        ).first()

        if not user:
            user = models.User(
                full_name=user_info.get("name"),
                email=user_info.get("email"),
                oauth_provider="google",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    finally:
        db.close()

    jwt_token = create_access_token({
        "sub": user_info.get("email"),
        "user_id": user.id,
        "name": user_info.get("name"),
        "picture": user_info.get("picture")
    })

    # Folosim 303 See Other in loc de 307
    frontend_url = f"http://localhost:4200/auth/callback?token={jwt_token}&name={user_info.get('name')}&email={user_info.get('email')}"
    return RedirectResponse(url=frontend_url, status_code=303)