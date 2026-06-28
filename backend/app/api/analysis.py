from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging
from app.database import get_supabase
from app.services.legal_checker import summarize_legal_risks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/properties", tags=["analysis"])


def _save_error(supabase, property_id: str, tipo: str, msg: str) -> None:
    try:
        supabase.table("property_analyses").upsert(
            {
                "property_id": property_id,
                "tipo": tipo,
                "erro_analise": msg[:1000],
            },
            on_conflict="property_id,tipo",
        ).execute()
    except Exception as e:
        logger.error(f"Falha ao salvar erro_analise {tipo}/{property_id}: {e}")


async def _analyze_doc_for_property(supabase, prop: dict, tipo: str) -> Optional[float]:
    """Roda extração + IA para matricula ou edital. Retorna score_risco ou None."""
    from app.services.pdf_extractor import extract_pdf_text
    from app.services.ai_analyzer import analyze_document
    from app.services.ipl_calculator import score_risco_from_analysis

    property_id = prop["id"]
    url_key = "url_matricula" if tipo == "matricula" else "url_edital"
    url = prop.get(url_key)
    if not url:
        return None

    logger.info(f"[{property_id}] Analisando {tipo}: {url}")
    try:
        pdf_data = await extract_pdf_text(url)
    except Exception as e:
        logger.error(f"[{property_id}] extract_pdf_text {tipo} falhou: {e}")
        _save_error(supabase, property_id, tipo, f"Falha ao baixar/extrair PDF: {e}")
        return None

    if not pdf_data or not pdf_data.get("texto"):
        reason = (pdf_data or {}).get("erro", "PDF indisponível")
        _save_error(supabase, property_id, tipo, f"{reason} ({url})")
        return None

    try:
        resultado = await analyze_document(pdf_data["texto"], tipo)
    except Exception as e:
        logger.exception(f"[{property_id}] analyze_document {tipo} crashou: {e}")
        _save_error(supabase, property_id, tipo, f"Erro inesperado na IA: {e}")
        return None

    if not resultado:
        _save_error(supabase, property_id, tipo, "IA retornou resposta vazia")
        return None

    if resultado.get("erro"):
        _save_error(supabase, property_id, tipo, resultado["erro"])
        return None

    analise = resultado["resultado"]
    sr = score_risco_from_analysis(analise)

    row = {
        "property_id": property_id,
        "tipo": tipo,
        "texto_extraido": pdf_data["texto"][:10000],
        "paginas_extraidas": pdf_data.get("paginas"),
        "resumo_executivo": analise.get("resumo_executivo"),
        "recomendacao": analise.get("recomendacao"),
        "nivel_risco": analise.get("nivel_risco"),
        "risco_evicao": analise.get("risco_evicao", False),
        "riscos_detalhados": analise.get("riscos", []),
        "dividas": analise.get("dividas", []),
        "pontos_positivos": analise.get("pontos_positivos", []),
        "score_risco": sr,
        "modelo_ia": resultado.get("modelo"),
        "tokens_usados": resultado.get("tokens"),
        "erro_analise": None,
    }
    if tipo == "edital":
        row.update({
            "risco_divida_iptu": analise.get("risco_divida_iptu", False),
            "risco_divida_condominio": analise.get("risco_divida_condominio", False),
            "risco_ocupacao": analise.get("risco_ocupacao", False),
            "risco_processo_judicial": analise.get("risco_processo_judicial", False),
            "risco_irregularidade": analise.get("risco_irregularidade", False),
            "risco_ambiental": analise.get("risco_ambiental", False),
        })

    try:
        supabase.table("property_analyses").upsert(row, on_conflict="property_id,tipo").execute()
    except Exception as e:
        logger.error(f"[{property_id}] Erro ao salvar análise {tipo}: {e}")
        _save_error(supabase, property_id, tipo, f"Erro ao salvar resultado: {e}")
        return None

    return sr


