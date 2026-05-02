# Evenimente

Prefix: `/events`  
Tag: `Events`

Modulul gestioneaza crearea, editarea, stergerea evenimentelor, inscrierile participantilor, sistemul de waitlist, QR code-uri, feedback, sponsori si materiale.

---

## Modelul EventCreate

Folosit la crearea si actualizarea evenimentelor.

| Camp | Tip | Obligatoriu | Default | Descriere |
|------|-----|-------------|---------|-----------|
| `title` | string | ✅ | — | Titlul evenimentului |
| `description` | string | ❌ | null | Descrierea evenimentului |
| `category` | string | ❌ | null | Categoria (ex: conferinta, workshop) |
| `faculty` | string | ❌ | null | Facultatea organizatoare |
| `start_datetime` | string (ISO) | ✅ | — | Data si ora de inceput |
| `end_datetime` | string (ISO) | ❌ | null | Data si ora de sfarsit |
| `registration_deadline` | string (ISO) | ❌ | null | Termen limita inscriere |
| `location` | string | ❌ | null | Locatia fizica |
| `participation_mode` | string | ❌ | `In-Person` | `In-Person`, `Online`, `Hybrid` |
| `entry_type` | string | ❌ | `free` | `free` sau `qr_code` |
| `max_participants` | int | ❌ | null | Numar maxim de participanti |
| `status` | string | ❌ | `active` | `active`, `cancelled`, `completed` |
| `registration_link` | string | ❌ | null | Link extern de inscriere |

---

## GET /events/

Returneaza toate evenimentele cu detalii complete, inclusiv sentiment, rating mediu si sponsori.

**Nu necesita autentificare.**

**Raspuns succes `200`:**
```json
[
  {
    "id": 1,
    "title": "Workshop Python",
    "description": "...",
    "category": "workshop",
    "faculty": "Informatica",
    "start_datetime": "2025-06-01 10:00:00",
    "end_datetime": "2025-06-01 14:00:00",
    "location": "Sala A1",
    "participation_mode": "In-Person",
    "status": "active",
    "entry_type": "qr_code",
    "max_participants": 50,
    "registration_deadline": "2025-05-30 23:59:00",
    "organizer_id": 3,
    "organizer_name": "Ion Popescu",
    "sponsors": [
      { "name": "Acme Corp", "logo_path": "/uploads/logo.png", "website_url": "https://acme.com" }
    ],
    "sentiment": { "label": "Foarte pozitiv", "color": "positive", "emoji": "🟢" },
    "avg_rating": 4.5,
    "feedback_count": 12
  }
]
```

---

## GET /events/my/created

Returneaza evenimentele create de utilizatorul autentificat.

**Necesita autentificare.**

**Raspuns:** Aceeasi structura ca `GET /events/`.

---

## GET /events/my/ids

Returneaza lista de ID-uri ale evenimentelor la care utilizatorul este inscris.

**Necesita autentificare.**

**Raspuns succes `200`:**
```json
[1, 5, 12]
```

---

## GET /events/{event_id}

Returneaza detaliile complete ale unui eveniment, inclusiv materialele atasate.

**Nu necesita autentificare.**

**Parametri URL:**

| Parametru | Tip | Descriere |
|-----------|-----|-----------|
| `event_id` | int | ID-ul evenimentului |

**Raspuns eroare `404`:**
```json
{ "detail": "Evenimentul nu a fost găsit" }
```

---

## POST /events/

Creeaza un eveniment nou. Organizatorul este setat automat din tokenul JWT.

**Necesita autentificare.**

**Request body:** `EventCreate`

**Raspuns succes `200`:**
```json
{ "message": "Eveniment creat cu succes!", "id": 7 }
```

---

## PUT /events/{event_id}

Actualizeaza un eveniment existent.

**Necesita autentificare.** Doar organizatorul sau un admin pot edita.

**Raspuns eroare `403`:**
```json
{ "detail": "Nu ai permisiunea să editezi acest eveniment" }
```

---

## DELETE /events/{event_id}

Sterge un eveniment. Doar organizatorul poate sterge.

**Necesita autentificare.**

**Raspuns succes `200`:**
```json
{ "message": "Eveniment șters" }
```

---

## POST /events/{event_id}/register

Inscrie utilizatorul curent la un eveniment. Daca evenimentul este complet, utilizatorul este adaugat pe **lista de asteptare**.

**Necesita autentificare.**

**Logica de inscriere:**

