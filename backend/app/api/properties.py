from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.database import get_supabase

router = APIRouter(prefix="/properties", tags=["properties"])

VALID_ORDER_FIELDS = {"ipl_score", "preco", "desconto_percentual", "updated_at", "created_at"}


@router.get("")
async def list_properties(
    uf: Optional[str] = None,
    cidade: Optional[str] = None,
    modalidade: Optional[str] = None,
    preco_min: Optional[float] = None,
    preco_max: Optional[float] = None,
    ipl_min: Optional[float] = None,
    aceita_fgts: Optional[bool] = None,
    aceita_financiamento: Optional[bool] = None,
    tem_analise: Optional[bool] = None,
    order_by: str = "ipl_score",
    order_dir: str = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    supabase = get_supabase()
    query = supabase.table("properties").select(
        "id,imovel_numero,uf,cidade,bairro,endereco,preco,valor_avaliacao,"
        "desconto_percentual,aceita_financiamento,aceita_fgts,modalidade,"
        "tipo_imovel,area_m2,quartos,status_ocupacao,ipl_score,ipl_score_margem,"
        "ipl_score_risco,ipl_classificacao,link_acesso,url_matricula,fotos,"
        "data_leilao,updated_at",
        count="exact",
    ).eq("ativo", True)

    if uf:
        query = query.eq("uf", uf.upper())
    if cidade:
        query = query.ilike("cidade", f"%{cidade}%")
    if modalidade:
        query = query.ilike("modalidade", f"%{modalidade}%")
    if preco_min is not None:
        query = query.gte("preco", preco_min)
    if preco_max is not None:
        query = query.lte("preco", preco_max)
    if ipl_min is not None:
        query = query.gte("ipl_score", ipl_min)
    if aceita_fgts is not None:
        query = query.eq("aceita_fgts", aceita_fgts)
    if aceita_financiamento is not None:
        query = query.eq("aceita_financiamento", aceita_financiamento)

    if order_by not in VALID_ORDER_FIELDS:
        order_by = "ipl_score"
    query = query.order(order_by, desc=(order_dir.lower() == "desc"), nullsfirst=False)

    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)

    try:
        result = query.execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na consulta: {str(e)}")

    total = result.count or 0

    return {
        "data": result.data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size) if total else 0,
    }


@router.get("/stats")
async def get_stats():
    supabase = get_supabase()
    result = supabase.table("properties").select(
        "uf,ipl_classificacao,preco,desconto_percentual",
        count="exact",
    ).eq("ativo", True).execute()

    data = result.data or []
    total = result.count or 0

    from collections import Counter
    ufs = Counter(p["uf"] for p in data)
    classificacoes = Counter(p.get("ipl_classificacao") for p in data if p.get("ipl_classificacao"))

    precos = [p["preco"] for p in data if p.get("preco")]
    descontos = [p["desconto_percentual"] for p in data if p.get("desconto_percentual")]

    return {
        "total_imoveis": total,
        "por_uf": dict(ufs.most_common(10)),
        "por_classificacao": dict(classificacoes),
        "preco_medio": round(sum(precos) / len(precos), 2) if precos else None,
        "desconto_medio": round(sum(descontos) / len(descontos), 2) if descontos else None,
    }


@router.get("/{property_id}")
async def get_property(property_id: str):
    supabase = get_supabase()
    result = supabase.table("properties").select("*").eq("id", property_id).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    analyses = supabase.table("property_analyses").select("*").eq("property_id", property_id).execute()
    legal = supabase.table("legal_checks").select("*").eq("property_id", property_id).execute()

    return {
        **result.data,
        "analyses": analyses.data or [],
        "legal_checks": legal.data or [],
    }
