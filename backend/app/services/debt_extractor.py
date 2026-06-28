"""
Extração de débitos e encumbrâncias de editais e matrículas.
Combina extração de PDF com análise de IA para identificar débitos
transferidos ao comprador em leilões imobiliários.
"""

import logging
from typing import Optional, List
from app.models.analysis import DividaItem, DividasResult

logger = logging.getLogger(__name__)


async def extract_debts_from_text(texto: str, tipo_documento: str = "auto") -> dict:
    """
    Extrai débitos de um texto de edital ou matrícula usando IA.
    
    Args:
        texto: Texto extraído do documento
        tipo_documento: "edital", "matricula" ou "auto" (detectar automaticamente)
    
    Returns:
        dict com resultado da extração ou erro
    """
    from app.services.ai_analyzer import analyze_document

    if not texto or len(texto.strip()) < 50:
        return {"erro": "Texto muito curto para análise de débitos"}

    resultado = await analyze_document(texto, "dividas")
    
    if not resultado:
        return {"erro": "IA retornou resposta vazia"}

    if resultado.get("erro"):
        return resultado

    return resultado


async def extract_debts_from_property(
    supabase, property_id: str
) -> Optional[dict]:
    """
    Extrai débitos de um imóvel usando seus documentos (edital/matricula).
    
    Args:
        supabase: Cliente Supabase
        property_id: ID do imóvel
    
    Returns:
        dict com resultado da extração ou None se não houver dados
    """
    from app.services.pdf_extractor import extract_pdf_text

    try:
        prop_result = (
            supabase.table("properties")
            .select("id,url_matricula,url_edital")
            .eq("id", property_id)
            .single()
            .execute()
        )
    except Exception as e:
        logger.error(f"Erro ao buscar imóvel {property_id}: {e}")
        return None

    if not prop_result.data:
        return None

    prop = prop_result.data
    textos = []

    # Tentar extrair de ambos os documentos
    for url_key, doc_tipo in [
        ("url_edital", "edital"),
        ("url_matricula", "matricula"),
    ]:
        url = prop.get(url_key)
        if not url:
            continue

        try:
            pdf_data = await extract_pdf_text(url)
            if pdf_data and pdf_data.get("texto"):
                textos.append((doc_tipo, pdf_data["texto"]))
        except Exception as e:
            logger.warning(f"Falha ao extrair {doc_tipo} para {property_id}: {e}")

    if not textos:
        return {"erro": "Nenhum documento disponível para extração de débitos"}

    # Combinar textos para análise conjunta
    texto_completo = "\n\n--- DOCUMENTO ---\n\n".join(
        [f"[{tipo.upper()}]\n{txt}" for tipo, txt in textos]
    )

    # Usar apenas os primeiros 30000 caracteres para não exceder limite do LLM
    resultado = await extract_debts_from_text(texto_completo[:30000])

    if resultado.get("erro"):
        return resultado

    # Enriquecer com dados do imóvel
    resultado["property_id"] = property_id
    resultado["documentos_analisados"] = [tipo for tipo, _ in textos]

    return resultado


def parse_dividas_from_analysis(analise: dict) -> DividasResult:
    """
    Converte o resultado da análise de débitos em modelo estruturado.
    
    Args:
        analise: Dict retornado pela IA
    
    Returns:
        DividasResult com dados estruturados
    """
    dividas_raw = analise.get("dividas", [])
    dividas = []

    for d in dividas_raw:
        try:
            divida = DividaItem(
                tipo=d.get("tipo", "OUTRO"),
                descricao=d.get("descricao", ""),
                valor_estimado=d.get("valor_estimado"),
                valor_texto=d.get("valor_texto", "Não informado"),
                periodo=d.get("periodo", "Não informado"),
                responsavel=d.get("responsavel", "NAO_INFORMADO"),
                severidade=d.get("severidade", "NAO_INFORMADO"),
                transferida_ao_comprador=d.get("transferida_ao_comprador", False),
                base_legal=d.get("base_legal", ""),
                clausula_documento=d.get("clausula_documento", ""),
                ocorrencia=d.get("ocorrencia", "NAO_ENCONTRADO"),
            )
            dividas.append(divida)
        except Exception as e:
            logger.warning(f"Erro ao parsear débito: {e}")
            continue

    return DividasResult(
        dividas=dividas,
        tem_iptu_pendente=analise.get("tem_iptu_pendente", False),
        tem_condominio_pendente=analise.get("tem_condominio_pendente", False),
        tem_contribuicao_melhoria=analise.get("tem_contribuicao_melhoria", False),
        tem_propter_rem=analise.get("tem_propter_rem", False),
        total_dividas_estimado=analise.get("total_dividas_estimado", 0.0),
        resumo_dividas=analise.get("resumo_dividas"),
        alerta_comprador=analise.get("alerta_comprador"),
    )


def calcular_risco_dividas(dividas_result: DividasResult) -> dict:
    """
    Calcula métricas de risco baseadas nos débitos extraídos.
    
    Returns:
        dict com score de risco e flags para o imóvel
    """
    dividas = dividas_result.dividas

    if not dividas:
        return {
            "risco_dividas_score": 0.0,
            "total_dividas_transferidas": 0,
            "valor_total_transferido": 0.0,
        }

    # Contar débitos transferidos ao comprador
    transferidas = [d for d in dividas if d.transferida_ao_comprador]
    total_transferido = sum(
        d.valor_estimado for d in transferidas if d.valor_estimado
    )

    # Calcular score de risco (0-10, 10 = maior risco)
    score = 0.0
    for d in transferidas:
        if d.severidade == "CRITICA":
            score += 3.0
        elif d.severidade == "ALTA":
            score += 2.0
        elif d.severidade == "MEDIA":
            score += 1.0
        elif d.severidade == "BAIXA":
            score += 0.5

    # Bonificação por tipos específicos
    if dividas_result.tem_iptu_pendente:
        score += 1.5
    if dividas_result.tem_condominio_pendente:
        score += 1.0
    if dividas_result.tem_propter_rem:
        score += 2.0

    score = min(10.0, score)

    return {
        "risco_dividas_score": round(score, 1),
        "total_dividas_transferidas": len(transferidas),
        "valor_total_transferido": round(total_transferido, 2),
    }
