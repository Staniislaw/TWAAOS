import os
import json
import httpx
import subprocess
from typing import Annotated, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database.database import get_db
from database import models
from auth.dependencies import get_current_user

load_dotenv()

router = APIRouter(prefix="/ai-scraper", tags=["AI Scraper"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[dict, Depends(get_current_user)]

class ImportEventRequest(BaseModel):
    title: str
    description: Optional[str] = None
    start_datetime: Optional[str] = None
    location: Optional[str] = None
    entry_type: Optional[str] = "free"
    price: Optional[str] = None


class ScrapedEvent(BaseModel):
    title: str
    description: Optional[str] = None
    start_datetime: Optional[str] = None
    location: Optional[str] = None
    entry_type: Optional[str] = "free"
    price: Optional[str] = None

class ScrapeResponse(BaseModel):
    source_url: str
    events: List[ScrapedEvent]
    debug_info: Optional[str] = None

def clean_html(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        element.decompose()
    return soup.get_text(separator="\n", strip=True)

async def get_events_from_ai(text_content: str) -> tuple:
    prompt = f"""Extrage toate evenimentele din textul următor ca JSON valid (listă de obiecte).
Fiecare obiect să aibă: title, description, start_datetime, location, entry_type, price.
entry_type este "free" dacă e gratuit, altfel "paid".
Returnează DOAR JSON-ul, fără explicații, fără markdown.

TEXT:
{text_content[:8000]}"""

    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File",
             r"C:\nvm4w\nodejs\gemini.ps1", "-p", prompt, "-y"],
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            cwd=r"C:\ISA-TWAOOS PROJECT\backend"
        )
        print(f"[GEMINI returncode]: {result.returncode}")
        print(f"[GEMINI stdout]: {result.stdout[:300]}")
        print(f"[GEMINI stderr]: {result.stderr[:300]}")

        if result.returncode != 0:
            return [], f"Eroare Gemini CLI: {result.stderr[:200]}"

        content = result.stdout.strip()

        if "[" in content and "]" in content:
            start = content.find("[")
            end = content.rfind("]") + 1
            content = content[start:end]

        return json.loads(content), None

    except subprocess.TimeoutExpired:
        return [], "Gemini CLI timeout"
    except Exception as e:
        return [], f"Eroare: {str(e)}"

@router.get("/scrape", response_model=ScrapeResponse)
async def scrape_local_events(url: str = "https://www.orasulsuceava.ro/evenimente/"):
    print(f"[SCRAPER] Start: {url}")

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            print(f"[SCRAPER] HTML: {len(response.text)} chars")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Eroare la accesarea site-ului: {str(e)}")

    cleaned_text = clean_html(response.text)
    print(f"[SCRAPER] Text curat: {len(cleaned_text)} chars")

    if len(cleaned_text) < 100:
        return {"source_url": url, "events": [], "debug_info": "Conținut gol sau blocat."}

    events_data, error_msg = await get_events_from_ai(cleaned_text)
    print(f"[SCRAPER] Evenimente: {len(events_data)}, Eroare: {error_msg}")

    return {
        "source_url": url,
        "events": events_data,
        "debug_info": error_msg
    }

@router.post("/import")
def import_scraped_event(event: ImportEventRequest, db: DbSession, user: CurrentUser):
    try:
        # Parsează data dacă există
        start_dt = None
        if event.start_datetime:
            try:
                start_dt = datetime.fromisoformat(event.start_datetime)
            except:
                start_dt = None

        new_event = models.Event(
            title=event.title,
            description=f"{event.description or ''}\n💰 Preț: {event.price}".strip() if event.price else event.description,
            location=event.location,
            entry_type="free" if event.entry_type == "free" else "registration",
            start_datetime=start_dt or datetime.utcnow(),
            status="pending",
            participation_mode="In-Person",
            organizer_id=user["user_id"],
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        return {"message": "Eveniment importat cu succes!", "id": new_event.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))