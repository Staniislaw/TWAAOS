# Autentificare — Endpoints

## POST /auth/register

Inregistreaza un utilizator nou.

**Nu necesita autentificare.**

**Request body:**
```json
{
  "username": "user@example.com",
  "password": "parola123"
}
```

**Raspuns succes `200`:**
```json
{
  "message": "User creat"
}
```

**Raspuns eroare `400`:**
```json
{
  "detail": "User deja există"
}
```

!!! info "Detalii implementare"
    - Parola este hashata cu algoritmul **Argon2**
    - Rolul implicit este `organizer`
    - Email-ul este folosit atat ca `username` cat si ca `full_name`

---

## POST /auth/login

Autentifica un utilizator si returneaza un JWT.

**Nu necesita autentificare.**

**Request body:**
```json
{
  "username": "user@example.com",
  "password": "parola123"
}
```

**Raspuns succes `200`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Raspuns eroare `401`:**
```json
{
  "detail": "Credentiale incorecte"
}
```

---

## GET /protected

Ruta de test pentru verificarea autentificarii.

**Necesita autentificare.**

**Raspuns succes `200`:**
```json
{
  "message": "Acces permis!",
  "user": {
    "sub": "user@example.com",
    "user_id": 1,
    "role": "organizer"
  }
}
```

---

## GET /profile

Returneaza datele din tokenul JWT al utilizatorului curent.

**Necesita autentificare.**

**Raspuns succes `200`:**
```json
{
  "message": "Profilul tau",
  "data": {
    "sub": "user@example.com",
    "user_id": 1,
    "role": "organizer"
  }
}
```
