# Backend API Documentation

Documentatia oficiala pentru aplicatia backend construita cu **FastAPI** + **SQLAlchemy**.

## Module principale

| Modul | Prefix | Descriere |
|-------|--------|-----------|
| Auth | `/auth` | Inregistrare, autentificare, JWT |
| Events | `/events` | Gestionare evenimente, inscrieri, QR |
| Users | `/users` | Gestionare utilizatori |

## Autentificare

Toate rutele protejate necesita un header de tipul:

```
Authorization: Bearer <token>
```

Tokenul se obtine dupa login la `/auth/login`.

## Documentatie interactiva

FastAPI genereaza automat documentatie interactiva:

- **Swagger UI** → `http://localhost:8000/docs`
- **ReDoc** → `http://localhost:8000/redoc`
