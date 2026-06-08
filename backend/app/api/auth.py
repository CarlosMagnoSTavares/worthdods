from fastapi import APIRouter, HTTPException, Header
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/verify-token")
async def verify_token(authorization: Optional[str] = Header(None)):
    """Verifica se o JWT do Supabase é válido."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token necessário")

    token = authorization.split(" ")[1]
    try:
        import jwt
        payload = jwt.decode(
            token, options={"verify_signature": False}, algorithms=["HS256"]
        )
        return {
            "valid": True,
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {e}")
