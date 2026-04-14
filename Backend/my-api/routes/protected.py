from fastapi import APIRouter, Depends, HTTPException, status, Header
from auth.jwt_handler import verify_token

router = APIRouter()

def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Format invalid. Foloseste: Bearer <token>"
        )
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid sau expirat"
        )
    return payload

@router.get("/protected")
def protected_route(user=Depends(get_current_user)):
    return {"message": "Acces permis!", "user": user}

@router.get("/profile")
def get_profile(user=Depends(get_current_user)):
    return {"message": "Profilul tau", "data": user}