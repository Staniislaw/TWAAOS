from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database.database import get_db
from database import models
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import re
import os
import shutil
from typing import List
from DTO.SponsorsDTO import SponsorCreate

from auth.dependencies import get_current_user

from services.email_service import send_registration_email,send_promoted_from_waitlist_email,send_waitlist_email

import uuid
import qrcode
import io
import base64

router = APIRouter(prefix="/events", tags=["Events"])

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    faculty: Optional[str] = None
    start_datetime: str
    end_datetime: Optional[str] = None
    registration_deadline: Optional[str] = None
    location: Optional[str] = None
    participation_mode: Optional[str] = "In-Person"
    entry_type: Optional[str] = 'free'
    max_participants: Optional[int] = None
    status: Optional[str] = "active"
    registration_link: Optional[str] = None

class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: Optional[str]
    faculty: Optional[str]
    start_datetime: str
    end_datetime: Optional[str]
    location: Optional[str]
    participation_mode: Optional[str]
    max_participants: Optional[int]
    status: str
    created_at: str

    class Config:
        from_attributes = True

# GET all events
@router.get("/")
def get_events(db: Session = Depends(get_db)):
    events = db.query(models.Event).all()
    result = []
    for event in events:
        sentiment = get_sentiment(event.feedbacks)
        result.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "category": event.category,
            "faculty": event.faculty,
            "start_datetime": str(event.start_datetime) if event.start_datetime else None,
            "end_datetime": str(event.end_datetime) if event.end_datetime else None,
            "location": event.location,
            "participation_mode": event.participation_mode,
            "status": event.status,
            "entry_type": event.entry_type,
            "max_participants": event.max_participants,
            "registration_deadline": str(event.registration_deadline) if event.registration_deadline else None,
            "registration_link": event.registration_link,
            "created_at": str(event.created_at),
            "updated_at": str(event.updated_at),
            "organizer_id": event.organizer_id,
            "organizer_name": event.organizer.full_name if event.organizer else "Necunoscut",
            "sponsors": [
                {"name": s.name, "logo_path": s.logo_path, "website_url": s.website_url}
                for s in event.sponsors
            ],
            "sentiment": sentiment,
            "avg_rating": round(sum(f.rating for f in event.feedbacks) / len(event.feedbacks),
                                1) if event.feedbacks else None,
            "feedback_count": len(event.feedbacks),
        })
    return result

# get created events by user.
@router.get("/my/created")
def get_my_created_events(db: Session = Depends(get_db), user=Depends(get_current_user)):
    user_id = user["user_id"]
    events = db.query(models.Event).filter(models.Event.organizer_id == user_id).all()
    result = []
    for event in events:
        sentiment = get_sentiment(event.feedbacks)
        result.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "category": event.category,
            "faculty": event.faculty,
            "start_datetime": str(event.start_datetime) if event.start_datetime else None,
            "end_datetime": str(event.end_datetime) if event.end_datetime else None,
            "location": event.location,
            "participation_mode": event.participation_mode,
            "status": event.status,
            "entry_type": event.entry_type,
            "max_participants": event.max_participants,
            "registration_deadline": str(event.registration_deadline) if event.registration_deadline else None,
            "registration_link": event.registration_link,
            "created_at": str(event.created_at),
            "updated_at": str(event.updated_at),
            "organizer_id": event.organizer_id,
            "organizer_name": event.organizer.full_name if event.organizer else "Necunoscut",
            "sponsors": [
                {"name": s.name, "logo_path": s.logo_path, "website_url": s.website_url}
                for s in event.sponsors
            ],
            "sentiment": sentiment,
            "avg_rating": round(sum(f.rating for f in event.feedbacks) / len(event.feedbacks), 1) if event.feedbacks else None,
            "feedback_count": len(event.feedbacks),
        })
    return result

