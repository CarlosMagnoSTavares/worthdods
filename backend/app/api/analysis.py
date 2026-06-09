from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime, timezone, timedelta
import logging
from app.database import get_supabase
from app.services.legal_checker import summarize_legal_risks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/properties", tags=["analysis"])


async def run_full_analysis(property_id: str):
    from app.services.pdf_extractor import extract_pdf_text
    from app.services.ai_analyzer import analyze_document
    from app.services.ipl_calculator import (
        score_risco_from_analysis, calcular_ipl, score_margem, classificar_ipl
    )
    from app.services.legal_checker import search_processes_by_property

    supabase = get_supabase()

    prop_result = supabase.table("properties").select("*").eq("id", property_id).single().execute()
    if not prop_result.data:
        logger.error(f"Imóvel {property_id} não encontrado para análise")
        return

    prop = prop_result.data
    score_risco_final = 5.0

    # 1. Análise da Matrícula
    if prop.get("url_matricula"):
        logger.info(f"Analisando matrícula: {prop['url_matricula']}")
        pdf_data = await extract_pdf_text(prop["url_matricula"])
        if pdf_data and pdf_data.get("texto"):
            resultado = await analyze_document(pdf_data["texto"], "matricula")
            if resultado and not resultado.get("erro"):
                analise = resultado["resultado"]
                sr = score_risco_from_analysis(analise)
                score_risco_final = sr

                supabase.table("property_analyses").upsert(
                    {
                        "property_id": property_id,
                        "tipo": "matricula",
                        "texto_extraido": pdf_data["texto"][:10000],
                        "paginas_extraidas": pdf_data["paginas"],
                        "resumo_executivo": analise.get("resumo_executivo"),
                        "recomendacao": analise.get("recomendacao"),
                        "nivel_risco": analise.get("nivel_risco"),
                        "risco_evicao": analise.get("risco_evicao", False),
                        "riscos_detalhados": analise.get("riscos", []),
                        "pontos_positivos": analise.get("pontos_positivos", []),
                        "score_risco": sr,
                        "modelo_ia": resultado.get("modelo"),
                        "tokens_usados": resultado.get("tokens"),
                    },
                    on_conflict="property_id,tipo",
                ).execute()
            elif resultado and resultado.get("erro"):
                supabase.table("property_analyses").upsert(
                    {
                        "property_id": property_id,
                        "tipo": "matricula",
                        "erro_analise": resultado["erro"],
                    },
                    on_conflict="property_id,tipo",
                ).execute()

    # 2. Análise do Edital
    if prop.get("url_edital"):
        logger.info(f"Analisando edital: {prop['url_edital']}")
        pdf_data = await extract_pdf_text(prop["url_edital"])
        if pdf_data and pdf_data.get("texto"):
            resultado = await analyze_document(pdf_data["texto"], "edital")
            if resultado and not resultado.get("erro"):
                analise = resultado["resultado"]
                sr = score_risco_from_analysis(analise)
                score_risco_final = min(score_risco_final, sr)

                supabase.table("property_analyses").upsert(
                    {
                        "property_id": property_id,
                        "tipo": "edital",
                        "texto_extraido": pdf_data["texto"][:10000],
                        "paginas_extraidas": pdf_data["paginas"],
                        "resumo_executivo": analise.get("resumo_executivo"),
                        "recomendacao": analise.get("recomendacao"),
                        "nivel_risco": analise.get("nivel_risco"),
                        "risco_evicao": analise.get("risco_evicao", False),
                        "risco_divida_iptu": analise.get("risco_divida_iptu", False),
                        "risco_divida_condominio": analise.get("risco_divida_condominio", False),
                        "risco_ocupacao": analise.get("risco_ocupacao", False),
                        "risco_processo_judicial": analise.get("risco_processo_judicial", False),
                        "risco_irregularidade": analise.get("risco_irregularidade", False),
                        "risco_ambiental": analise.get("risco_ambiental", False),
                        "riscos_detalhados": analise.get("riscos", []),
                        "pontos_positivos": analise.get("pontos_positivos", []),
                        "score_risco": sr,
                        "modelo_ia": resultado.get("modelo"),
                        "tokens_usados": resultado.get("tokens"),
                    },
                    on_conflict="property_id,tipo",
                ).execute()

    # 3. Processos judiciais
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

    # 4. Recalcular IPL final
    if prop.get("preco") and prop.get("valor_avaliacao"):
        sm = score_margem(float(prop["preco"]), float(prop["valor_avaliacao"]))
        ipl = calcular_ipl(sm, score_risco_final)
        supabase.table("properties").update(
            {
                "ipl_score": ipl,
                "ipl_score_risco": score_risco_final,
                "ipl_classificacao": classificar_ipl(ipl),
            }
        ).eq("id", property_id).execute()

    logger.info(f"Análise concluída para {property_id}: IPL ajustado")


@router.post("/{property_id}/analyze")
async def trigger_analysis(property_id: str, background_tasks: BackgroundTasks):
    supabase = get_supabase()

    prop = supabase.table("properties").select(
        "id,imovel_numero,uf,url_matricula,url_edital"
    ).eq("id", property_id).single().execute()

    if not prop.data:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")

    # Verificar análise recente (evitar spam)
    existing = supabase.table("property_analyses").select(
        "id,created_at"
    ).eq("property_id", property_id).execute()

    if existing.data:
        try:
            last = max(
                datetime.fromisoformat(r["created_at"].replace("Z", "+00:00"))
                for r in existing.data
            )
            if datetime.now(timezone.utc) - last < timedelta(hours=6):
                legal = supabase.table("legal_checks").select("*").eq("property_id", property_id).execute()
                legal_data = legal.data or []
                return {
                    "message": "Análise recente já disponível",
                    "property_id": property_id,
                    "status": "cached",
                    "analyses": existing.data,
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
