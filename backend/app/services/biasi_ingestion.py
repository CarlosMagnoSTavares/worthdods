"""
Scraping e parse de imóveis da Biasi Leilões (biasileiloes.com.br).
A Biasi é uma das maiores leiloeiras do Brasil, parceira de bancos como
Santander, Itaú, Banco do Brasil e Caixa Econômica Federal.
"""

import httpx
import logging
import re
import json
from typing import Optional, List, Dict
from bs4 import BeautifulSoup
from app.config import settings

logger = logging.getLogger(__name__)

BIASI_BASE_URL = "https://www.biasileiloes.com.br"
BIASI_LOTES_URL = f"{BIASI_BASE_URL}/lotes"


async def fetch_biasi_page(
    client: httpx.AsyncClient,
    page: int = 1,
    uf: Optional[str] = None,
    tipo: Optional[str] = None,
    comitente: Optional[str] = None,
) -> Optional[str]:
    """Fetch a page of Biasi property listings."""
    params = {"pagina": page}
    if uf:
        params["uf"] = uf
    if tipo:
        params["tipo"] = tipo
    if comitente:
        params["comitente"] = comitente

    try:
        resp = await client.get(BIASI_LOTES_URL, params=params)
        if resp.status_code == 200:
            return resp.text
        logger.warning(f"Biasi page {page}: status {resp.status_code}")
        return None
    except Exception as e:
        logger.error(f"Erro fetch Biasi page {page}: {e}")
        return None


def parse_biasi_listing(html: str) -> List[Dict]:
    """Parse Biasi property listings from HTML."""
    soup = BeautifulSoup(html, "lxml")
    properties = []

    cards = soup.select(".lote-card, .card-lote, .item-lote, article")
    if not cards:
        cards = soup.select("[class*='lote'], [class*='card'], [class*='item']")

    for card in cards:
        try:
            prop = {}

            title_el = card.select_one("h2, h3, .titulo, .title, [class*='titulo']")
            if title_el:
                prop["titulo"] = title_el.get_text(strip=True)
            else:
                continue

            price_el = card.select_one(".preco, .valor, [class*='preco'], [class*='valor']")
            if price_el:
                price_text = price_el.get_text(strip=True)
                prop["preco_texto"] = price_text
                prop["preco"] = parse_brl_biasi(price_text)

            aval_el = card.select_one(".avaliacao, [class*='avaliacao']")
            if aval_el:
                aval_text = aval_el.get_text(strip=True)
                prop["valor_avaliacao"] = parse_brl_biasi(aval_text)

            link_el = card.select_one("a[href*='lote'], a[href*='imovel']")
            if link_el:
                href = link_el.get("href", "")
                if not href.startswith("http"):
                    href = f"{BIASI_BASE_URL}{href}"
                prop["link_acesso"] = href

            location_el = card.select_one(".localizacao, .location, [class*='local']")
            if location_el:
                loc_text = location_el.get_text(strip=True)
                prop["endereco"] = loc_text
                uf_match = re.search(r"/([A-Z]{2})", loc_text)
                if uf_match:
                    prop["uf"] = uf_match.group(1)
                city_match = re.match(r"([^/-]+)", loc_text)
                if city_match:
                    prop["cidade"] = city_match.group(1).strip()

            type_el = card.select_one(".tipo, [class*='tipo']")
            if type_el:
                prop["tipo_imovel"] = type_el.get_text(strip=True)

            desc_el = card.select_one(".descricao, .description, [class*='desc']")
            if desc_el:
                prop["descricao"] = desc_el.get_text(strip=True)[:500]

            area_el = card.select_one("[class*='area']")
            if area_el:
                area_text = area_el.get_text(strip=True)
                area_match = re.search(r"([\d.,]+)\s*m", area_text)
                if area_match:
                    prop["area_m2"] = parse_area(area_match.group(1))

            quartos_el = card.select_one("[class*='quarto'], [class*='dorm']")
            if quartos_el:
                q_match = re.search(r"(\d+)", quartos_el.get_text())
                if q_match:
                    prop["quartos"] = int(q_match.group(1))

            modalidade_el = card.select_one(".modalidade, [class*='modalidade']")
            if modalidade_el:
                prop["modalidade"] = modalidade_el.get_text(strip=True)

            comitente_el = card.select_one(".comitente, [class*='comitente']")
            if comitente_el:
                prop["comitente"] = comitente_el.get_text(strip=True)

            if prop.get("titulo") and (prop.get("preco") or prop.get("valor_avaliacao")):
                properties.append(prop)

        except Exception as e:
            logger.debug(f"Erro parse card Biasi: {e}")
            continue

    return properties


def parse_brl_biasi(value: str) -> Optional[float]:
    """Parse Brazilian Real currency string to float."""
    if not value:
        return None
    cleaned = re.sub(r"[R$\s]", "", value).replace(".", "").replace(",", ".")
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    try:
        return float(cleaned) if cleaned else None
    except (ValueError, TypeError):
        return None


def parse_area(value: str) -> Optional[float]:
    """Parse area string like '150,5' to float."""
    if not value:
        return None
    cleaned = value.replace(",", ".")
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def calculate_discount(preco: Optional[float], avaliacao: Optional[float]) -> Optional[float]:
    """Calculate discount percentage from price and appraisal."""
    if preco and avaliacao and avaliacao > 0:
        return round((avaliacao - preco) / avaliacao * 100, 2)
    return None


