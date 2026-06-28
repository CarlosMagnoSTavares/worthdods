"""
Serviço de análise de risco de ocupação para imóveis em leilão.
Extrai sinais de ocupação do edital/matrícula e gera score de risco
com estimativa de prazo de desocupação e custos.
"""

import logging
import re
from typing import Optional, List
from app.models.analysis import DividaItem

logger = logging.getLogger(__name__)

# Palavras-chave para detecção de ocupação
OCUPACAO_SIGNALS = {
    "desocupado": {
        "nivel": "BAIXO",
        "peso": 0.0,
        "descricao": "Imóvel declarado desocupado",
    },
    "vago": {
        "nivel": "BAIXO",
        "peso": 0.0,
        "descricao": "Imóvel vago",
    },
    "imissão na posse": {
        "nivel": "BAIXO",
        "peso": 0.0,
        "descricao": "Imissão na posse prevista",
    },
    "imissao na posse": {
        "nivel": "BAIXO",
        "peso": 0.0,
        "descricao": "Imissão na posse prevista",
    },
    "ocupado": {
        "nivel": "ALTO",
        "peso": 3.0,
        "descricao": "Imóvel declarado ocupado",
    },
    "residência atual": {
        "nivel": "ALTO",
        "peso": 2.5,
        "descricao": "Imóvel é residência atual do proprietário",
    },
    "residencia atual": {
        "nivel": "ALTO",
        "peso": 2.5,
        "descricao": "Imóvel é residência atual do proprietário",
    },
    "morador": {
        "nivel": "MEDIO",
        "peso": 2.0,
        "descricao": "Presença de morador mencionada",
    },
    "inquilino": {
        "nivel": "MEDIO",
        "peso": 2.0,
        "descricao": "Inquilino no imóvel",
    },
    "locação": {
        "nivel": "MEDIO",
        "peso": 1.5,
        "descricao": "Imóvel locado",
    },
    "locacao": {
        "nivel": "MEDIO",
        "peso": 1.5,
        "descricao": "Imóvel locado",
    },
    "aluguel": {
        "nivel": "MEDIO",
        "peso": 1.5,
        "descricao": "Imóvel com renda de aluguel",
    },
    "desocupação": {
        "nivel": "ALTO",
        "peso": 3.5,
        "descricao": "Necessita desocupação judicial",
    },
    "desocupacao": {
        "nivel": "ALTO",
        "peso": 3.5,
        "descricao": "Necessita desocupação judicial",
    },
    "reintegração de posse": {
        "nivel": "CRITICO",
        "peso": 4.0,
        "descricao": "Reintegração de posse necessária",
    },
    "reintegracao de posse": {
        "nivel": "CRITICO",
        "peso": 4.0,
        "descricao": "Reintegração de posse necessária",
    },
    "busca e apreensão": {
        "nivel": "CRITICO",
        "peso": 4.0,
        "descricao": "Busca e apreensão em andamento",
    },
    "execução de despejo": {
        "nivel": "ALTO",
        "peso": 3.5,
        "descricao": "Execução de despejo em andamento",
    },
    "execucao de despejo": {
        "nivel": "ALTO",
        "peso": 3.5,
        "descricao": "Execução de despejo em andamento",
    },
}

# Custo estimado de desocupação (valores em R$)
CUSTO_DESLOCACAO = {
    "honorarios_advocaticios": {"min": 5000, "max": 15000, "label": "Honorários advocatícios"},
    "custas_judiciais": {"min": 2000, "max": 5000, "label": "Custas judiciais"},
    "desocupacao_fisica": {"min": 1000, "max": 3000, "label": "Desocupação física"},
    "indenizacao": {"min": 5000, "max": 20000, "label": "Indenização (se aplicável)"},
    "reforma_pos_desocupacao": {"min": 5000, "max": 30000, "label": "Reforma pós-desocupação"},
}

# Prazo estimado de desocupação (em meses)
PRAZO_DESLOCACAO = {
    "imissao_posse": {"min": 1, "max": 3, "label": "Com imissão na posse"},
    "desocupacao_voluntaria": {"min": 1, "max": 6, "label": "Desocupação voluntária"},
    "desocupacao_judicial": {"min": 6, "max": 24, "label": "Desocupação judicial"},
    "reintegracao_posse": {"min": 12, "max": 36, "label": "Reintegração de posse"},
}


def extract_occupancy_signals(texto: str) -> List[dict]:
    """
    Extrai sinais de ocupação do texto do edital ou matrícula.
    
    Returns:
        Lista de sinais encontrados com nível de risco e descrição
    """
    if not texto:
        return []
    
    texto_lower = texto.lower()
    signals_found = []
    
    for keyword, info in OCUPACAO_SIGNALS.items():
        if keyword in texto_lower:
            signals_found.append({
                "sinal": keyword,
                "nivel": info["nivel"],
                "peso": info["peso"],
                "descricao": info["descricao"],
            })
    
    return signals_found


