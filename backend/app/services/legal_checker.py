"""
Consulta processos judiciais via CNJ Datajud API pública.
Cobre: execuções extrajudiciais, cotas condominiais, IPTU, penhoras,
hipotecas, alienação fiduciária, busca e apreensão.
"""

import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

CNJ_BASE_URL = "https://api-publica.datajud.cnj.jus.br"

UF_TRIBUNAIS = {
    "SP": ["tjsp", "trf3"],
    "RJ": ["tjrj", "trf2"],
    "MG": ["tjmg", "trf6"],
    "RS": ["tjrs", "trf4"],
    "PR": ["tjpr", "trf4"],
    "SC": ["tjsc", "trf4"],
    "BA": ["tjba", "trf1"],
    "GO": ["tjgo", "trf1"],
    "PE": ["tjpe", "trf5"],
    "CE": ["tjce", "trf5"],
    "MA": ["tjma", "trf1"],
    "PA": ["tjpa", "trf1"],
    "ES": ["tjes", "trf2"],
    "RN": ["tjrn", "trf5"],
    "MT": ["tjmt", "trf1"],
    "MS": ["tjms", "trf3"],
    "DF": ["tjdft", "trf1"],
    "AM": ["tjam", "trf1"],
    "PI": ["tjpi", "trf1"],
    "AL": ["tjal", "trf5"],
    "SE": ["tjse", "trf5"],
    "PB": ["tjpb", "trf5"],
    "RO": ["tjro", "trf1"],
    "TO": ["tjto", "trf1"],
    "AC": ["tjac", "trf1"],
    "AP": ["tjap", "trf1"],
    "RR": ["tjrr", "trf1"],
}

# Assuntos CNJ relevantes para risco do comprador em leilão
ASSUNTOS_RISCO = [
    "alienação fiduciária",
    "busca e apreensão",
    "cotas condominiais",
    "cota condominial",
    "execução de título extrajudicial",
    "execução fiscal",
    "penhora",
    "hipoteca",
    "IPTU",
    "dívida ativa",
    "imissão na posse",
    "reintegração de posse",
    "usucapião",
    "anulação de arrematação",
    "nulidade de leilão",
    "evicção",
]

# Classificação de severidade por tipo de assunto
SEVERIDADE_MAP = {
    "alienação fiduciária": "ALTA",
    "busca e apreensão": "ALTA",
    "cotas condominiais": "ALTA",
    "cota condominial": "ALTA",
    "execução de título extrajudicial": "ALTA",
    "execução fiscal": "ALTA",
    "penhora": "ALTA",
    "hipoteca": "MEDIA",
    "IPTU": "MEDIA",
    "dívida ativa": "MEDIA",
    "imissão na posse": "CRITICA",
    "reintegração de posse": "CRITICA",
    "usucapião": "CRITICA",
    "anulação de arrematação": "CRITICA",
    "nulidade de leilão": "CRITICA",
    "evicção": "CRITICA",
}


def _classify_severity(assunto_text: str) -> str:
    text_lower = assunto_text.lower()
    for keyword, severity in SEVERIDADE_MAP.items():
        if keyword.lower() in text_lower:
            return severity
    return "MEDIA"


def _classify_tipo(assunto_text: str) -> str:
    text_lower = assunto_text.lower()
    if any(k in text_lower for k in ["cotas condominiais", "cota condominial", "condomínio"]):
        return "DIVIDA_CONDOMINIO"
    if any(k in text_lower for k in ["iptu", "execução fiscal", "dívida ativa"]):
        return "DIVIDA_IPTU"
    if any(k in text_lower for k in ["penhora"]):
        return "PENHORA"
    if any(k in text_lower for k in ["hipoteca"]):
        return "HIPOTECA"
    if any(k in text_lower for k in ["alienação fiduciária", "busca e apreensão"]):
        return "ALIENACAO_FIDUCIARIA"
    if any(k in text_lower for k in ["imissão", "reintegração", "usucapião"]):
        return "EVICAO"
    if any(k in text_lower for k in ["anulação", "nulidade", "evicção"]):
        return "EVICAO"
    return "PROCESSO_JUDICIAL"


