from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from app.database import get_supabase

router = APIRouter(prefix="/favorites", tags=["favorites"])


def get_user_from_token(authorization: Optional[str]) -> str:
    """Extrai user_id do JWT do Supabase."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token de autenticação necessário")
    token = authorization.split(" ")[1]
    try:
        from app.config import settings
        import jwt
        payload = jwt.decode(
            token,
            settings.SUPABASE_ANON_KEY,
            algorithms=["HS256"],
            options={"verify_signature": False},
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")


@router.get("")
async def list_favorites(authorization: Optional[str] = Header(None)):
    user_id = get_user_from_token(authorization)
    supabase = get_supabase()
    result = supabase.table("user_favorites").select(
        "*, properties(*)"
    ).eq("user_id", user_id).execute()
    return {"data": result.data or []}


@router.post("/{property_id}")
async def add_favorite(property_id: str, authorization: Optional[str] = Header(None)):
    user_id = get_user_from_token(authorization)
    supabase = get_supabase()

    prop = supabase.table("properties").select("id").eq("id", property_id).single().execute()
    if not prop.data:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    supabase.table("user_favorites").upsert(
        {"user_id": user_id, "property_id": property_id},
        on_conflict="user_id,property_id",
    ).execute()

    return {"message": "Adicionado aos favoritos"}


@router.delete("/{property_id}")
async def remove_favorite(property_id: str, authorization: Optional[str] = Header(None)):
    user_id = get_user_from_token(authorization)
    supabase = get_supabase()

    supabase.table("user_favorites").delete().eq("user_id", user_id).eq(
        "property_id", property_id
    ).execute()

    return {"message": "Removido dos favoritos"}
