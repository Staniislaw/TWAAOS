import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from database.database import Base, get_db
from database import models
import database.database as db_module
import routes.auth as auth_module  # ← ADAUGĂ
from main import app

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_temp.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Suprascrie SessionLocal în TOATE modulele care îl folosesc
db_module.SessionLocal = TestingSessionLocal
auth_module.SessionLocal = TestingSessionLocal  # ← ADAUGĂ

def create_test_users():
    db = TestingSessionLocal()
    try:
        # Șterge userii existenți pentru a evita conflicte
        db.query(models.User).filter(
            models.User.email.in_(["admin", "organizer@test.com"])
        ).delete(synchronize_session=False)
        db.commit()

        db.add(models.User(
            full_name="Admin Test",
            email="admin",
            password_hash=hash_password("admin123"),
            role="admin",
            is_active=True
        ))
        db.add(models.User(
            full_name="Organizer Test",
            email="organizer@test.com",
            password_hash=hash_password("org123"),
            role="organizer",
            is_active=True
        ))
        db.commit()
    finally:
        db.close()

create_test_users()

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    response = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200, f"Login failed: {response.json()}"
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def organizer_headers(client):
    response = client.post("/auth/login", json={"username": "organizer@test.com", "password": "org123"})
    assert response.status_code == 200, f"Organizer login failed: {response.json()}"
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_event_data():
    return {
        "title": "Test Event PyTest",
        "description": "Descriere test",
        "category": "academic",
        "faculty": "FIESC",
        "start_datetime": "2026-06-01T10:00:00",
        "end_datetime": "2026-06-01T12:00:00",
        "location": "Sala 101",
        "participation_mode": "In-Person",
        "entry_type": "free",
        "max_participants": 50,
        "status": "active"
    }