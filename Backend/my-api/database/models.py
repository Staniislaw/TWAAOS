from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="user")
    password_hash = Column(String, nullable=True)
    oauth_provider = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    events = relationship("Event", back_populates="organizer")
    registrations = relationship("EventRegistration", back_populates="user")
    feedbacks = relationship("EventFeedback", back_populates="user")
    materials = relationship("EventMaterial", back_populates="uploaded_by_user")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    organizer_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    description = Column(Text, nullable=True)
    start_datetime = Column(DateTime)
    end_datetime = Column(DateTime)
    location = Column(String, nullable=True)
    participation_mode = Column(String, nullable=True)
    category = Column(String, nullable=True)
    faculty = Column(String, nullable=True)
    status = Column(String, default="active")
    entry_type = Column(String, default="free")
    registration_link = Column(String, nullable=True)
    max_participants = Column(Integer, nullable=True)
    registration_deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    organizer = relationship("User", back_populates="events")
    registrations = relationship("EventRegistration", back_populates="event")
    feedbacks = relationship("EventFeedback", back_populates="event")
    materials = relationship("EventMaterial", back_populates="event")
    sponsors = relationship("EventSponsor", back_populates="event")

class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="registered")
    qr_code_token = Column(String, nullable=True)
    checked_in = Column(Boolean, default=False)
    checked_in_at = Column(DateTime, nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="registrations")
    user = relationship("User", back_populates="registrations")


class EventFeedback(Base):
    __tablename__ = "event_feedback"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")


class EventMaterial(Base):
    __tablename__ = "event_materials"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    file_name = Column(String)
    file_type = Column(String, nullable=True)
    file_path = Column(String)
    file_size_kb = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="materials")
    uploaded_by_user = relationship("User", back_populates="materials")


class EventSponsor(Base):
    __tablename__ = "event_sponsors"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    name = Column(String)
    logo_path = Column(String, nullable=True)
    website_url = Column(String, nullable=True)

    event = relationship("Event", back_populates="sponsors")