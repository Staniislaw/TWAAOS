# Utilizatori

Prefix: `/users`

---

## GET /users/

Returneaza lista tuturor utilizatorilor.

**Nu necesita autentificare.**

**Raspuns succes `200`:** Lista de obiecte `User`.

---

## GET /users/{user_id}

Returneaza un utilizator dupa ID.

**Nu necesita autentificare.**

**Parametri URL:**

| Parametru | Tip | Descriere |
|-----------|-----|-----------|
| `user_id` | int | ID-ul utilizatorului |

**Raspuns succes `200`:** Obiect `User` sau `null` daca nu exista.