def calculate_occupancy_risk(
    signals: List[dict],
    status_ocupacao: Optional[str] = None,
    texto: Optional[str] = None,
) -> dict:
    """
    Calcula o score de risco de ocupação baseado nos sinais extraídos.
    
    Returns:
        dict com nivel_risco, score, prazo estimado e custo estimado
    """
    if not signals:
        # Sem sinais = usar status do edital se disponível
        if status_ocupacao:
            if status_ocupacao == "DESOCUPADO":
                return {
                    "nivel_risco": "BAIXO",
                    "score": 0.0,
                    "prazo_estimado": PRAZO_DESLOCACAO["imissao_posse"],
                    "custo_estimado": {"min": 0, "max": 2000},
                    "sinais": [],
                    "resumo": "Imóvel desocupado. Baixo risco de desocupação.",
                }
            elif status_ocupacao == "OCUPADO":
                return {
                    "nivel_risco": "ALTO",
                    "score": 3.0,
                    "prazo_estimado": PRAZO_DESLOCACAO["desocupacao_judicial"],
                    "custo_estimado": {"min": 12000, "max": 43000},
                    "sinais": [],
                    "resumo": "Imóvel ocupado. Risco alto de desocupação judicial.",
                }
        return {
            "nivel_risco": "DESCONHECIDO",
            "score": 1.5,
            "prazo_estimado": {"min": 1, "max": 12, "label": "Não determinado"},
            "custo_estimado": {"min": 5000, "max": 25000},
            "sinais": [],
            "resumo": "Status de ocupação não determinado.",
        }
    
    # Calcular score baseado nos sinais
    total_peso = sum(s["peso"] for s in signals)
    nivel_max = max(signals, key=lambda s: s["peso"])
    
    # Determinar nível geral
    if nivel_max["nivel"] == "CRITICO":
        nivel_geral = "CRITICO"
    elif nivel_max["nivel"] == "ALTO":
        nivel_geral = "ALTO"
    elif nivel_max["nivel"] == "MEDIO":
        nivel_geral = "MEDIO"
    else:
        nivel_geral = "BAIXO"
    
    # Determinar prazo baseado no sinal mais grave
    if any(s["sinal"] in ["reintegração de posse", "reintegracao de posse"] for s in signals):
        prazo = PRAZO_DESLOCACAO["reintegracao_posse"]
        custo = {
            "min": CUSTO_DESLOCACAO["honorarios_advocaticios"]["min"] + CUSTO_DESLOCACAO["custas_judiciais"]["min"] + CUSTO_DESLOCACAO["indenizacao"]["min"],
            "max": CUSTO_DESLOCACAO["honorarios_advocaticios"]["max"] + CUSTO_DESLOCACAO["custas_judiciais"]["max"] + CUSTO_DESLOCACAO["indenizacao"]["max"],
        }
    elif any(s["sinal"] in ["desocupação", "desocupacao", "execução de despejo", "execucao de despejo"] for s in signals):
        prazo = PRAZO_DESLOCACAO["desocupacao_judicial"]
        custo = {
            "min": CUSTO_DESLOCACAO["honorarios_advocaticios"]["min"] + CUSTO_DESLOCACAO["custas_judiciais"]["min"],
            "max": CUSTO_DESLOCACAO["honorarios_advocaticios"]["max"] + CUSTO_DESLOCACAO["custas_judiciais"]["max"],
        }
    elif any(s["sinal"] in ["imissão na posse", "imissao na posse"] for s in signals):
        prazo = PRAZO_DESLOCACAO["imissao_posse"]
        custo = {"min": 0, "max": 2000}
    else:
        prazo = PRAZO_DESLOCACAO["desocupacao_voluntaria"]
        custo = {
            "min": CUSTO_DESLOCACAO["honorarios_advocaticios"]["min"],
            "max": CUSTO_DESLOCACAO["honorarios_advocaticios"]["max"],
        }
    
    # Gerar resumo
    sinais_desc = ", ".join([s["descricao"] for s in signals[:3]])
    resumo = f"Sinais encontrados: {sinais_desc}. "
    if nivel_geral in ["ALTO", "CRITICO"]:
        resumo += f"Risco {nivel_geral.lower()} de desocupação. Prazo estimado: {prazo['min']}-{prazo['max']} meses. Custo estimado: R$ {custo['min']:,}-{custo['max']:,}."
    else:
        resumo += f"Risco {nivel_geral.lower()} de desocupação."
    
    return {
        "nivel_risco": nivel_geral,
        "score": min(10.0, total_peso),
        "prazo_estimado": prazo,
        "custo_estimado": custo,
        "sinais": signals,
        "resumo": resumo,
    }


def get_occupancy_risk_label(nivel: str) -> str:
    """Retorna label legível para o nível de risco."""
    labels = {
        "BAIXO": "Baixo Risco",
        "MEDIO": "Médio Risco",
        "ALTO": "Alto Risco",
        "CRITICO": "Risco Crítico",
        "DESCONHECIDO": "Desconhecido",
    }
    return labels.get(nivel, nivel)


def get_occupancy_risk_color(nivel: str) -> str:
    """Retorna cor CSS para o nível de risco."""
    cores = {
        "BAIXO": "#1a6b3c",
        "MEDIO": "#b8860b",
        "ALTO": "#e65100",
        "CRITICO": "#c0392b",
        "DESCONHECIDO": "#6b6055",
    }
    return cores.get(nivel, "#6b6055")
