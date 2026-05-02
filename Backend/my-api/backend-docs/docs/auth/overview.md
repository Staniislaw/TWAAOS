# Autentificare — Prezentare generala

Sistemul foloseste **JWT (JSON Web Tokens)** pentru autentificare. Tokenurile sunt generate la login si trebuie trimise in fiecare request protejat.

## Flux de autentificare

1. Utilizatorul se inregistreaza la `POST /auth/register`
2. Utilizatorul se autentifica la `POST /auth/login` si primeste un `access_token`
3. Tokenul se include in header-ul `Authorization: Bearer <token>` la fiecare request protejat

## Structura tokenului JWT

Tokenul contine urmatoarele informatii (payload):

| Camp | Tip | Descriere |
|------|-----|-----------|
| `sub` | string | Email-ul utilizatorului |
| `user_id` | int | ID-ul utilizatorului |
| `role` | string | Rolul: `admin`, `organizer`, etc. |

## Roluri

| Rol | Permisiuni |
|-----|-----------|
| `admin` | Acces complet, poate edita/sterge orice eveniment |
| `organizer` | Poate crea si gestiona propriile evenimente |

## Dependinta `get_current_user`

Rutele protejate folosesc dependinta `get_current_user` care:

1. Extrage tokenul din header-ul `Authorization`
2. Verifica formatul `Bearer <token>`
3. Valideaza tokenul cu `verify_token()`
4. Returneaza payload-ul JWT sau arunca `401 Unauthorized`

```python
# Exemplu de utilizare
@router.get("/ruta-protejata")
def ruta(user=Depends(get_current_user)):
    user_id = user["user_id"]
    role = user["role"]
```

!!! warning "Token invalid sau expirat"
    Daca tokenul este invalid sau a expirat, API-ul returneaza `401 Unauthorized` cu mesajul `Token invalid sau expirat`.