async def _extract_debts_for_property(supabase, prop: dict) -> Optional[dict]:
    """Roda extração de débitos de edital/matricula. Retorna dict com resultado ou None."""
    from app.services.debt_extractor import (
        extract_debts_from_property,
        parse_dividas_from_analysis,
        calcular_risco_dividas,
    )

    property_id = prop["id"]

    try:
        resultado = await extract_debts_from_property(supabase, property_id)
    except Exception as e:
        logger.error(f"[{property_id}] extract_debts falhou: {e}")
        _save_error(supabase, property_id, "dividas", f"Falha na extração de débitos: {e}")
        return None

    if not resultado:
        _save_error(supabase, property_id, "dividas", "Extração de débitos retornou vazio")
        return None

    if resultado.get("erro"):
        _save_error(supabase, property_id, "dividas", resultado["erro"])
        return None

    # Parsear resultado em modelo estruturado
    dividas_result = parse_dividas_from_analysis(resultado["resultado"])
    risco = calcular_risco_dividas(dividas_result)

    # Salvar no banco
    row = {
        "property_id": property_id,
        "tipo": "dividas",
        "dividas": [d.model_dump() for d in dividas_result.dividas],
        "tem_iptu_pendente": dividas_result.tem_iptu_pendente,
        "tem_condominio_pendente": dividas_result.tem_condominio_pendente,
        "tem_contribuicao_melhoria": dividas_result.tem_contribuicao_melhoria,
        "tem_propter_rem": dividas_result.tem_propter_rem,
        "total_dividas_estimado": dividas_result.total_dividas_estimado,
        "resumo_dividas": dividas_result.resumo_dividas,
        "alerta_comprador": dividas_result.alerta_comprador,
        "risco_dividas_score": risco["risco_dividas_score"],
        "total_dividas_transferidas": risco["total_dividas_transferidas"],
        "valor_total_transferido": risco["valor_total_transferido"],
        "modelo_ia": resultado.get("modelo"),
        "tokens_usados": resultado.get("tokens"),
        "erro_analise": None,
    }

    try:
        supabase.table("property_analyses").upsert(row, on_conflict="property_id,tipo").execute()
    except Exception as e:
        logger.error(f"[{property_id}] Erro ao salvar débitos: {e}")
        _save_error(supabase, property_id, "dividas", f"Erro ao salvar: {e}")
        return None

    logger.info(
        f"[{property_id}] Débitos extraídos: {len(dividas_result.dividas)} itens, "
        f"risco={risco['risco_dividas_score']}, "
        f"transferidos={risco['total_dividas_transferidas']}"
    )
    return risco


async def _analyze_occupancy_risk(supabase, prop: dict) -> None:
    """Analisa risco de ocupação do imóvel baseado nos sinais extraídos."""
    from app.services.pdf_extractor import extract_pdf_text
    from app.services.occupancy_risk import (
        extract_occupancy_signals,
        calculate_occupancy_risk,
    )

    property_id = prop["id"]

    # Buscar análise de edital existente para usar status_ocupacao
    try:
        edital_analysis = (
            supabase.table("property_analyses")
            .select("status_ocupacao, texto_extraido")
            .eq("property_id", property_id)
            .eq("tipo", "edital")
            .single()
            .execute()
        )
        status_ocupacao = edital_analysis.data.get("status_ocupacao") if edital_analysis.data else None
        texto_edital = edital_analysis.data.get("texto_extraido") if edital_analysis.data else None
    except Exception:
        status_ocupacao = None
        texto_edital = None

    # Se não temos texto do edital, tentar extrair
    if not texto_edital:
        url_edital = prop.get("url_edital")
        if url_edital:
            try:
                pdf_data = await extract_pdf_text(url_edital)
                if pdf_data and pdf_data.get("texto"):
                    texto_edital = pdf_data["texto"]
            except Exception as e:
                logger.warning(f"[{property_id}] Falha ao extrair edital para análise de ocupação: {e}")

    # Extrair sinais de ocupação
    signals = extract_occupancy_signals(texto_edital or "")

    # Calcular risco
    risk = calculate_occupancy_risk(signals, status_ocupacao, texto_edital)

    # Salvar no banco
    try:
        supabase.table("property_analyses").update({
            "ocupacao_risco_nivel": risk["nivel_risco"],
            "ocupacao_prazo_desocupacao": f"{risk['prazo_estimado']['min']}-{risk['prazo_estimado']['max']} meses",
            "ocupacao_custo_estimado": f"R$ {risk['custo_estimado']['min']:,}-{risk['custo_estimado']['max']:,}",
            "ocupacao_sinais": risk["sinais"],
        }).eq("property_id", property_id).eq("tipo", "edital").execute()
    except Exception as e:
        logger.error(f"[{property_id}] Erro ao salvar ocupação: {e}")

    logger.info(
        f"[{property_id}] Análise de ocupação: nivel={risk['nivel_risco']}, "
        f"prazo={risk['prazo_estimado']['min']}-{risk['prazo_estimado']['max']} meses"
    )


