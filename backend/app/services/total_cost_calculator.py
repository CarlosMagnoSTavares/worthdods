"""
Total Cost Calculator for Auction Properties

Calculates the total estimated cost of purchasing a property at auction,
including all fees, taxes, and hidden costs.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class CostBreakdown:
    """Breakdown of all costs associated with an auction property purchase."""
    preco_lance: float  # Winning bid price
    comissao_leilao: float  # Auctioneer commission (typically 5%)
    itbi: float  # ITBI (imposto de transmissão) - varies by municipality
    registro_cartorio: float  # Registration and notary fees
    custos_evicao: float  # Estimated eviction costs (if occupied)
    orcamento_reforma: float  # Estimated reform budget
    dividas_pendentes: float  # Outstanding debts (IPTU, condominium, etc.)
    custo_total: float  # Total estimated cost
    valor_mercado: float  # Market value comparison
    margem_lucro_pct: float  # Profit margin percentage
    roi_indicador: str  # ROI indicator (Excelente, Bom, Regular, Ruim, Crítico)


@dataclass
class CostInputs:
    """Input parameters for cost calculation."""
    preco_lance: float
    valor_avaliacao: float
    uf: str
    cidade: Optional[str] = None
    status_ocupacao: Optional[str] = None
    area_m2: Optional[float] = None
    idade_imovel_anos: Optional[int] = None
    condicao_imovel: Optional[str] = None  # "bom", "regular", "ruim"
    dividas_iptu: float = 0.0
    dividas_condominio: float = 0.0
    dividas_outros: float = 0.0
    # Customizable rates (defaults based on typical Brazilian values)
    taxa_comissao: float = 0.05  # 5% auctioneer commission
    taxa_itbi: float = 0.03  # 3% ITBI (varies by municipality)
    taxa_registro: float = 0.02  # 2% registration and notary fees
    custo_evicao_base: float = 12000.0  # R$ 12,000 base eviction cost


def calcular_comissao_leilao(preco_lance: float, taxa: float = 0.05) -> float:
    """Calculate auctioneer commission."""
    return round(preco_lance * taxa, 2)


def calcular_itbi(preco_lance: float, taxa: float = 0.03) -> float:
    """Calculate ITBI (imposto de transmissão imobiliária)."""
    return round(preco_lance * taxa, 2)


def calcular_registro_cartorio(preco_lance: float, taxa: float = 0.02) -> float:
    """Calculate registration and notary fees."""
    return round(preco_lance * taxa, 2)


def calcular_custos_evicao(
    status_ocupacao: Optional[str],
    custo_base: float = 12000.0,
    risco_evicao: bool = False
) -> float:
    """Calculate estimated eviction costs based on occupancy status."""
    if status_ocupacao == "desocupado" and not risco_evicao:
        return 0.0
    
    # If occupied or eviction risk exists, estimate costs
    # Base cost includes legal fees, official costs, and timeline
    if risco_evicao:
        return round(custo_base * 1.5, 2)  # Higher cost for confirmed eviction risk
    elif status_ocupacao == "ocupado":
        return round(custo_base, 2)
    else:
        return 0.0


def calcular_orcamento_reforma(
    area_m2: Optional[float],
    idade_imovel_anos: Optional[int],
    condicao_imovel: Optional[str] = None,
    preco_lance: float = 0.0
) -> float:
    """Calculate estimated reform budget based on property characteristics."""
    if not area_m2 or area_m2 <= 0:
        # If no area info, use percentage of property value
        return round(preco_lance * 0.20, 2)  # Default 20% of property value
    
    # Cost per square meter for reforms in Brazil (approximate)
    custo_m2_base = 800.0  # R$ 800/m² for basic reforms
    
    # Adjust based on property age
    fator_idade = 1.0
    if idade_imovel_anos:
        if idade_imovel_anos > 30:
            fator_idade = 1.5  # Older properties need more work
        elif idade_imovel_anos > 20:
            fator_idade = 1.3
        elif idade_imovel_anos > 10:
            fator_idade = 1.1
    
    # Adjust based on condition
    fator_condicao = 1.0
    if condicao_imovel:
        condicao_lower = condicao_imovel.lower()
        if "ruim" in condicao_lower or "péssimo" in condicao_lower:
            fator_condicao = 1.5
        elif "regular" in condicao_lower:
            fator_condicao = 1.2
        elif "bom" in condicao_lower:
            fator_condicao = 1.0
        elif "ótimo" in condicao_lower or "excelente" in condicao_lower:
            fator_condicao = 0.8
    
    custo_total = area_m2 * custo_m2_base * fator_idade * fator_condicao
    return round(custo_total, 2)


def calcular_dividas_pendentes(
    dividas_iptu: float = 0.0,
    dividas_condominio: float = 0.0,
    dividas_outros: float = 0.0
) -> float:
    """Calculate total outstanding debts."""
    return round(dividas_iptu + dividas_condominio + dividas_outros, 2)


def calcular_custo_total(inputs: CostInputs) -> CostBreakdown:
    """Calculate the total cost of purchasing an auction property."""
    
    # Calculate individual cost components
    comissao = calcular_comissao_leilao(inputs.preco_lance, inputs.taxa_comissao)
    itbi = calcular_itbi(inputs.preco_lance, inputs.taxa_itbi)
    registro = calcular_registro_cartorio(inputs.preco_lance, inputs.taxa_registro)
    evicao = calcular_custos_evicao(
        inputs.status_ocupacao,
        inputs.custo_evicao_base,
        risco_evicao=inputs.dividas_outros > 0  # Assume eviction risk if there are other debts
    )
    reforma = calcular_orcamento_reforma(
        inputs.area_m2,
        inputs.idade_imovel_anos,
        inputs.condicao_imovel,
        inputs.preco_lance
    )
    dividas = calcular_dividas_pendentes(
        inputs.dividas_iptu,
        inputs.dividas_condominio,
        inputs.dividas_outros
    )
    
    # Calculate total cost
    custo_total = inputs.preco_lance + comissao + itbi + registro + evicao + reforma + dividas
    
    # Calculate profit margin
    valor_mercado = inputs.valor_avaliacao if inputs.valor_avaliacao > 0 else inputs.preco_lance * 1.2
    margem_lucro = ((valor_mercado - custo_total) / valor_mercado) * 100 if valor_mercado > 0 else 0
    
    # Determine ROI indicator
    roi_indicador = classificar_roi(margem_lucro)
    
    return CostBreakdown(
        preco_lance=inputs.preco_lance,
        comissao_leilao=comissao,
        itbi=itbi,
        registro_cartorio=registro,
        custos_evicao=evicao,
        orcamento_reforma=reforma,
        dividas_pendentes=dividas,
        custo_total=custo_total,
        valor_mercado=valor_mercado,
        margem_lucro_pct=round(margem_lucro, 2),
        roi_indicador=roi_indicador
    )


def classificar_roi(margem_lucro_pct: float) -> str:
    """Classify ROI based on profit margin percentage."""
    if margem_lucro_pct >= 30:
        return "Excelente"
    elif margem_lucro_pct >= 20:
        return "Bom"
    elif margem_lucro_pct >= 10:
        return "Regular"
    elif margem_lucro_pct >= 0:
        return "Ruim"
    else:
        return "Crítico"


def roi_cor(classificacao: str) -> str:
    """Get color code for ROI classification."""
    cores = {
        "Excelente": "#1a6b3c",
        "Bom": "#4a7c2f",
        "Regular": "#b8860b",
        "Ruim": "#c0642b",
        "Crítico": "#c0392b",
    }
    return cores.get(classificacao, "#6b6055")


def formatar_moeda(valor: float) -> str:
    """Format value as Brazilian Real currency."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_resumo_custos(breakdown: CostBreakdown) -> Dict[str, Any]:
    """Generate a summary of the cost breakdown."""
    return {
        "preco_lance": formatar_moeda(breakdown.preco_lance),
        "comissao_leilao": formatar_moeda(breakdown.comissao_leilao),
        "itbi": formatar_moeda(breakdown.itbi),
        "registro_cartorio": formatar_moeda(breakdown.registro_cartorio),
        "custos_evicao": formatar_moeda(breakdown.custos_evicao),
        "orcamento_reforma": formatar_moeda(breakdown.orcamento_reforma),
        "dividas_pendentes": formatar_moeda(breakdown.dividas_pendentes),
        "custo_total": formatar_moeda(breakdown.custo_total),
        "valor_mercado": formatar_moeda(breakdown.valor_mercado),
        "margem_lucro_pct": f"{breakdown.margem_lucro_pct:.1f}%",
        "roi_indicador": breakdown.roi_indicador,
        "roi_cor": roi_cor(breakdown.roi_indicador)
    }