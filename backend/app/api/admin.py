from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from typing import Optional, List
from app.database import get_supabase
from app.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(x_admin_key: Optional[str] = Header(None)):
    if x_admin_key != settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Acesso negado")


@router.post("/sync")
async def trigger_sync(
    background_tasks: BackgroundTasks,
    fonte: Optional[str] = None,
    ufs: Optional[str] = None,
    x_admin_key: Optional[str] = Header(None),
):
    require_admin(x_admin_key)
    from app.services.caixa_ingestion import sync_all_ufs
    from app.services.santander_ingestion import sync_santander
    from app.services.biasi_ingestion import sync_biasi

    ufs_list: Optional[List[str]] = None
    if ufs:
        ufs_list = [u.strip().upper() for u in ufs.split(",")]

    fontes = ["caixa", "santander", "biasi"] if not fonte else [fonte.lower()]

    for f in fontes:
        if f == "caixa":
            background_tasks.add_task(sync_all_ufs, ufs_list)
        elif f == "santander":
            background_tasks.add_task(sync_santander, ufs_list)
        elif f == "biasi":
            background_tasks.add_task(sync_biasi, ufs_list)

    return {
        "message": "Sincronização iniciada",
        "fontes": fontes,
        "ufs": ufs_list or settings.ufs_list,
        "status": "processing",
    }


@router.get("/sync/logs")
async def get_sync_logs(x_admin_key: Optional[str] = Header(None)):
    require_admin(x_admin_key)
    supabase = get_supabase()
    result = supabase.table("sync_logs").select("*").order(
        "iniciado_em", desc=True
    ).limit(20).execute()
    return {"logs": result.data or []}


@router.post("/properties/{property_id}/analyze")
async def admin_analyze(
    property_id: str,
    background_tasks: BackgroundTasks,
    x_admin_key: Optional[str] = Header(None),
):
    require_admin(x_admin_key)
    from app.api.analysis import run_full_analysis

    background_tasks.add_task(run_full_analysis, property_id)
    return {"message": "Análise iniciada", "property_id": property_id}


@router.post("/sync-and-cleanup")
async def sync_and_cleanup(
    background_tasks: BackgroundTasks,
    x_admin_key: Optional[str] = Header(None),
):
    require_admin(x_admin_key)
    from app.services.caixa_ingestion import sync_all_ufs
    from app.services.santander_ingestion import sync_santander
    from app.services.biasi_ingestion import sync_biasi

    background_tasks.add_task(sync_all_ufs)
    background_tasks.add_task(sync_santander)
    background_tasks.add_task(sync_biasi)

    return {
        "message": "Sincronização e limpeza iniciadas para todas as fontes",
        "fontes": ["caixa", "santander", "biasi"],
        "status": "processing",
    }


@router.delete("/properties/{property_id}/analysis")
async def delete_analysis(
    property_id: str,
    x_admin_key: Optional[str] = Header(None),
):
    require_admin(x_admin_key)
    supabase = get_supabase()
    supabase.table("property_analyses").delete().eq("property_id", property_id).execute()
    supabase.table("legal_checks").delete().eq("property_id", property_id).execute()
    return {"message": "Análise removida", "property_id": property_id}
