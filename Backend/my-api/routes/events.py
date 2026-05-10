from typing import Annotated, Optional, List
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

from services.email_service import send_registration_email, send_promoted_from_waitlist_email, send_waitlist_email

import uuid
import qrcode
import io
import base64


router = APIRouter(prefix="/events", tags=["Events"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[dict, Depends(get_current_user)]


class EventCreate(BaseModel):
    """
    Schema Pydantic pentru crearea sau actualizarea unui eveniment.

    Attributes:
        title (str): Titlul evenimentului. Camp obligatoriu.
        description (str, optional): Descrierea detaliata a evenimentului.
        category (str, optional): Categoria evenimentului (ex: conferinta, workshop, seminar).
        faculty (str, optional): Facultatea sau departamentul organizator.
        start_datetime (str): Data si ora de inceput in format ISO 8601 (ex: '2025-06-01T10:00:00').
        end_datetime (str, optional): Data si ora de sfarsit in format ISO 8601.
        registration_deadline (str, optional): Termenul limita pentru inscrieri in format ISO 8601.
        location (str, optional): Locatia fizica a evenimentului.
        participation_mode (str, optional): Modul de participare. Valori posibile: 'In-Person', 'Online', 'Hybrid'. Default: 'In-Person'.
        entry_type (str, optional): Tipul de intrare. Valori posibile: 'free', 'qr_code'. Default: 'free'.
        max_participants (int, optional): Numarul maxim de participanti admisi.
        status (str, optional): Statusul evenimentului. Valori posibile: 'active', 'cancelled', 'completed'. Default: 'active'.
        registration_link (str, optional): Link extern pentru inscriere.
    """

    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    faculty: Optional[str] = None
    start_datetime: str
    end_datetime: Optional[str] = None
    registration_deadline: Optional[str] = None
    location: Optional[str] = None
    participation_mode: Optional[str] = "In-Person"
    entry_type: Optional[str] = "free"
    max_participants: Optional[int] = None
    status: Optional[str] = "active"
    registration_link: Optional[str] = None


class EventResponse(BaseModel):
    """
    Schema Pydantic pentru raspunsul unui eveniment.

    Attributes:
        id (int): ID-ul unic al evenimentului.
        title (str): Titlul evenimentului.
        description (str, optional): Descrierea evenimentului.
        category (str, optional): Categoria evenimentului.
        faculty (str, optional): Facultatea organizatoare.
        start_datetime (str): Data si ora de inceput.
        end_datetime (str, optional): Data si ora de sfarsit.
        location (str, optional): Locatia evenimentului.
        participation_mode (str, optional): Modul de participare.
        max_participants (int, optional): Numarul maxim de participanti.
        status (str): Statusul curent al evenimentului.
        created_at (str): Timestamp-ul crearii evenimentului.
    """

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
def serialize_event_full(event: models.Event, include_rejection: bool = False) -> dict:
    sentiment = get_sentiment(event.feedbacks)
    data = {
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
        "avg_rating": round(
            sum(f.rating for f in event.feedbacks) / len(event.feedbacks), 1
        ) if event.feedbacks else None,
        "feedback_count": len(event.feedbacks),
    }
    if include_rejection:
        data["rejection_reason"] = event.rejection_reason
    return data

def generate_qr_base64(token: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@router.get("/")
def get_events(db: DbSession) -> list:
    """
    Returneaza lista tuturor evenimentelor disponibile.

    Pentru fiecare eveniment sunt incluse informatii despre organizator,
    sponsori, sentiment agregat din feedback-uri si rating-ul mediu.

    Args:
        db (Session): Sesiunea bazei de date injectata prin dependency injection.

    Returns:
        list[dict]: Lista de dictionare cu datele complete ale evenimentelor,
            inclusiv campurile: id, title, description, category, faculty,
            start_datetime, end_datetime, location, participation_mode, status,
            entry_type, max_participants, registration_deadline, registration_link,
            created_at, updated_at, organizer_id, organizer_name, sponsors,
            sentiment, avg_rating, feedback_count.
    """
    events = db.query(models.Event).filter(
        models.Event.status.notin_(["pending", "rejected"])
    ).all()
    return [serialize_event_full(e) for e in events]


@router.get("/my/created")
def get_my_created_events(db: DbSession, user: CurrentUser) -> list:
    """
    Returneaza evenimentele create de utilizatorul autentificat curent.

    Filtreaza evenimentele dupa organizer_id, extras din tokenul JWT.
    Include aceleasi campuri ca GET /events/, dar doar pentru evenimentele
    apartinand utilizatorului curent.

    Args:
        db (Session): Sesiunea bazei de date.
        user (dict): Payload-ul JWT al utilizatorului curent, continand user_id si role.

    Returns:
        list[dict]: Lista evenimentelor create de utilizatorul curent.

    Raises:
        HTTPException 401: Daca tokenul JWT lipseste sau este invalid.
    """
    events = db.query(models.Event).filter(
        models.Event.organizer_id == user["user_id"]
    ).all()
    return [serialize_event_full(e, include_rejection=True) for e in events]


@router.get("/{event_id}")
def get_event(event_id: int, db: DbSession) -> dict:
    """
    Returneaza detaliile complete ale unui eveniment dupa ID.

    Include toate campurile evenimentului, plus lista de materiale atasate,
    sponsori, sentiment si rating mediu calculat din feedback-uri.

    Args:
        event_id (int): ID-ul unic al evenimentului cautat.
        db (Session): Sesiunea bazei de date.

    Returns:
        dict: Datele complete ale evenimentului, inclusiv campul 'materials'
            cu fisierele atasate (id, file_name, file_type, file_size_kb, file_path).

    Raises:
        HTTPException 404: Daca evenimentul cu ID-ul specificat nu exista.
    """
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu a fost găsit")

    data = serialize_event_full(event)
    data["materials"] = [
        {
            "id": m.id,
            "file_name": m.file_name,
            "file_type": m.file_type,
            "file_size_kb": m.file_size_kb,
            "file_path": m.file_path,
        }
        for m in event.materials
    ]
    # sponsors cu id inclus pentru GET single event
    data["sponsors"] = [
        {"id": s.id, "name": s.name, "logo_path": s.logo_path, "website_url": s.website_url}
        for s in event.sponsors
    ]
    return data


@router.post("/")
def create_event(event_data: EventCreate, db: DbSession, user: CurrentUser) -> dict:
    """
    Creeaza un eveniment nou in baza de date.

    Organizatorul este setat automat din tokenul JWT al utilizatorului autentificat.
    Datele de tip datetime sunt convertite din format ISO 8601 string la obiecte datetime.

    Args:
        event_data (EventCreate): Datele evenimentului de creat.
        db (Session): Sesiunea bazei de date.
        user (dict): Payload-ul JWT, folosit pentru a extrage user_id-ul organizatorului.

    Returns:
        dict: Mesaj de confirmare si ID-ul evenimentului creat.
            Exemplu: {"message": "Eveniment creat cu succes!", "id": 7}

    Raises:
        HTTPException 400: Daca datele sunt invalide sau apare o eroare la salvare.
        HTTPException 401: Daca utilizatorul nu este autentificat.
    """
    try:
        new_event = models.Event(
            title=event_data.title,
            description=event_data.description,
            category=event_data.category,
            faculty=event_data.faculty,
            start_datetime=datetime.fromisoformat(event_data.start_datetime),
            end_datetime=datetime.fromisoformat(event_data.end_datetime) if event_data.end_datetime else None,
            registration_deadline=datetime.fromisoformat(
                event_data.registration_deadline) if event_data.registration_deadline else None,
            location=event_data.location,
            participation_mode=event_data.participation_mode,
            entry_type=event_data.entry_type,
            max_participants=event_data.max_participants,
            status="pending",
            registration_link=event_data.registration_link,
            organizer_id=user["user_id"],
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return {"message": "Eveniment creat cu succes!", "id": new_event.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{event_id}")
def update_event(event_id: int, event_data: EventCreate, db: DbSession, user: CurrentUser) -> dict:
    """
    Actualizeaza datele unui eveniment existent.

    Doar organizatorul evenimentului sau un utilizator cu rolul 'admin'
    poate efectua modificari. Campul updated_at este actualizat automat.

    Args:
        event_id (int): ID-ul evenimentului de actualizat.
        event_data (EventCreate): Noile date ale evenimentului.
        db (Session): Sesiunea bazei de date.
        user (dict): Payload-ul JWT al utilizatorului curent.

    Returns:
        dict: Mesaj de confirmare si ID-ul evenimentului actualizat.
            Exemplu: {"message": "Eveniment actualizat!", "id": 7}

    Raises:
        HTTPException 404: Daca evenimentul nu exista.
        HTTPException 403: Daca utilizatorul nu are permisiunea de a edita.
        HTTPException 401: Daca utilizatorul nu este autentificat.
    """
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu a fost găsit")
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

@router.delete("/{event_id}")
def delete_event(event_id: int, db: DbSession, user: CurrentUser) -> dict:
    """
    Sterge un eveniment din baza de date.

    Doar organizatorul evenimentului poate efectua stergerea.
    Adminii nu pot sterge evenimentele altora prin acest endpoint.

    Args:
        event_id (int): ID-ul evenimentului de sters.
        db (Session): Sesiunea bazei de date.
        user (dict): Payload-ul JWT al utilizatorului curent.

    Returns:
        dict: Mesaj de confirmare.
            Exemplu: {"message": "Eveniment șters"}

    Raises:
        HTTPException 404: Daca evenimentul nu exista.
        HTTPException 403: Daca utilizatorul nu este organizatorul evenimentului.
        HTTPException 401: Daca utilizatorul nu este autentificat.
    """
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Eveniment negăsit")
    if event.organizer_id != user["user_id"]:
        raise HTTPException(status_code=403, detail="Nu ai permisiunea să ștergi acest eveniment")
    db.delete(event)
    db.commit()
    return {"message": "Eveniment șters"}


@router.get("/{event_id}/materials")
def get_event_materials(event_id: int, db: DbSession) -> list:
    """
    Returneaza lista materialelor atasate unui eveniment.

    Args:
        event_id (int): ID-ul evenimentului.
        db (Session): Sesiunea bazei de date.

    Returns:
        list[EventMaterial]: Lista obiectelor EventMaterial asociate evenimentului.
    """
    return db.query(models.EventMaterial).filter(
        models.EventMaterial.event_id == event_id
    ).all()


@router.get("/{event_id}/feedback")
def get_event_feedback(event_id: int, db: DbSession) -> list:
    """
    Returneaza toate feedback-urile primite pentru un eveniment.

    Args:
        event_id (int): ID-ul evenimentului.
        db (Session): Sesiunea bazei de date.

    Returns:
        list[EventFeedback]: Lista obiectelor EventFeedback asociate evenimentului.
    """
    return db.query(models.EventFeedback).filter(
        models.EventFeedback.event_id == event_id
    ).all()


@router.get("/{event_id}/sponsors")
def get_event_sponsors(event_id: int, db: DbSession) -> list:
    """
    Returneaza lista sponsorilor unui eveniment.

    Args:
        event_id (int): ID-ul evenimentului.
        db (Session): Sesiunea bazei de date.

    Returns:
        list[EventSponsor]: Lista obiectelor EventSponsor asociate evenimentului.
    """
    return db.query(models.EventSponsor).filter(
        models.EventSponsor.event_id == event_id
    ).all()


@router.post("/{event_id}/register")
def register_to_event(event_id: int, db: DbSession, user: CurrentUser) -> dict:
    """
    Inscrie utilizatorul curent la un eveniment.

    Logica de inscriere:
        1. Verifica existenta evenimentului.
        2. Verifica daca utilizatorul este deja inscris (registered sau waitlist).
        3. Numara locurile ocupate (doar status 'registered').
        4. Daca evenimentul este complet, adauga utilizatorul pe waitlist si trimite email.
        5. Daca exista locuri, genereaza QR code (doar daca entry_type == 'qr_code').
        6. Salveaza inregistrarea si trimite email de confirmare.

    Args:
        event_id (int): ID-ul evenimentului la care se face inscrierea.
        db (Session): Sesiunea bazei de date.
        user (dict): Payload-ul JWT al utilizatorului curent.

    Returns:
        dict: Statusul inscrierii. Daca evenimentul are entry_type 'qr_code',
            raspunsul include si campurile 'qr_code' (base64 PNG) si 'qr_token' (UUID).

    Raises:
        HTTPException 404: Daca evenimentul nu exista.
        HTTPException 400: Daca utilizatorul este deja inscris.
        HTTPException 401: Daca utilizatorul nu este autentificat.

    Example:
        Raspuns pentru loc disponibil::

            {
                "message": "Înregistrat cu succes!",
                "status": "registered",
                "registration_id": 42,
                "qr_code": "data:image/png;base64,...",
                "qr_token": "550e8400-e29b-41d4-a716-446655440000"
            }

        Raspuns pentru waitlist::

            {
                "message": "Evenimentul e complet! Ești pe lista de așteptare pe poziția 3.",
                "status": "waitlist",
                "waitlist_position": 3
            }
    """
    user_id = user["user_id"]

    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu există")

    existing = db.query(models.EventRegistration).filter(
        models.EventRegistration.event_id == event_id,
        models.EventRegistration.user_id == user_id,
        models.EventRegistration.status.in_(["registered", "waitlist"]),
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ești deja înregistrat la acest eveniment!")

    registered_count = db.query(models.EventRegistration).filter(
        models.EventRegistration.event_id == event_id,
        models.EventRegistration.status == "registered",
    ).count()

    is_full = event.max_participants and registered_count >= event.max_participants

    db_user = db.query(models.User).filter(models.User.id == user_id).first()

    if is_full:
        waitlist_count = db.query(models.EventRegistration).filter(
            models.EventRegistration.event_id == event_id,
            models.EventRegistration.status == "waitlist",
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

        send_waitlist_email(
            to_email=db_user.email,
            user_name=db_user.full_name,
            event_title=event.title,
            position=waitlist_count + 1,
        )
        return {
            "message": f"Evenimentul e complet! Ești pe lista de așteptare pe poziția {waitlist_count + 1}.",
            "status": "waitlist",
            "waitlist_position": waitlist_count + 1,
        }

    # ✅ generate_qr_base64 în loc de cod duplicat
    qr_token = None
    qr_image_base64 = None
    if event.entry_type == "qr_code":
        qr_token = str(uuid.uuid4())
        qr_image_base64 = generate_qr_base64(qr_token)

    registration = models.EventRegistration(
        event_id=event_id,
        user_id=user_id,
        status="registered",
        qr_code_token=qr_token,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)

    send_registration_email(
        to_email=db_user.email,
        user_name=db_user.full_name,
        event_title=event.title,
        event_date=str(event.start_datetime),
        event_location=event.location or "—",
        qr_image_base64=qr_image_base64,
    )

    response = {"message": "Înregistrat cu succes!", "status": "registered", "registration_id": registration.id}
    if qr_image_base64:
        response["qr_code"] = f"data:image/png;base64,{qr_image_base64}"
        response["qr_token"] = qr_token
    return response


@router.delete("/{event_id}/unregister")
def unregister_from_event(event_id: int, db: DbSession, user: CurrentUser) -> dict:
    """
    Dezinscrie utilizatorul curent de la un eveniment.

    Daca utilizatorul avea statusul 'registered', primul participant
    din waitlist este promovat automat la 'registered', primeste un QR code
    (daca entry_type == 'qr_code') si un email de notificare.
    Pozitiile din waitlist sunt reordonate dupa promovare.

    Daca utilizatorul era pe waitlist, este sters fara a promova pe altcineva.

    Args:
        event_id (int): ID-ul evenimentului de la care se face dezinscrierea.
        db (Session): Sesiunea bazei de date.
        user (dict): Payload-ul JWT al utilizatorului curent.

    Returns:
        dict: Mesaj de confirmare.
            Exemplu: {"message": "Te-ai dezînscris cu succes!"}

    Raises:
        HTTPException 404: Daca utilizatorul nu este inscris la eveniment.
        HTTPException 401: Daca utilizatorul nu este autentificat.
    """
    user_id = user["user_id"]

    registration = db.query(models.EventRegistration).filter(
        models.EventRegistration.event_id == event_id,
        models.EventRegistration.user_id == user_id,
        models.EventRegistration.status.in_(["registered", "waitlist"]),
    ).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Nu ești înregistrat la acest eveniment!")

    was_registered = registration.status == "registered"
    event = db.query(models.Event).filter(models.Event.id == event_id).first()

    db.delete(registration)
    db.flush()

    if was_registered:
        next_in_waitlist = db.query(models.EventRegistration).filter(
            models.EventRegistration.event_id == event_id,
            models.EventRegistration.status == "waitlist",
        ).order_by(models.EventRegistration.waitlist_position).first()

        if next_in_waitlist:
            qr_token = None
            qr_image_base64 = None
            if event.entry_type == "qr_code":
                qr_token = str(uuid.uuid4())
                qr_image_base64 = generate_qr_base64(qr_token)

            next_in_waitlist.status = "registered"
            next_in_waitlist.waitlist_position = None
            next_in_waitlist.qr_code_token = qr_token
            next_in_waitlist.registered_at = datetime.utcnow()
            db.flush()

            remaining = db.query(models.EventRegistration).filter(
                models.EventRegistration.event_id == event_id,
                models.EventRegistration.status == "waitlist",
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
                qr_image_base64=qr_image_base64,
            )
            return {"message": "Te-ai dezînscris cu succes!"}

    db.commit()
    return {"message": "Te-ai dezînscris cu succes!"}


@router.post("/{event_id}/feedback")
def submit_feedback(event_id: int, feedback_data: dict, db: DbSession) -> dict:
    """
    Trimite un feedback pentru un eveniment.

    Args:
        event_id (int): ID-ul evenimentului pentru care se trimite feedback-ul.
        feedback_data (dict): Datele feedback-ului. Campuri asteptate:
            - rating (int): Nota de la 1 la 5.
            - comment (str, optional): Comentariul textual.
        db (Session): Sesiunea bazei de date.

    Returns:
        EventFeedback: Obiectul feedback salvat in baza de date.
    """
    feedback = models.EventFeedback(
        event_id=event_id,
        user_id=1,
        rating=feedback_data.get("rating"),
        comment=feedback_data.get("comment"),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {"message": "Feedback trimis!", "id": feedback.id}


@router.get("/my/ids")
def get_my_event_ids(db: DbSession, user: CurrentUser) -> list[int]:
    """
    Returneaza lista ID-urilor evenimentelor la care utilizatorul curent este inscris.

    Util pentru a verifica rapid in frontend care evenimente sunt bifate
    ca inscrise, fara a incarca toate datele evenimentelor.

    Args:
        db (Session): Sesiunea bazei de date.
        user (dict): Payload-ul JWT al utilizatorului curent.

    Returns:
        list[int]: Lista de ID-uri ale evenimentelor la care utilizatorul are o inregistrare.
            Exemplu: [1, 5, 12]

    Raises:
        HTTPException 401: Daca utilizatorul nu este autentificat.
    """
    registrations = db.query(models.EventRegistration).filter(
        models.EventRegistration.user_id == user["user_id"]
    ).all()
    return [r.event_id for r in registrations]


@router.get("/{event_id}/is-registered")
def is_registered(event_id: int, db: DbSession, user: CurrentUser) -> dict:
    """
    Verifica daca utilizatorul curent este inscris la un eveniment specific.

    Args:
        event_id (int): ID-ul evenimentului de verificat.
        db (Session): Sesiunea bazei de date.
        user (dict): Payload-ul JWT al utilizatorului curent.

    Returns:
        dict: Statusul inscrierii cu campurile:
            - registered (bool): True daca utilizatorul are o inregistrare activa.
            - status (str): 'registered', 'waitlist', 'attended' sau '' daca nu e inscris.
            - waitlist_position (int | None): Pozitia in waitlist sau None.

    Raises:
        HTTPException 401: Daca utilizatorul nu este autentificat.
    """
    registration = db.query(models.EventRegistration).filter(
        models.EventRegistration.user_id == user["user_id"],
        models.EventRegistration.event_id == event_id,
    ).first()
    if not registration:
        return {"registered": False, "status": "", "waitlist_position": None}
    return {"registered": True, "status": registration.status, "waitlist_position": registration.waitlist_position}

@router.get("/{event_id}/my-qr")
def get_my_qr(event_id: int, db: DbSession, user: CurrentUser) -> dict:
    """
    Returneaza imaginea QR code a utilizatorului curent pentru un eveniment.

    QR code-ul este regenerat din tokenul unic salvat in baza de date
    si returnat ca imagine PNG encodata in base64.

    Args:
        event_id (int): ID-ul evenimentului.
        db (Session): Sesiunea bazei de date.
        user (dict): Payload-ul JWT al utilizatorului curent.

    Returns:
        dict: Datele QR code-ului:
            - qr_code (str): Imaginea PNG encodata base64 (format data URI).
            - qr_token (str): Tokenul UUID unic al QR code-ului.

    Raises:
        HTTPException 404: Daca utilizatorul nu este inscris la eveniment.
        HTTPException 404: Daca evenimentul nu foloseste QR code (entry_type != 'qr_code').
        HTTPException 401: Daca utilizatorul nu este autentificat.
    """
    registration = db.query(models.EventRegistration).filter(
        models.EventRegistration.event_id == event_id,
        models.EventRegistration.user_id == user["user_id"],
    ).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Nu ești înregistrat la acest eveniment")
    if not registration.qr_code_token:
        raise HTTPException(status_code=404, detail="Acest eveniment nu folosește QR")

    qr_image_base64 = generate_qr_base64(registration.qr_code_token)
    return {
        "qr_code": f"data:image/png;base64,{qr_image_base64}",
        "qr_token": registration.qr_code_token,
    }

@router.post("/{event_id}/verify-qr")
def verify_qr(event_id: int, body: dict, db: DbSession, user: CurrentUser) -> dict:
    """
    Verifica un token QR la intrarea participantului la eveniment.

    Folosit de organizator pentru a scana si valida QR code-ul unui participant.
    La validare cu succes, statusul inscrierii devine 'attended' si se
    marcheaza check-in-ul cu timestamp-ul curent.

    Args:
        event_id (int): ID-ul evenimentului la care se face verificarea.
        body (dict): Corpul requestului continand campul 'token' (str UUID).
        db (Session): Sesiunea bazei de date.
        user (dict): Payload-ul JWT al organizatorului autentificat.

    Returns:
        dict: Rezultatul verificarii.
            Exemplu: {"valid": True, "message": "Intrare confirmată!"}

    Raises:
        HTTPException 404: Daca tokenul QR nu corespunde niciunei inregistrari.
        HTTPException 400: Daca QR code-ul a fost deja folosit (status 'attended').
        HTTPException 401: Daca utilizatorul nu este autentificat.
    """
    token = body.get("token")
    registration = db.query(models.EventRegistration).filter(
        models.EventRegistration.event_id == event_id,
        models.EventRegistration.qr_code_token == token,
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


@router.post("/{event_id}/sponsors")
def add_sponsor(event_id: int, sponsor_data: SponsorCreate, db: DbSession) -> dict:
    """
    Adauga un sponsor la un eveniment.

    Args:
        event_id (int): ID-ul evenimentului la care se adauga sponsorul.
        sponsor_data (SponsorCreate): Datele sponsorului: name, logo_url, website_url.
        db (Session): Sesiunea bazei de date.

    Returns:
        dict: Mesaj de confirmare, ID-ul si numele sponsorului adaugat.
            Exemplu: {"message": "Sponsor adăugat!", "id": 3, "name": "Acme Corp"}

    Raises:
        HTTPException 404: Daca evenimentul nu exista.
    """
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu există")

    sponsor = models.EventSponsor(
        event_id=event_id,
        name=sponsor_data.name,
        logo_path=sponsor_data.logo_url,
        website_url=sponsor_data.website_url,
    )
    db.add(sponsor)
    db.commit()
    db.refresh(sponsor)
    return {"message": "Sponsor adăugat!", "id": sponsor.id, "name": sponsor.name}

@router.delete("/{event_id}/sponsors/{sponsor_id}")
def delete_sponsor(event_id: int, sponsor_id: int, db: DbSession) -> dict:
    """
    Sterge un sponsor dintr-un eveniment dupa ID.

    Args:
        event_id (int): ID-ul evenimentului.
        sponsor_id (int): ID-ul sponsorului de sters.
        db (Session): Sesiunea bazei de date.

    Returns:
        dict: Mesaj de confirmare.
            Exemplu: {"message": "Sponsor șters!"}

    Raises:
        HTTPException 404: Daca sponsorul nu exista sau nu apartine evenimentului.
    """
    sponsor = db.query(models.EventSponsor).filter(
        models.EventSponsor.id == sponsor_id,
        models.EventSponsor.event_id == event_id,
    ).first()
    if not sponsor:
        raise HTTPException(status_code=404, detail="Sponsor negăsit")
    db.delete(sponsor)
    db.commit()
    return {"message": "Sponsor șters!"}


@router.post("/{event_id}/materials")
def upload_materials(
    event_id: int,
    files: Annotated[List[UploadFile], File(...)],
    db: DbSession,
) -> dict:

    """
    Incarca unul sau mai multe fisiere ca materiale pentru un eveniment.

    Fisierele sunt salvate pe disk in directorul 'uploads/events/{event_id}/'.
    Numele fisierelor sunt sanitizate automat pentru a elimina caracterele speciale.
    Metadatele fiecarui fisier (nume, tip, dimensiune, cale) sunt salvate in baza de date.

    Args:
        event_id (int): ID-ul evenimentului la care se ataseaza materialele.
        files (List[UploadFile]): Lista de fisiere uploadate prin multipart/form-data.
        db (Session): Sesiunea bazei de date.

    Returns:
        dict: Mesaj de confirmare si lista fisierelor salvate cu name, size_kb si type.
            Exemplu: {"message": "2 fișiere încărcate!", "files": [...]}

    Raises:
        HTTPException 404: Daca evenimentul nu exista.
    """
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu există")

    upload_dir = f"uploads/events/{event_id}"
    os.makedirs(upload_dir, exist_ok=True)

    saved = []
    for file in files:
        safe_name = sanitize_filename(file.filename)
        file_path = f"{upload_dir}/{safe_name}"
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        size_kb = os.path.getsize(file_path) // 1024
        ext = safe_name.split(".")[-1].lower() if "." in safe_name else ""

        material = models.EventMaterial(
            event_id=event_id,
            uploaded_by=1,
            file_name=file.filename,
            file_type=ext,
            file_path=file_path,
            file_size_kb=size_kb,
        )
        db.add(material)
        saved.append({"name": file.filename, "size_kb": size_kb, "type": ext})

    db.commit()
    return {"message": f"{len(saved)} fișiere încărcate!", "files": saved}

@router.delete("/{event_id}/materials/{material_id}")
def delete_material(event_id: int, material_id: int, db: DbSession) -> dict:
    """
    Sterge un material dintr-un eveniment si fisierul aferent de pe disk.

    Args:
        event_id (int): ID-ul evenimentului.
        material_id (int): ID-ul materialului de sters.
        db (Session): Sesiunea bazei de date.

    Returns:
        dict: Mesaj de confirmare.
            Exemplu: {"message": "Material șters!"}

    Raises:
        HTTPException 404: Daca materialul nu exista sau nu apartine evenimentului.
    """
    material = db.query(models.EventMaterial).filter(
        models.EventMaterial.id == material_id,
        models.EventMaterial.event_id == event_id,
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Materialul negăsit")
    if os.path.exists(material.file_path):
        os.remove(material.file_path)
    db.delete(material)
    db.commit()
    return {"message": "Material șters!"}


@router.get("/{event_id}/participants")
def get_participants(event_id: int, db: DbSession, user: CurrentUser) -> list:
    """
    Returneaza lista completa a participantilor la un eveniment.

    Accesibil doar de catre organizatorul evenimentului sau utilizatorii cu rolul 'admin'.
    Include informatii despre status, pozitia in waitlist si check-in.

    Args:
        event_id (int): ID-ul evenimentului.
        db (Session): Sesiunea bazei de date.
        user (dict): Payload-ul JWT al utilizatorului curent.

    Returns:
        list[dict]: Lista participantilor cu campurile: id, user_id, full_name,
            email, status, waitlist_position, registered_at, checked_in, checked_in_at.

    Raises:
        HTTPException 404: Daca evenimentul nu exista.
        HTTPException 403: Daca utilizatorul nu este organizatorul sau admin.
        HTTPException 401: Daca utilizatorul nu este autentificat.
    """
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Evenimentul nu există")
    if event.organizer_id != user["user_id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acces interzis!")

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
        for r in db.query(models.EventRegistration).filter(
            models.EventRegistration.event_id == event_id
        ).all()
    ]

def get_sentiment(feedbacks) -> dict:
    """
    Calculeaza sentimentul agregat pe baza rating-urilor din feedback-uri.

    Folosit intern pentru a clasifica perceptia generala a participantilor
    despre un eveniment, bazat pe media rating-urilor primite.

    Args:
        feedbacks (list): Lista obiectelor EventFeedback, fiecare avand campul 'rating'.

    Returns:
        dict: Dictionarul cu sentimentul calculat, continand campurile:
            - label (str): Eticheta textuala a sentimentului.
            - color (str): Identificatorul de culoare ('positive', 'mixed', 'negative', 'very_negative', 'neutral').
            - emoji (str): Emoji reprezentativ.

    Examples:
        Valorile posibile returnate:

        - Rating mediu >= 4.0: {"label": "Foarte pozitiv", "color": "positive", "emoji": "🟢"}
        - Rating mediu >= 3.0: {"label": "Mixt", "color": "mixed", "emoji": "🟡"}
        - Rating mediu >= 2.0: {"label": "Negativ", "color": "negative", "emoji": "🔴"}
        - Rating mediu < 2.0:  {"label": "Foarte negativ", "color": "very_negative", "emoji": "⛔"}
        - Fara feedback:       {"label": "Fără recenzii", "color": "neutral", "emoji": "⚪"}
    """
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


def sanitize_filename(filename: str) -> str:
    """
    Sanitizeaza numele unui fisier pentru a fi salvat in siguranta pe disk.

    Elimina sau inlocuieste caracterele speciale care ar putea cauza probleme
    in sistemul de fisiere, pastrând extensia originala a fisierului.

    Args:
        filename (str): Numele original al fisierului uploadat.

    Returns:
        str: Numele sanitizat, cu caracterele speciale inlocuite prin underscore
            si underscore-urile consecutive reduse la unul singur.

    Examples:
        >>> sanitize_filename("raport final (2025).pdf")
        'raport_final__2025_.pdf'
        >>> sanitize_filename("fisier___test.docx")
        'fisier_test.docx'
    """
    name, ext = os.path.splitext(filename)
    name = re.sub(r'[^\w\-]', '_', name)
    name = re.sub(r'_+', '_', name)
    return f"{name}{ext}"