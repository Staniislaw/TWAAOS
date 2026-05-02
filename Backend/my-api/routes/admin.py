from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from database import models
from auth.dependencies import get_current_user
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import func, extract

router = APIRouter(prefix="/admin", tags=["Admin"])

def require_admin(user=Depends(get_current_user)):
    print("USER PAYLOAD:", user)  # ← adaugă asta
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acces restricționat!")
    return user

# ============ USERI ============

@router.get("/users")
def get_all_users(db: Session = Depends(get_db), user=Depends(require_admin)):
    users = db.query(models.User).all()
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": str(u.created_at),
            "oauth_provider": u.oauth_provider,
        }
        for u in users
    ]

@router.put("/users/{user_id}/role")
def update_user_role(user_id: int, body: dict, db: Session = Depends(get_db), user=Depends(require_admin)):
    new_role = body.get("role")
    if new_role not in ["student", "organizer", "admin"]:
        raise HTTPException(status_code=400, detail="Rol invalid!")

    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Userul nu există!")

    db_user.role = new_role
    db.commit()
    return {"message": f"Rol actualizat la {new_role}!", "user_id": user_id}

@router.put("/users/{user_id}/toggle-active")
def toggle_user_active(user_id: int, db: Session = Depends(get_db), user=Depends(require_admin)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Userul nu există!")

    db_user.is_active = not db_user.is_active
    db.commit()
    return {"message": "Status actualizat!", "is_active": db_user.is_active}

# ============ EVENIMENTE ============

class EventDecision(BaseModel):
    action: str  # "approve" sau "reject"
    rejection_reason: Optional[str] = None

@router.get("/events/pending")
def get_pending_events(db: Session = Depends(get_db), user=Depends(require_admin)):
    events = db.query(models.Event).filter(models.Event.status == "pending").all()
    return [
        {
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
            "created_at": str(e.created_at),
            "organizer_name": e.organizer.full_name if e.organizer else "Necunoscut",
            "organizer_id": e.organizer_id,
        }
        for e in events
    ]

@router.put("/events/{event_id}/decision")
def decide_event(event_id: int, decision: EventDecision, db: Session = Depends(get_db), user=Depends(require_admin)):
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
    return {"message": f"Eveniment {'aprobat' if decision.action == 'approve' else 'respins'}!"}

# routes/admin.py

@router.get("/events/rejected")
def get_rejected_events(db: Session = Depends(get_db), user=Depends(require_admin)):
    events = db.query(models.Event).filter(models.Event.status == "rejected").all()
    return [
        {
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
            "rejection_reason": e.rejection_reason,
            "created_at": str(e.created_at),
            "organizer_name": e.organizer.full_name if e.organizer else "Necunoscut",
            "organizer_id": e.organizer_id,
        }
        for e in events
    ]
@router.get("/reports")
def get_reports(db: Session = Depends(get_db), user=Depends(require_admin)):

    # 1. Evenimente pe lună (ultimele 12 luni)
    events_per_month = db.query(
        extract('year', models.Event.created_at).label('year'),
        extract('month', models.Event.created_at).label('month'),
        func.count(models.Event.id).label('count')
    ).group_by('year', 'month').order_by('year', 'month').all()

    # 2. Participare medie per eveniment
    avg_participation = db.query(
        func.avg(
            db.query(func.count(models.EventRegistration.id))
            .filter(models.EventRegistration.event_id == models.Event.id)
            .filter(models.EventRegistration.status == 'registered')
            .correlate(models.Event)
            .scalar_subquery()
        )
    ).scalar()

    # 3. Evenimente per organizator
    events_per_organizer = db.query(
        models.User.full_name,
        models.User.email,
        func.count(models.Event.id).label('count')
    ).join(models.Event, models.Event.organizer_id == models.User.id)\
     .group_by(models.User.id)\
     .order_by(func.count(models.Event.id).desc())\
     .all()

    # 4. Statistici generale
    total_events = db.query(func.count(models.Event.id)).scalar()
    total_users = db.query(func.count(models.User.id)).scalar()
    total_registrations = db.query(func.count(models.EventRegistration.id)).scalar()
    total_feedback = db.query(func.count(models.EventFeedback.id)).scalar()
    avg_rating = db.query(func.avg(models.EventFeedback.rating)).scalar()

    # 5. Evenimente pe categorie
    events_per_category = db.query(
        models.Event.category,
        func.count(models.Event.id).label('count')
    ).group_by(models.Event.category).all()

    # 6. Evenimente pe status
    events_per_status = db.query(
        models.Event.status,
        func.count(models.Event.id).label('count')
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
        ]
    }