async def sync_biasi(ufs: Optional[List[str]] = None) -> dict:
    """Sync properties from Biasi Leilões."""
    from app.database import get_supabase
    from app.services.ipl_calculator import score_margem, calcular_ipl, classificar_ipl, score_oportunidade

    target_ufs = ufs or settings.ufs_list
    stats = {"fonte": "biasi", "processados": 0, "novos": 0, "erros": 0, "ufs": target_ufs, "ids": []}

    supabase = get_supabase()

    log_entry = supabase.table("sync_logs").insert({
        "tipo": "biasi_scraping",
        "status": "running"
    }).execute()
    log_id = log_entry.data[0]["id"] if log_entry.data else None

    async with httpx.AsyncClient(
        timeout=60.0,
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }
    ) as client:
        for uf in target_ufs:
            try:
                for page in range(1, 6):
                    html = await fetch_biasi_page(client, page=page, uf=uf)
                    if not html:
                        break

                    properties = parse_biasi_listing(html)
                    if not properties:
                        break

                    batch = []
                    for prop in properties:
                        imovel_numero = generate_biasi_id(prop)
                        if not imovel_numero:
                            continue

                        preco = prop.get("preco")
                        avaliacao = prop.get("valor_avaliacao")
                        desconto = calculate_discount(preco, avaliacao)

                        record = {
                            "imovel_numero": imovel_numero,
                            "uf": prop.get("uf", uf).upper(),
                            "cidade": prop.get("cidade", "N/A"),
                            "bairro": None,
                            "endereco": prop.get("endereco", prop.get("titulo", "")),
                            "preco": preco or 0,
                            "valor_avaliacao": avaliacao,
                            "desconto_percentual": desconto,
                            "aceita_financiamento": True,
                            "aceita_fgts": False,
                            "descricao": prop.get("descricao"),
                            "modalidade": prop.get("modalidade", "leilao"),
                            "link_acesso": prop.get("link_acesso"),
                            "url_matricula": None,
                            "url_edital": None,
                            "tipo_imovel": prop.get("tipo_imovel"),
                            "area_m2": prop.get("area_m2"),
                            "quartos": prop.get("quartos"),
                            "fonte": "biasi",
                            "ativo": True,
                        }

                        if preco and avaliacao and avaliacao > 0:
                            sm = score_margem(preco, avaliacao)
                            so = score_oportunidade(
                                aceita_fgts=False,
                                aceita_financiamento=True,
                                desconto_pct=desconto or 0.0,
                            )
                            ipl = calcular_ipl(sm, 5.0, so)
                            record["ipl_score"] = ipl
                            record["ipl_score_margem"] = sm
                            record["ipl_classificacao"] = classificar_ipl(ipl)

                        batch.append(record)
                        stats["processados"] += 1
                        stats["ids"].append(imovel_numero)

                    if batch:
                        try:
                            supabase.table("properties").upsert(
                                batch, on_conflict="imovel_numero"
                            ).execute()
                            stats["novos"] += len(batch)
                        except Exception as e:
                            logger.error(f"Upsert batch Biasi {uf}: {e}")
                            stats["erros"] += 1

            except Exception as e:
                logger.error(f"Erro sync Biasi {uf}: {e}")
                stats["erros"] += 1

    seen_ids = stats.get("ids", [])
    if stats["erros"] == 0 and seen_ids:
        try:
            batch = []
            page = 0
            page_size = 1000
            while True:
                result = supabase.table("properties").select("imovel_numero").eq("ativo", True).eq("fonte", "biasi").range(page * page_size, (page + 1) * page_size - 1).execute()
                if not result.data:
                    break
                for row in result.data:
                    imovel = row.get("imovel_numero")
                    if imovel and imovel not in seen_ids:
                        batch.append(imovel)
                page += 1
                if len(result.data) < page_size:
                    break

            if batch:
                for i in range(0, len(batch), 100):
                    chunk = batch[i:i + 100]
                    supabase.table("properties").update({"ativo": False}).in_("imovel_numero", chunk).eq("fonte", "biasi").execute()
                logger.info(f"Marcados {len(batch)} imóveis Biasi como inativos")
        except Exception as e:
            logger.error(f"Erro ao marcar inativos Biasi: {e}")

    if log_id:
        supabase.table("sync_logs").update({
            "status": "completed" if stats["erros"] == 0 else "partial",
            "registros_processados": stats["processados"],
            "registros_novos": stats["novos"],
            "finalizado_em": "now()",
        }).eq("id", log_id).execute()

    logger.info(f"Sync Biasi: {stats['processados']} imóveis processados")
    return stats


def generate_biasi_id(prop: Dict) -> Optional[str]:
    """Generate a unique ID for a Biasi property."""
    link = prop.get("link_acesso", "")
    if link:
        id_match = re.search(r"/(\d+)", link)
        if id_match:
            return f"biasi-{id_match.group(1)}"

    titulo = prop.get("titulo", "")
    preco = prop.get("preco", 0)
    if titulo and preco:
        hash_input = f"{titulo}-{preco}"
        import hashlib
        hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"biasi-{hash_val}"

    return None