async def run_full_analysis(property_id: str):
    from app.services.ipl_calculator import calcular_ipl, score_margem, classificar_ipl
    from app.services.legal_checker import search_processes_by_property

    supabase = get_supabase()

    try:
        prop_result = supabase.table("properties").select("*").eq("id", property_id).single().execute()
    except Exception as e:
        logger.error(f"Erro ao buscar imóvel {property_id}: {e}")
        return

    if not prop_result.data:
        logger.error(f"Imóvel {property_id} não encontrado para análise")
        return

    prop = prop_result.data
    score_risco_final = 5.0
    any_url = bool(prop.get("url_matricula") or prop.get("url_edital"))

    if not any_url:
        _save_error(supabase, property_id, "edital", "Imóvel sem URL de matrícula ou edital disponível")

    # 1. Matrícula
    sr_mat = await _analyze_doc_for_property(supabase, prop, "matricula")
    if sr_mat is not None:
        score_risco_final = sr_mat

    # 2. Edital
    sr_edt = await _analyze_doc_for_property(supabase, prop, "edital")
    if sr_edt is not None:
        score_risco_final = min(score_risco_final, sr_edt) if sr_mat is not None else sr_edt

    # 3. Processos judiciais
    try:
        legal_results = await search_processes_by_property(
            property_id,
            prop["uf"],
            prop.get("imovel_numero", ""),
            endereco=prop.get("endereco", ""),
            proprietario=prop.get("proprietario", ""),
        )
        if legal_results:
            try:
                supabase.table("legal_checks").upsert(
                    legal_results, on_conflict="property_id,tribunal,numero_processo"
                ).execute()
                score_risco_final = max(0.0, score_risco_final - 1.5)
            except Exception as e:
                logger.error(f"Erro ao salvar legal_checks: {e}")
    except Exception as e:
        logger.error(f"Busca de processos falhou: {e}")

    # 4. Extração de débitos
    try:
        risco_dividas = await _extract_debts_for_property(supabase, prop)
        if risco_dividas:
            # Reduzir score de risco se houver débitos significativos
            score_risco_final = max(
                0.0, score_risco_final - (risco_dividas.get("risco_dividas_score", 0) * 0.3)
            )
    except Exception as e:
        logger.error(f"Extração de débitos falhou: {e}")

    # 5. Análise de risco de ocupação
    try:
        await _analyze_occupancy_risk(supabase, prop)
    except Exception as e:
        logger.error(f"Análise de ocupação falhou: {e}")

    # 5. Recalcular IPL final
    try:
        if prop.get("preco") and prop.get("valor_avaliacao"):
            from app.services.ipl_calculator import score_oportunidade
            sm = score_margem(float(prop["preco"]), float(prop["valor_avaliacao"]))
            so = score_oportunidade(
                aceita_fgts=bool(prop.get("aceita_fgts")),
                aceita_financiamento=bool(prop.get("aceita_financiamento")),
                desconto_pct=float(prop.get("desconto_percentual") or 0.0),
            )
            ipl = calcular_ipl(sm, score_risco_final, so)
            supabase.table("properties").update(
                {
                    "ipl_score": ipl,
                    "ipl_score_risco": score_risco_final,
                    "ipl_classificacao": classificar_ipl(ipl),
                }
            ).eq("id", property_id).execute()
    except Exception as e:
        logger.error(f"Recálculo de IPL falhou: {e}")

    logger.info(f"Análise concluída para {property_id}: IPL ajustado")