# GET events by ID with feedBacks sentiments
@router.get("/{event_id}")
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu a fost găsit")
    sentiment = get_sentiment(event.feedbacks)
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "category": event.category,
        "faculty": event.faculty,
        "start_datetime": str(event.start_datetime) if event.start_datetime else None,
        "end_datetime": str(event.end_datetime) if event.end_datetime else None,
        "location": event.location,
        "participation_mode": event.participation_mode,
        "status": event.status,
        "entry_type": event.entry_type,
        "max_participants": event.max_participants,
        "registration_deadline": str(event.registration_deadline) if event.registration_deadline else None,
        "registration_link": event.registration_link,
        "created_at": str(event.created_at),
        "updated_at": str(event.updated_at),
        "organizer_id": event.organizer_id,
        "organizer_name": event.organizer.full_name if event.organizer else "Necunoscut",
        "sponsors": [
            {"id": s.id, "name": s.name, "logo_path": s.logo_path, "website_url": s.website_url}
            for s in event.sponsors
        ],
        "sentiment": sentiment,
        "avg_rating": round(sum(f.rating for f in event.feedbacks) / len(event.feedbacks), 1) if event.feedbacks else None,
        "feedback_count": len(event.feedbacks),
        "materials": [
            {
                "id": m.id,
                "file_name": m.file_name,
                "file_type": m.file_type,
                "file_size_kb": m.file_size_kb,
                "file_path": m.file_path
            }
            for m in event.materials
        ]
    }

