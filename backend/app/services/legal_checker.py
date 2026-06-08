"""
Consulta processos judiciais via CNJ Datajud API pública.
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


async def search_processes_by_property(
    property_id: str, uf: str, imovel_numero: str
) -> list[dict]:
    tribunais = UF_TRIBUNAIS.get(uf.upper(), [f"tj{uf.lower()}"])
    results = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for tribunal in tribunais[:2]:
            try:
                resp = await client.post(
                    f"{CNJ_BASE_URL}/api_publica_{tribunal}/_search",
                    headers={
                        "Authorization": f"APIKey {settings.CNJ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "query": {
                            "bool": {
                                "should": [
                                    {"match": {"assunto": imovel_numero}},
                                    {"match_phrase": {"assunto": "alienação fiduciária"}},
                                    {"match_phrase": {"assunto": "busca e apreensão"}},
                                ]
                            }
                        },
                        "size": 5,
                        "_source": [
                            "numeroProcesso", "classe", "assunto",
                            "dataAjuizamento", "grau", "movimentos",
                        ],
                    },
                )

                if resp.status_code == 200:
                    data = resp.json()
                    hits = data.get("hits", {}).get("hits", [])
                    for hit in hits:
                        src = hit.get("_source", {})
                        classe = src.get("classe", {})
                        results.append({
                            "property_id": property_id,
                            "tribunal": tribunal.upper(),
                            "numero_processo": src.get("numeroProcesso"),
                            "classe_processual": (
                                classe.get("nome") if isinstance(classe, dict) else str(classe)
                            ),
                            "assunto": str(src.get("assunto", ""))[:500],
                            "data_ajuizamento": src.get("dataAjuizamento"),
                            "grau": src.get("grau"),
                            "raw_data": src,
                        })
            except Exception as e:
                logger.warning(f"CNJ {tribunal}: {e}")
                continue

    return results
