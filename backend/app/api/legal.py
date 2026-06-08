from fastapi import APIRouter, HTTPException
from app.database import get_supabase

router = APIRouter(prefix="/properties", tags=["legal"])


@router.get("/{property_id}/legal")
async def get_legal_checks(property_id: str):
    supabase = get_supabase()

    prop = supabase.table("properties").select("id").eq("id", property_id).single().execute()
    if not prop.data:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    result = supabase.table("legal_checks").select("*").eq("property_id", property_id).execute()

    return {"property_id": property_id, "legal_checks": result.data or []}
