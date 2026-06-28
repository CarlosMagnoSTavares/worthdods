"""
Download e parse dos CSVs da Caixa Econômica Federal.
CSV formato:
  Linha 0: "Gerado em dd/mm/yyyy" — pular
  Linha 1: cabeçalho — pular
  Linhas 2+: dados separados por ponto-e-vírgula
"""

import httpx
import csv
import io
import asyncio
import logging
from typing import Optional
from app.config import settings
from app.utils.helpers import parse_brl, parse_discount_pct, build_matricula_url, build_edital_url

logger = logging.getLogger(__name__)

ALL_UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS",
    "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC",
    "SE", "SP", "TO",
]


async def sync_uf(uf: str) -> dict:
    url = settings.CAIXA_CSV_BASE_URL.format(uf=uf)
    stats = {"uf": uf, "processados": 0, "novos": 0, "erros": 0, "ids": []}

    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 Worthdods/1.0"})
            if resp.status_code != 200:
                logger.warning(f"CSV {uf}: status {resp.status_code}")
                stats["erros"] = 1
                return stats
            try:
                content = resp.content.decode("utf-8-sig")
            except UnicodeDecodeError:
                content = resp.content.decode("latin-1")
    except Exception as e:
        logger.error(f"Erro download CSV {uf}: {e}")
        stats["erros"] = 1
        return stats

    from app.database import get_supabase
    from app.services.ipl_calculator import score_margem, calcular_ipl, classificar_ipl, score_oportunidade

    reader = csv.reader(io.StringIO(content), delimiter=";")
    rows = list(reader)

    supabase = get_supabase()
    batch = []

    for row in rows[2:]:
        if len(row) < 11:
            continue
        imovel_numero = row[0].strip()
        if not imovel_numero:
            continue
        # Pular linhas de cabeçalho que escapam do slice
        if not any(c.isdigit() for c in imovel_numero):
            continue

        preco = parse_brl(row[5])
        avaliacao = parse_brl(row[6])
        desconto = parse_discount_pct(row[7])

        if desconto is None and preco and avaliacao and avaliacao > 0:
            desconto = round((avaliacao - preco) / avaliacao * 100, 2)

        descricao = row[9].strip() if len(row) > 9 else None
        aceita_fgts = bool(descricao and "fgts" in descricao.lower())

        link_acesso = row[11].strip() if len(row) > 11 else None

        record: dict = {
            "imovel_numero": imovel_numero,
            "uf": (row[1].strip() or uf).upper(),
            "cidade": row[2].strip(),
            "bairro": row[3].strip() or None,
            "endereco": row[4].strip(),
            "preco": preco,
            "valor_avaliacao": avaliacao,
            "desconto_percentual": desconto,
            "aceita_financiamento": "sim" in (row[8] or "").lower(),
            "aceita_fgts": aceita_fgts,
            "descricao": descricao,
            "modalidade": row[10].strip() or None,
            "link_acesso": link_acesso,
            "url_matricula": build_matricula_url(uf, imovel_numero),
            "url_edital": build_edital_url(uf, imovel_numero),
            "ativo": True,
        }

        if preco and avaliacao and avaliacao > 0:
            sm = score_margem(preco, avaliacao)
            so = score_oportunidade(
                aceita_fgts=record["aceita_fgts"],
                aceita_financiamento=record["aceita_financiamento"],
                desconto_pct=desconto or 0.0,
            )
            ipl = calcular_ipl(sm, 5.0, so)
            record["ipl_score"] = ipl
            record["ipl_score_margem"] = sm
            record["ipl_classificacao"] = classificar_ipl(ipl)

        batch.append(record)
        stats["processados"] += 1
        stats["ids"].append(imovel_numero)

        if len(batch) >= 100:
            try:
                supabase.table("properties").upsert(batch, on_conflict="imovel_numero").execute()
                stats["novos"] += len(batch)
            except Exception as e:
                logger.error(f"Upsert batch {uf}: {e}")
            batch = []

    if batch:
        try:
            supabase.table("properties").upsert(batch, on_conflict="imovel_numero").execute()
            stats["novos"] += len(batch)
        except Exception as e:
            logger.error(f"Upsert final {uf}: {e}")

    logger.info(f"Sync {uf}: {stats['processados']} imóveis processados")
    return stats


async def sync_all_ufs(ufs: Optional[list] = None) -> dict:
    from app.database import get_supabase

    target_ufs = ufs or settings.ufs_list
    supabase = get_supabase()

    log_entry = supabase.table("sync_logs").insert({
        "tipo": "caixa_csv", "status": "running"
    }).execute()
    log_id = log_entry.data[0]["id"] if log_entry.data else None

    total = 0
    errors = 0
    all_seen: set[str] = set()

    for uf in target_ufs:
        try:
            stats = await sync_uf(uf)
            total += stats["processados"]
            errors += stats["erros"]
            all_seen.update(stats.get("ids", []))
        except Exception as e:
            logger.error(f"Erro sync {uf}: {e}")
            errors += 1
        await asyncio.sleep(2)

    inativados = 0
    if errors == 0 and all_seen:
        try:
            batch = []
            page = 0
            page_size = 1000
            while True:
                result = supabase.table("properties").select("imovel_numero").eq("ativo", True).is_("fonte", "null").range(page * page_size, (page + 1) * page_size - 1).execute()
                if not result.data:
                    break
                for row in result.data:
                    imovel = row.get("imovel_numero")
                    if imovel and imovel not in all_seen:
                        batch.append(imovel)
                page += 1
                if len(result.data) < page_size:
                    break

            if batch:
                for i in range(0, len(batch), 100):
                    chunk = batch[i:i + 100]
                    supabase.table("properties").update({"ativo": False}).in_("imovel_numero", chunk).is_("fonte", "null").execute()
                inativados = len(batch)
                logger.info(f"Marcados {inativados} imóveis Caixa como inativos (removidos do CSV)")
        except Exception as e:
            logger.error(f"Erro ao marcar inativos Caixa: {e}")

    if log_id:
        supabase.table("sync_logs").update({
            "status": "completed" if errors == 0 else "partial",
            "registros_processados": total,
            "finalizado_em": "now()",
        }).eq("id", log_id).execute()

    return {"total": total, "errors": errors, "ufs": target_ufs, "inativados": inativados}