# POST new event
@router.post("/")
def create_event(event_data: EventCreate, db: Session = Depends(get_db),user=Depends(get_current_user)):
    try:
        new_event = models.Event(
            title=event_data.title,
            description=event_data.description,
            category=event_data.category,
            faculty=event_data.faculty,
            start_datetime=datetime.fromisoformat(event_data.start_datetime),
            end_datetime=datetime.fromisoformat(event_data.end_datetime) if event_data.end_datetime else None,
            registration_deadline=datetime.fromisoformat(event_data.registration_deadline) if event_data.registration_deadline else None,
            location=event_data.location,
            participation_mode=event_data.participation_mode,
            entry_type=event_data.entry_type,
            max_participants=event_data.max_participants,
            status=event_data.status,
            registration_link=event_data.registration_link,
            organizer_id=user["user_id"]  # temporar, ulterior din JWT
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return {"message": "Eveniment creat cu succes!", "id": new_event.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# PUT update event
@router.put("/{event_id}")
def update_event(event_id: int, event_data: EventCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu a fost găsit")

    # doar organizatorul sau adminul poate edita
    if event.organizer_id != user["user_id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Nu ai permisiunea să editezi acest eveniment")

    event.title = event_data.title
    event.description = event_data.description
    event.category = event_data.category
    event.faculty = event_data.faculty
    event.location = event_data.location
    event.participation_mode = event_data.participation_mode
    event.max_participants = event_data.max_participants
    event.status = event_data.status
    event.entry_type = event_data.entry_type
    event.registration_link = event_data.registration_link
    event.start_datetime = datetime.fromisoformat(
    event_data.start_datetime) if event_data.start_datetime else event.start_datetime
    event.end_datetime = datetime.fromisoformat(event_data.end_datetime) if event_data.end_datetime else None
    event.registration_deadline = datetime.fromisoformat(
    event_data.registration_deadline) if event_data.registration_deadline else None
    event.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(event)
    return {"message": "Eveniment actualizat!", "id": event.id}

# DELETE event
@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Eveniment negăsit")
    if event.organizer_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Nu ai permisiunea să ștergi acest eveniment")
    db.delete(event)
    db.commit()
    return {"message": "Eveniment șters"}



# GET materiale event
@router.get("/{event_id}/materials")
def get_event_materials(event_id: int, db: Session = Depends(get_db)):
    return db.query(models.EventMaterial).filter(
        models.EventMaterial.event_id == event_id
    ).all()

# GET feedback event
@router.get("/{event_id}/feedback")
def get_event_feedback(event_id: int, db: Session = Depends(get_db)):
    return db.query(models.EventFeedback).filter(
        models.EventFeedback.event_id == event_id
    ).all()

# GET sponsori event
@router.get("/{event_id}/sponsors")
def get_event_sponsors(event_id: int, db: Session = Depends(get_db)):
    return db.query(models.EventSponsor).filter(
        models.EventSponsor.event_id == event_id
    ).all()

# POST inregistrare la event
@router.post("/{event_id}/register")
def register_to_event(event_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    user_id = user["user_id"]  # din JWT, nu mai e hardcodat

    # 1. Verifici dacă evenimentul există
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu există")

    # 2. Verifici dacă userul e deja înregistrat
    existing = db.query(models.EventRegistration).filter(
        models.EventRegistration.event_id == event_id,
        models.EventRegistration.user_id == user_id,
        models.EventRegistration.status.in_(["registered", "waitlist"])
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ești deja înregistrat la acest eveniment!")

    # Numarare locurile ocupate (doar "registered", nu waitlist)
    registered_count = db.query(models.EventRegistration).filter(
        models.EventRegistration.event_id == event_id,
        models.EventRegistration.status == "registered"
    ).count()

    # 3. Verifici dacă mai sunt locuri
    is_full = event.max_participants and registered_count >= event.max_participants

    if is_full:
        # Calculezi poziția în waitlist
        waitlist_count = db.query(models.EventRegistration).filter(
            models.EventRegistration.event_id == event_id,
            models.EventRegistration.status == "waitlist"
        ).count()

        registration = models.EventRegistration(
            event_id=event_id,
            user_id=user_id,
            status="waitlist",
            waitlist_position=waitlist_count + 1,
            qr_code_token=None,
        )
        db.add(registration)
        db.commit()

        # Trimite email waitlist
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        send_waitlist_email(
            to_email=db_user.email,
            user_name=db_user.full_name,
            event_title=event.title,
            position=waitlist_count + 1
        )

        return {
            "message": f"Evenimentul e complet! Ești pe lista de așteptare pe poziția {waitlist_count + 1}.",
            "status": "waitlist",
            "waitlist_position": waitlist_count + 1
        }

    # 4. Generezi QR token DOAR dacă entry_type == "qr_code"
    qr_token = None
    qr_image_base64 = None

    if event.entry_type == "qr_code":
        # Generezi tokenul unic
        qr_token = str(uuid.uuid4())

        # Generezi imaginea QR
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_token)  # QR-ul conține tokenul unic
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        qr_image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # 5. Salvezi înregistrarea în DB
    registration = models.EventRegistration(
        event_id=event_id,
        user_id=user_id,
        status="registered",
        qr_code_token=qr_token,  # None dacă nu e qr_code
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)


    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    #Trimitere mail de confiramre
    send_registration_email(
        to_email=db_user.email,
        user_name=db_user.full_name,
        event_title=event.title,
        event_date=str(event.start_datetime),
        event_location=event.location or "—",
        qr_image_base64=qr_image_base64
    )
    # 6. Returnezi răspunsul
    response = {"message": "Înregistrat cu succes!", "status": "registered", "registration_id": registration.id}

    if qr_image_base64:
        response["qr_code"] = f"data:image/png;base64,{qr_image_base64}"
        response["qr_token"] = qr_token

    return response

@router.delete("/{event_id}/unregister")
def unregister_from_event(event_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    user_id = user["user_id"]

    # ← caută atât "registered" cât și "waitlist"
    registration = db.query(models.EventRegistration).filter(
        models.EventRegistration.event_id == event_id,
        models.EventRegistration.user_id == user_id,
        models.EventRegistration.status.in_(["registered", "waitlist"])
    ).first()

    if not registration:
        raise HTTPException(status_code=404, detail="Nu ești înregistrat la acest eveniment!")

    was_registered = registration.status == "registered"  # ← reține dacă era registered

    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    db.delete(registration)
    db.flush()

    # Promovezi din waitlist DOAR dacă cel care pleacă era "registered"
    # (dacă era pe waitlist, nu se eliberează un loc real)
    if was_registered:
        next_in_waitlist = db.query(models.EventRegistration).filter(
            models.EventRegistration.event_id == event_id,
            models.EventRegistration.status == "waitlist"
        ).order_by(models.EventRegistration.waitlist_position).first()

        if next_in_waitlist:
            qr_token = None
            qr_image_base64 = None

            if event.entry_type == "qr_code":
                qr_token = str(uuid.uuid4())
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(qr_token)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)
                qr_image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

            next_in_waitlist.status = "registered"
            next_in_waitlist.waitlist_position = None
            next_in_waitlist.qr_code_token = qr_token
            next_in_waitlist.registered_at = datetime.utcnow()

            db.flush()
            # Reordonezi restul din waitlist
            remaining = db.query(models.EventRegistration).filter(
                models.EventRegistration.event_id == event_id,
                models.EventRegistration.status == "waitlist"  # ← nu îl mai include pe cel promovat
            ).order_by(models.EventRegistration.waitlist_position).all()

            for i, reg in enumerate(remaining):
                reg.waitlist_position = i + 1

            db.commit()

            promoted_user = db.query(models.User).filter(
                models.User.id == next_in_waitlist.user_id
            ).first()

            send_promoted_from_waitlist_email(
                to_email=promoted_user.email,
                user_name=promoted_user.full_name,
                event_title=event.title,
                event_date=str(event.start_datetime),
                event_location=event.location or "—",
                qr_image_base64=qr_image_base64
            )
            return {"message": "Te-ai dezînscris cu succes!"}

    db.commit()
    return {"message": "Te-ai dezînscris cu succes!"}

# POST feedback event
@router.post("/{event_id}/feedback")
def submit_feedback(event_id: int, feedback_data: dict, db: Session = Depends(get_db)):
    feedback = models.EventFeedback(
        event_id=event_id,
        user_id=1,  # temporar, ulterior din JWT
        rating=feedback_data.get("rating"),
        comment=feedback_data.get("comment")
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback

#GET metoda de preluare la care evenimnte sunt deja inregistrat returneaz doar ids
@router.get("/my/ids")
def get_my_event_ids(db: Session = Depends(get_db),user=Depends(get_current_user)):
    user_id = user["user_id"]

    registrations = db.query(models.EventRegistration).filter(
        models.EventRegistration.user_id == user_id
    ).all()

    return [r.event_id for r in registrations]

@router.get("/{event_id}/is-registered")
def is_registered(event_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    user_id = user["user_id"]
    registration = db.query(models.EventRegistration).filter(
        models.EventRegistration.user_id == user_id,
        models.EventRegistration.event_id == event_id
    ).first()

    if not registration:
        return {"registered": False, "status": "", "waitlist_position": None}

    return {
        "registered": True,
        "status": registration.status,                        # "registered" sau "waitlist"
        "waitlist_position": registration.waitlist_position   # numărul poziției sau None
    }


# GET qr-code al userului pentru un event
@router.get("/{event_id}/my-qr")
def get_my_qr(event_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    user_id = user["user_id"]

    registration = db.query(models.EventRegistration).filter(
        models.EventRegistration.event_id == event_id,
        models.EventRegistration.user_id == user_id
    ).first()

    if not registration:
        raise HTTPException(status_code=404, detail="Nu ești înregistrat la acest eveniment")

    if not registration.qr_code_token:
        raise HTTPException(status_code=404, detail="Acest eveniment nu folosește QR")
    # Regenerezi imaginea din token
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(registration.qr_code_token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    qr_image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return {
        "qr_code": f"data:image/png;base64,{qr_image_base64}",
        "qr_token": registration.qr_code_token
    }


# POST verificare QR la intrare (folosit de organizator)
@router.post("/{event_id}/verify-qr")
def verify_qr(event_id: int, body: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    token = body.get("token")

    registration = db.query(models.EventRegistration).filter(
        models.EventRegistration.event_id == event_id,
        models.EventRegistration.qr_code_token == token
    ).first()

    if not registration:
        raise HTTPException(status_code=404, detail="QR invalid!")

    if registration.status == "attended":
        raise HTTPException(status_code=400, detail="QR deja folosit!")

    registration.status = "attended"
    registration.checked_in = True
    registration.checked_in_at = datetime.utcnow()
    db.commit()

    return {"valid": True, "message": "Intrare confirmată!"}

# POST add sponsors
@router.post("/{event_id}/sponsors")
def add_sponsor(event_id: int, sponsor_data: SponsorCreate, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu există")

    sponsor = models.EventSponsor(
        event_id=event_id,
        name=sponsor_data.name,
        logo_path=sponsor_data.logo_url,
        website_url=sponsor_data.website_url
    )
    db.add(sponsor)
    db.commit()
    db.refresh(sponsor)
    return {"message": "Sponsor adăugat!", "id": sponsor.id, "name": sponsor.name}
#DELETE stergere sponsor dupa id
@router.delete("/{event_id}/sponsors/{sponsor_id}")
def delete_sponsor(event_id: int, sponsor_id: int, db: Session = Depends(get_db)):
    sponsor = db.query(models.EventSponsor).filter(
        models.EventSponsor.id == sponsor_id,
        models.EventSponsor.event_id == event_id
    ).first()
    if not sponsor:
        raise HTTPException(status_code=404, detail="Sponsor negăsit")
    db.delete(sponsor)
    db.commit()
    return {"message": "Sponsor șters!"}

# ============ MATERIALE ============
#POST adaugare materiale
@router.post("/{event_id}/materials")
def upload_materials(
    event_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu există")

    upload_dir = f"uploads/events/{event_id}"
    os.makedirs(upload_dir, exist_ok=True)

    saved = []
    for file in files:
        safe_name = sanitize_filename(file.filename)  # ← nume curat
        file_path = f"{upload_dir}/{safe_name}"

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        size_kb = os.path.getsize(file_path) // 1024
        ext = safe_name.split(".")[-1].lower() if "." in safe_name else ""

        material = models.EventMaterial(
            event_id=event_id,
            uploaded_by=1,
            file_name=file.filename,   # numele original afișat în UI
            file_type=ext,
            file_path=file_path,       # path-ul cu nume curat pe disk
            file_size_kb=size_kb
        )
        db.add(material)
        saved.append({"name": file.filename, "size_kb": size_kb, "type": ext})

    db.commit()
    return {"message": f"{len(saved)} fișiere încărcate!", "files": saved}
#DELETE sterge material dupa id
@router.delete("/{event_id}/materials/{material_id}")
def delete_material(event_id: int, material_id: int, db: Session = Depends(get_db)):
    material = db.query(models.EventMaterial).filter(
        models.EventMaterial.id == material_id,
        models.EventMaterial.event_id == event_id
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Materialul negăsit")

    # Șterge fișierul de pe disk
    if os.path.exists(material.file_path):
        os.remove(material.file_path)

    db.delete(material)
    db.commit()
    return {"message": "Material șters!"}

#Functie de preluare sentiment pe baza de feddBack
def get_sentiment(feedbacks) -> dict:
    if not feedbacks:
        return {"label": "Fără recenzii", "color": "neutral", "emoji": "⚪"}

    avg = sum(f.rating for f in feedbacks) / len(feedbacks)

    if avg >= 4.0:
        return {"label": "Foarte pozitiv", "color": "positive", "emoji": "🟢"}
    elif avg >= 3.0:
        return {"label": "Mixt", "color": "mixed", "emoji": "🟡"}
    elif avg >= 2.0:
        return {"label": "Negativ", "color": "negative", "emoji": "🔴"}
    else:
        return {"label": "Foarte negativ", "color": "very_negative", "emoji": "⛔"}


@router.get("/")
def get_events(db: Session = Depends(get_db)):
    events = db.query(models.Event).all()
    result = []
    for event in events:
        sentiment = get_sentiment(event.feedbacks)
        result.append({
            # ... toate câmpurile existente ...
            "sentiment": sentiment,
            "avg_rating": round(sum(f.rating for f in event.feedbacks) / len(event.feedbacks),
                                1) if event.feedbacks else None,
            "feedback_count": len(event.feedbacks),
        })
    return result

#get toti participantio la evenimentul x.
@router.get("/{event_id}/participants")
def get_participants(event_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu există")

    # Doar organizatorul sau admin poate vedea lista
    if event.organizer_id != user["user_id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acces interzis!")

    registrations = db.query(models.EventRegistration).filter(
        models.EventRegistration.event_id == event_id
    ).all()

    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "full_name": r.user.full_name,
            "email": r.user.email,
            "status": r.status,
            "waitlist_position": r.waitlist_position,
            "registered_at": str(r.registered_at),
            "checked_in": r.checked_in,
            "checked_in_at": str(r.checked_in_at) if r.checked_in_at else None,
        }
        for r in registrations
    ]
#HELPERS
def sanitize_filename(filename: str) -> str:
    # Păstrezi extensia
    name, ext = os.path.splitext(filename)
    # Înlocuiești orice caracter special cu underscore
    name = re.sub(r'[^\w\-]', '_', name)
    # Elimini underscore-uri multiple consecutive
    name = re.sub(r'_+', '_', name)
    return f"{name}{ext}"
