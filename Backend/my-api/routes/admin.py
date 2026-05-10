from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from pydantic import BaseModel
from database.database import get_db
from database import models
from auth.dependencies import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])

DbSession = Annotated[Session, Depends(get_db)]

def require_admin(user: Annotated[dict, Depends(get_current_user)]) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acces restricționat!")
    return user

AdminUser = Annotated[dict, Depends(require_admin)]

class UpdateRoleBody(BaseModel):
    role: str

class EventDecision(BaseModel):
    action: str
    rejection_reason: Optional[str] = None

def serialize_user(u: models.User) -> dict:
    return {
        "id": u.id,
        "full_name": u.full_name,
        "email": u.email,
        "role": u.role,
        "is_active": u.is_active,
        "created_at": str(u.created_at),
        "oauth_provider": u.oauth_provider,
    }

def serialize_event(e: models.Event) -> dict:
    return {
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "category": e.category,
        "faculty": e.faculty,
        "start_datetime": str(e.start_datetime),
        "end_datetime": str(e.end_datetime) if e.end_datetime else None,
        "location": e.location,
        "participation_mode": e.participation_mode,
        "entry_type": e.entry_type,
        "max_participants": e.max_participants,
        "status": e.status,
        "rejection_reason": getattr(e, "rejection_reason", None),
        "created_at": str(e.created_at),
        "organizer_name": e.organizer.full_name if e.organizer else "Necunoscut",
        "organizer_id": e.organizer_id,
    }

# ============ USERI ============

@router.get("/users")
def get_all_users(db: DbSession, user: AdminUser) -> list[dict]:
    return [serialize_user(u) for u in db.query(models.User).all()]

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    body: UpdateRoleBody,
    db: DbSession,
    user: AdminUser,
) -> dict:
    valid_roles = {"student", "organizer", "admin"}
    if body.role not in valid_roles:
        raise HTTPException(status_code=400, detail="Rol invalid!")

    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Userul nu există!")

    db_user.role = body.role
    db.commit()
    return {"message": f"Rol actualizat la {body.role}!", "user_id": user_id}

@router.put("/users/{user_id}/toggle-active")
def toggle_user_active(user_id: int, db: DbSession, user: AdminUser) -> dict:
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Userul nu există!")

    db_user.is_active = not db_user.is_active
    db.commit()
    return {"message": "Status actualizat!", "is_active": db_user.is_active}

# ============ EVENIMENTE ============

VALID_STATUSES = {"pending", "active", "rejected"}

@router.get("/events/pending")
def get_pending_events(db: DbSession, user: AdminUser) -> list[dict]:
    events = db.query(models.Event).filter(models.Event.status == "pending").all()
    return [serialize_event(e) for e in events]

@router.get("/events/rejected")
def get_rejected_events(db: DbSession, user: AdminUser) -> list[dict]:
    events = db.query(models.Event).filter(models.Event.status == "rejected").all()
    return [serialize_event(e) for e in events]

@router.put("/events/{event_id}/decision")
def decide_event(
    event_id: int,
    decision: EventDecision,
    db: DbSession,
    user: AdminUser,
) -> dict:
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu există!")

    if decision.action == "approve":
        event.status = "active"
        event.rejection_reason = None
    elif decision.action == "reject":
        if not decision.rejection_reason:
            raise HTTPException(status_code=400, detail="Motivul respingerii e obligatoriu!")
        event.status = "rejected"
        event.rejection_reason = decision.rejection_reason
    else:
        raise HTTPException(status_code=400, detail="Acțiune invalidă!")

    db.commit()
    label = "aprobat" if decision.action == "approve" else "respins"
    return {"message": f"Eveniment {label}!"}

# ============ RAPOARTE ============

@router.get("/reports")
def get_reports(db: DbSession, user: AdminUser) -> dict:
    events_per_month = db.query(
        extract("year", models.Event.created_at).label("year"),
        extract("month", models.Event.created_at).label("month"),
        func.count(models.Event.id).label("count"),
    ).group_by("year", "month").order_by("year", "month").all()

    avg_participation = db.query(
        func.avg(
            db.query(func.count(models.EventRegistration.id))
            .filter(models.EventRegistration.event_id == models.Event.id)
            .filter(models.EventRegistration.status == "registered")
            .correlate(models.Event)
            .scalar_subquery()
        )
    ).scalar()

    events_per_organizer = (
        db.query(
            models.User.full_name,
            models.User.email,
            func.count(models.Event.id).label("count"),
        )
        .join(models.Event, models.Event.organizer_id == models.User.id)
        .group_by(models.User.id)
        .order_by(func.count(models.Event.id).desc())
        .all()
    )

    total_events        = db.query(func.count(models.Event.id)).scalar()
    total_users         = db.query(func.count(models.User.id)).scalar()
    total_registrations = db.query(func.count(models.EventRegistration.id)).scalar()
    total_feedback      = db.query(func.count(models.EventFeedback.id)).scalar()
    avg_rating          = db.query(func.avg(models.EventFeedback.rating)).scalar()

    events_per_category = db.query(
        models.Event.category,
        func.count(models.Event.id).label("count"),
    ).group_by(models.Event.category).all()

    events_per_status = db.query(
        models.Event.status,
        func.count(models.Event.id).label("count"),
    ).group_by(models.Event.status).all()

    return {
        "general": {
            "total_events": total_events,
            "total_users": total_users,
            "total_registrations": total_registrations,
            "total_feedback": total_feedback,
            "avg_rating": round(float(avg_rating), 2) if avg_rating else 0,
            "avg_participation": round(float(avg_participation), 1) if avg_participation else 0,
        },
        "events_per_month": [
            {"year": int(r.year), "month": int(r.month), "count": r.count}
            for r in events_per_month
        ],
        "events_per_organizer": [
            {"name": r.full_name or "Necunoscut", "email": r.email, "count": r.count}
            for r in events_per_organizer
        ],
        "events_per_category": [
            {"category": r.category or "Necunoscută", "count": r.count}
            for r in events_per_category
        ],
        "events_per_status": [
            {"status": r.status, "count": r.count}
            for r in events_per_status
        ],
    }