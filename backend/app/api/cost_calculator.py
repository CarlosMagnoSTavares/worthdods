from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.total_cost_calculator import (
    calcular_custo_total,
    gerar_resumo_custos,
    CostInputs
)

router = APIRouter(prefix="/properties", tags=["cost-calculator"])


class CostCalculationRequest(BaseModel):
    """Request model for cost calculation."""
    preco_lance: float
    valor_avaliacao: float
    uf: str
    cidade: Optional[str] = None
    status_ocupacao: Optional[str] = None
    area_m2: Optional[float] = None
    idade_imovel_anos: Optional[int] = None
    condicao_imovel: Optional[str] = None
    dividas_iptu: float = 0.0
    dividas_condominio: float = 0.0
    dividas_outros: float = 0.0
    # Customizable rates
    taxa_comissao: Optional[float] = None
    taxa_itbi: Optional[float] = None
    taxa_registro: Optional[float] = None
    custo_evicao_base: Optional[float] = None


class CostCalculationResponse(BaseModel):
    """Response model for cost calculation."""
    preco_lance: float
    comissao_leilao: float
    itbi: float
    registro_cartorio: float
    custos_evicao: float
    orcamento_reforma: float
    dividas_pendentes: float
    custo_total: float
    valor_mercado: float
    margem_lucro_pct: float
    roi_indicador: str
    roi_cor: str
    resumo: dict


@router.post("/calculate-costs", response_model=CostCalculationResponse)
async def calculate_total_costs(request: CostCalculationRequest):
    """
    Calculate the total cost of purchasing an auction property.
    
    This endpoint calculates all fees, taxes, and hidden costs associated
    with buying a property at auction in Brazil.
    """
    # Create CostInputs from request
    inputs = CostInputs(
        preco_lance=request.preco_lance,
        valor_avaliacao=request.valor_avaliacao,
        uf=request.uf,
        cidade=request.cidade,
        status_ocupacao=request.status_ocupacao,
        area_m2=request.area_m2,
        idade_imovel_anos=request.idade_imovel_anos,
        condicao_imovel=request.condicao_imovel,
        dividas_iptu=request.dividas_iptu,
        dividas_condominio=request.dividas_condominio,
        dividas_outros=request.dividas_outros
    )
    
    # Apply custom rates if provided
    if request.taxa_comissao is not None:
        inputs.taxa_comissao = request.taxa_comissao
    if request.taxa_itbi is not None:
        inputs.taxa_itbi = request.taxa_itbi
    if request.taxa_registro is not None:
        inputs.taxa_registro = request.taxa_registro
    if request.custo_evicao_base is not None:
        inputs.custo_evicao_base = request.custo_evicao_base
    
    # Calculate costs
    breakdown = calcular_custo_total(inputs)
    resumo = gerar_resumo_custos(breakdown)
    
    return CostCalculationResponse(
        preco_lance=breakdown.preco_lance,
        comissao_leilao=breakdown.comissao_leilao,
        itbi=breakdown.itbi,
        registro_cartorio=breakdown.registro_cartorio,
        custos_evicao=breakdown.custos_evicao,
        orcamento_reforma=breakdown.orcamento_reforma,
        dividas_pendentes=breakdown.dividas_pendentes,
        custo_total=breakdown.custo_total,
        valor_mercado=breakdown.valor_mercado,
        margem_lucro_pct=breakdown.margem_lucro_pct,
        roi_indicador=breakdown.roi_indicador,
        roi_cor=breakdown.roi_cor,
        resumo=resumo
    )


@router.get("/property/{property_id}/costs")
async def get_property_costs(property_id: str):
    """
    Get cost calculation for a specific property from the database.
    
    This endpoint retrieves property data and calculates the total costs.
    """
    from app.database import get_supabase
    
    supabase = get_supabase()
    
    # Get property data
    result = supabase.table("properties").select("*").eq("id", property_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Property not found")
    
    prop = result.data[0]
    
    # Get debt analysis if available
    debt_data = {}
    analysis_result = supabase.table("property_analyses") \
        .select("*") \
        .eq("property_id", property_id) \
        .eq("tipo", "edital") \
        .execute()
    
    if analysis_result.data:
        analysis = analysis_result.data[0]
        # Extract debt information from analysis
        dividas = analysis.get("dividas", [])
        for divida in dividas:
            tipo = divida.get("tipo", "").lower()
            valor = divida.get("valor", 0)
            if "iptu" in tipo:
                debt_data["dividas_iptu"] = valor
            elif "condomínio" in tipo or "condominio" in tipo:
                debt_data["dividas_condominio"] = valor
            else:
                debt_data["dividas_outros"] = debt_data.get("dividas_outros", 0) + valor
    
    # Create CostInputs from property data
    inputs = CostInputs(
        preco_lance=prop.get("preco", 0),
        valor_avaliacao=prop.get("valor_avaliacao", 0) or prop.get("preco", 0) * 1.2,
        uf=prop.get("uf", ""),
        cidade=prop.get("cidade"),
        status_ocupacao=prop.get("status_ocupacao"),
        area_m2=prop.get("area_m2"),
        dividas_iptu=debt_data.get("dividas_iptu", 0),
        dividas_condominio=debt_data.get("dividas_condominio", 0),
        dividas_outros=debt_data.get("dividas_outros", 0)
    )
    
    # Calculate costs
    breakdown = calcular_custo_total(inputs)
    resumo = gerar_resumo_custos(breakdown)
    
    return {
        "property_id": property_id,
        "preco_lance": breakdown.preco_lance,
        "comissao_leilao": breakdown.comissao_leilao,
        "itbi": breakdown.itbi,
        "registro_cartorio": breakdown.registro_cartorio,
        "custos_evicao": breakdown.custos_evicao,
        "orcamento_reforma": breakdown.orcamento_reforma,
        "dividas_pendentes": breakdown.dividas_pendentes,
        "custo_total": breakdown.custo_total,
        "valor_mercado": breakdown.valor_mercado,
        "margem_lucro_pct": breakdown.margem_lucro_pct,
        "roi_indicador": breakdown.roi_indicador,
        "roi_cor": breakdown.roi_cor,
        "resumo": resumo
    }