```
Daca locuri disponibile:
  → status = "registered"
  → se genereaza QR daca entry_type == "qr_code"
  → se trimite email de confirmare cu QR (daca exista)

Daca complet:
  → status = "waitlist"
  → se calculeaza pozitia in waitlist
  → se trimite email de waitlist
```

**Raspuns succes — loc disponibil `200`:**
```json
{
  "message": "Înregistrat cu succes!",
  "status": "registered",
  "registration_id": 42,
  "qr_code": "data:image/png;base64,...",
  "qr_token": "uuid-unic"
}
```

**Raspuns succes — waitlist `200`:**
```json
{
  "message": "Evenimentul e complet! Ești pe lista de așteptare pe poziția 3.",
  "status": "waitlist",
  "waitlist_position": 3
}
```

**Raspuns eroare `400`:**
```json
{ "detail": "Ești deja înregistrat la acest eveniment!" }
```

---

## DELETE /events/{event_id}/unregister

Dezinscrie utilizatorul de la un eveniment. Daca utilizatorul era `registered`, primul din waitlist este promovat automat si primeste email de confirmare.

**Necesita autentificare.**

**Raspuns succes `200`:**
```json
{ "message": "Te-ai dezînscris cu succes!" }
```

---

## GET /events/{event_id}/is-registered

Verifica daca utilizatorul curent este inscris la un eveniment.

**Necesita autentificare.**

**Raspuns `200`:**
```json
{
  "registered": true,
  "status": "waitlist",
  "waitlist_position": 2
}
```

---

## GET /events/{event_id}/my-qr

Returneaza imaginea QR a utilizatorului curent pentru un eveniment cu `entry_type == "qr_code"`.

**Necesita autentificare.**

**Raspuns succes `200`:**
```json
{
  "qr_code": "data:image/png;base64,...",
  "qr_token": "uuid-unic"
}
```

---

## POST /events/{event_id}/verify-qr

Verifica un token QR la intrarea la eveniment. Marcheaza participantul ca `attended`.

**Necesita autentificare** (organizator).

**Request body:**
```json
{ "token": "uuid-token-qr" }
```

**Raspuns succes `200`:**
```json
{ "valid": true, "message": "Intrare confirmată!" }
```

**Raspuns eroare `400`:**
```json
{ "detail": "QR deja folosit!" }
```

---

## GET /events/{event_id}/participants

Returneaza lista completa a participantilor. Accesibil doar organizatorului sau adminului.

**Necesita autentificare.**

**Raspuns succes `200`:**
```json
[
  {
    "id": 1,
    "user_id": 5,
    "full_name": "Maria Ionescu",
    "email": "maria@example.com",
    "status": "registered",
    "waitlist_position": null,
    "registered_at": "2025-05-01 12:00:00",
    "checked_in": true,
    "checked_in_at": "2025-06-01 10:05:00"
  }
]
```

---

## POST /events/{event_id}/feedback

Trimite feedback pentru un eveniment.

**Request body:**
```json
{
  "rating": 5,
  "comment": "Eveniment excelent!"
}
```

---

## Sponsori

### GET /events/{event_id}/sponsors
Returneaza sponsorii unui eveniment.

### POST /events/{event_id}/sponsors
Adauga un sponsor.

**Request body:**
```json
{
  "name": "Firma XYZ",
  "logo_url": "/uploads/logo.png",
  "website_url": "https://firma.com"
}
```

### DELETE /events/{event_id}/sponsors/{sponsor_id}
Sterge un sponsor dupa ID.

---

## Materiale

### GET /events/{event_id}/materials
Returneaza materialele atasate unui eveniment.

### POST /events/{event_id}/materials
Incarca fisiere (multipart/form-data). Accepta mai multe fisiere simultan.

!!! info "Sanitizare nume fisiere"
    Numele fisierelor sunt sanitizate automat — caracterele speciale sunt inlocuite cu `_`.

### DELETE /events/{event_id}/materials/{material_id}
Sterge un material si fisierul aferent de pe disk.

---

## Sistemul de sentiment

Rating-urile din feedback sunt agregate si clasificate automat:

| Rating mediu | Label | Culoare |
|-------------|-------|---------|
| ≥ 4.0 | Foarte pozitiv | 🟢 |
| ≥ 3.0 | Mixt | 🟡 |
| ≥ 2.0 | Negativ | 🔴 |
| < 2.0 | Foarte negativ | ⛔ |
| Fara recenzii | Fara recenzii | ⚪ |