@router.post("/{property_id}/analyze")
async def trigger_analysis(property_id: str, background_tasks: BackgroundTasks):
    supabase = get_supabase()

    prop = supabase.table("properties").select(
        "id,imovel_numero,uf,url_matricula,url_edital"
    ).eq("id", property_id).single().execute()

    if not prop.data:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    # Verificar análise recente (evitar spam). Linhas com erro não bloqueiam retry.
    existing = supabase.table("property_analyses").select(
        "id,created_at,erro_analise,resumo_executivo"
    ).eq("property_id", property_id).execute()

    successful = [
        r for r in (existing.data or [])
        if not r.get("erro_analise") and r.get("resumo_executivo")
    ]

    if successful:
        try:
            last = max(
                datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                for r in successful
            )
            if datetime.now(timezone.utc) - last < timedelta(hours=6):
                full = supabase.table("property_analyses").select("*").eq(
                    "property_id", property_id
                ).execute()
                legal = supabase.table("legal_checks").select("*").eq("property_id", property_id).execute()
                legal_data = legal.data or []
                return {
                    "message": "Análise recente já disponível",
                    "property_id": property_id,
                    "status": "cached",
                    "analyses": full.data or [],
                    "legal_checks": legal_data,
                    "legal_summary": summarize_legal_risks(legal_data),
                }
        except Exception:
            pass

    background_tasks.add_task(run_full_analysis, property_id)

    return {
        "message": "Análise iniciada em background",
        "property_id": property_id,
        "status": "processing",
    }


@router.get("/{property_id}/analysis")
async def get_analysis(property_id: str):
    supabase = get_supabase()

    analyses = supabase.table("property_analyses").select("*").eq(
        "property_id", property_id
    ).execute()

    legal = supabase.table("legal_checks").select("*").eq(
        "property_id", property_id
    ).execute()

    has_analysis = bool(analyses.data)
    is_processing = False

    legal_data = legal.data or []

    return {
        "property_id": property_id,
        "analyses": analyses.data or [],
        "legal_checks": legal_data,
        "legal_summary": summarize_legal_risks(legal_data),
        "has_analysis": has_analysis,
        "is_processing": is_processing,
    }


@router.get("/{property_id}/debts")
async def get_debt_analysis(property_id: str):
    supabase = get_supabase()

    try:
        result = (
            supabase.table("property_analyses")
            .select("*")
            .eq("property_id", property_id)
            .eq("tipo", "dividas")
            .single()
            .execute()
        )
    except Exception:
        # Sem análise de débitos disponível
        return {
            "property_id": property_id,
            "has_debt_analysis": False,
            "dividas": [],
            "risco_dividas_score": 0.0,
        }

    data = result.data

    return {
        "property_id": property_id,
        "has_debt_analysis": True,
        "dividas": data.get("dividas", []),
        "tem_iptu_pendente": data.get("tem_iptu_pendente", False),
        "tem_condominio_pendente": data.get("tem_condominio_pendente", False),
        "tem_contribuicao_melhoria": data.get("tem_contribuicao_melhoria", False),
        "tem_propter_rem": data.get("tem_propter_rem", False),
        "total_dividas_estimado": data.get("total_dividas_estimado", 0.0),
        "risco_dividas_score": data.get("risco_dividas_score", 0.0),
        "total_dividas_transferidas": data.get("total_dividas_transferidas", 0),
        "valor_total_transferido": data.get("valor_total_transferido", 0.0),
        "resumo_dividas": data.get("resumo_dividas"),
        "alerta_comprador": data.get("alerta_comprador"),
        "modelo_ia": data.get("modelo_ia"),
        "created_at": data.get("created_at"),
    }


@router.post("/{property_id}/analyze-debts")
async def trigger_debt_analysis(property_id: str, background_tasks: BackgroundTasks):
    supabase = get_supabase()

    try:
        prop = supabase.table("properties").select(
            "id,imovel_numero,uf,url_matricula,url_edital"
        ).eq("id", property_id).single().execute()
    except Exception:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    if not prop.data:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    if not prop.data.get("url_matricula") and not prop.data.get("url_edital"):
        raise HTTPException(
            status_code=400,
            detail="Imóvel sem URL de matrícula ou edital para análise de débitos"
        )

    background_tasks.add_task(_extract_debts_for_property, supabase, prop.data)

    return {
        "message": "Análise de débitos iniciada em background",
        "property_id": property_id,
        "status": "processing",
    }