async def _query_tribunal(
    client: httpx.AsyncClient,
    tribunal: str,
    query_body: dict,
    property_id: str,
) -> list[dict]:
    results = []
    try:
        resp = await client.post(
            f"{CNJ_BASE_URL}/api_publica_{tribunal}/_search",
            headers={
                "Authorization": f"APIKey {settings.CNJ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=query_body,
        )
        if resp.status_code == 200:
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            for hit in hits:
                src = hit.get("_source", {})
                classe = src.get("classe", {})
                assunto_raw = src.get("assunto", "")
                assunto_str = str(assunto_raw)[:500]

                results.append({
                    "property_id": property_id,
                    "tribunal": tribunal.upper(),
                    "numero_processo": src.get("numeroProcesso"),
                    "classe_processual": (
                        classe.get("nome") if isinstance(classe, dict) else str(classe)
                    ),
                    "assunto": assunto_str,
                    "tipo_risco": _classify_tipo(assunto_str),
                    "severidade": _classify_severity(assunto_str),
                    "data_ajuizamento": src.get("dataAjuizamento"),
                    "grau": src.get("grau"),
                    "raw_data": src,
                })
    except Exception as e:
        logger.warning(f"CNJ {tribunal}: {e}")
    return results


async def search_processes_by_property(
    property_id: str, uf: str, imovel_numero: str,
    endereco: str = "", proprietario: str = "",
) -> list[dict]:
    tribunais = UF_TRIBUNAIS.get(uf.upper(), [f"tj{uf.lower()}"])
    results = []

    # Query 1: por número do imóvel + termos de risco relevantes
    should_clauses = [{"match": {"assunto": imovel_numero}}] if imovel_numero else []
    for assunto in ASSUNTOS_RISCO:
        should_clauses.append({"match_phrase": {"assunto": assunto}})

    query_body_imovel = {
        "query": {
            "bool": {
                "should": should_clauses,
                "minimum_should_match": 1,
            }
        },
        "size": 10,
        "_source": [
            "numeroProcesso", "classe", "assunto",
            "dataAjuizamento", "grau", "movimentos", "partes",
        ],
    }

    # Query 2: por endereço do imóvel (se disponível)
    query_body_endereco = None
    if endereco and len(endereco) > 10:
        query_body_endereco = {
            "query": {
                "bool": {
                    "must": [
                        {"match_phrase": {"assunto": word}}
                        for word in endereco.split()[:3]  # primeiras 3 palavras do endereço
                        if len(word) > 4
                    ][:2]  # no máximo 2 must clauses
                }
            },
            "size": 5,
            "_source": [
                "numeroProcesso", "classe", "assunto",
                "dataAjuizamento", "grau", "movimentos",
            ],
        }

    seen_processos = set()

    async with httpx.AsyncClient(timeout=30.0) as client:
        for tribunal in tribunais[:2]:
            tribunal_results = await _query_tribunal(
                client, tribunal, query_body_imovel, property_id
            )
            for r in tribunal_results:
                key = (r["tribunal"], r["numero_processo"])
                if key not in seen_processos:
                    seen_processos.add(key)
                    results.append(r)

            if query_body_endereco and len(query_body_endereco["query"]["bool"].get("must", [])) >= 1:
                endereco_results = await _query_tribunal(
                    client, tribunal, query_body_endereco, property_id
                )
                for r in endereco_results:
                    key = (r["tribunal"], r["numero_processo"])
                    if key not in seen_processos:
                        seen_processos.add(key)
                        results.append(r)

    return results


def summarize_legal_risks(legal_checks: list[dict]) -> dict:
    """Sumariza os riscos jurídicos para exibição no frontend."""
    if not legal_checks:
        return {
            "total_processos": 0,
            "tem_risco_critico": False,
            "tipos_risco": [],
            "score_juridico": 10.0,
            "resumo": "Nenhum processo judicial identificado.",
        }

    tipos = set()
    tem_critico = False
    deducao = 0.0

    deducoes_por_tipo = {
        "EVICAO": 4.0,
        "DIVIDA_CONDOMINIO": 2.5,
        "DIVIDA_IPTU": 2.0,
        "PENHORA": 2.0,
        "ALIENACAO_FIDUCIARIA": 1.5,
        "HIPOTECA": 1.0,
        "PROCESSO_JUDICIAL": 1.0,
    }

    for check in legal_checks:
        tipo = check.get("tipo_risco", "PROCESSO_JUDICIAL")
        tipos.add(tipo)
        severidade = check.get("severidade", "MEDIA")
        if severidade == "CRITICA":
            tem_critico = True
        mult = {"BAIXA": 0.5, "MEDIA": 1.0, "ALTA": 1.3, "CRITICA": 1.5}.get(severidade, 1.0)
        deducao += deducoes_por_tipo.get(tipo, 1.0) * mult

    score = max(0.0, round(10.0 - deducao, 1))

    return {
        "total_processos": len(legal_checks),
        "tem_risco_critico": tem_critico,
        "tipos_risco": list(tipos),
        "score_juridico": score,
        "resumo": f"{len(legal_checks)} processo(s) identificado(s): {', '.join(tipos)}.",
    }
