"""
Download e extração de texto de PDFs da Caixa.
pdfplumber para PDFs com texto selecionável; pymupdf para fallback.
"""

import httpx
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://venda-imoveis.caixa.gov.br/",
}


async def _try_direct(url: str) -> tuple[Optional[bytes], str]:
    async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
        try:
            await client.get("https://venda-imoveis.caixa.gov.br/sistema/", headers=BROWSER_HEADERS)
        except Exception:
            pass
        try:
            resp = await client.get(url, headers=BROWSER_HEADERS)
        except httpx.TimeoutException:
            return None, "Timeout"
        except Exception as e:
            return None, f"Erro de rede: {e}"

        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}"
        content = resp.content
        if not content:
            return None, "Resposta vazia"
        if content[:4] != b"%PDF":
            ctype = resp.headers.get("content-type", "?")
            return None, f"Não é PDF (content-type={ctype})"
        return content, "ok"


async def _try_proxy(url: str) -> tuple[Optional[bytes], str]:
    """Fallback via r.jina.ai (proxy público gratuito) para contornar bloqueio de IP."""
    proxy_url = f"https://r.jina.ai/{url}"
    try:
        async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
            resp = await client.get(proxy_url, headers={"User-Agent": BROWSER_HEADERS["User-Agent"]})
            if resp.status_code != 200:
                return None, f"proxy HTTP {resp.status_code}"
            content = resp.content
            if content[:4] == b"%PDF":
                return content, "ok"
            # jina pode retornar texto extraído já — tratamos isso fora
            return None, "proxy não retornou PDF binário"
    except Exception as e:
        return None, f"proxy erro: {e}"


async def fetch_text_via_proxy(url: str) -> Optional[str]:
    """Última saída: pega o texto já extraído via r.jina.ai (que faz OCR/parsing remoto)."""
    proxy_url = f"https://r.jina.ai/{url}"
    try:
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            resp = await client.get(
                proxy_url,
                headers={
                    "User-Agent": BROWSER_HEADERS["User-Agent"],
                    "Accept": "text/plain",
                    "X-Return-Format": "text",
                },
            )
            if resp.status_code != 200:
                return None
            text = resp.text or ""
            return text if len(text.strip()) > 100 else None
    except Exception as e:
        logger.warning(f"fetch_text_via_proxy falhou: {e}")
        return None


async def download_pdf(url: str) -> tuple[Optional[bytes], str]:
    """Retorna (bytes_ou_None, mensagem_de_status). Tenta direto e via proxy."""
    content, status = await _try_direct(url)
    if content:
        return content, "ok"
    logger.info(f"PDF direto falhou ({status}); tentando proxy r.jina.ai")
    content2, status2 = await _try_proxy(url)
    if content2:
        return content2, "ok (proxy)"
    return None, f"{status}; proxy: {status2}"


def extract_text_pdfplumber(pdf_bytes: bytes) -> tuple[str, int]:
    import pdfplumber
    parts = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            num_pages = len(pdf.pages)
            for page in pdf.pages[:30]:
                text = page.extract_text()
                if text:
                    parts.append(text)
        return "\n\n".join(parts), num_pages
    except Exception as e:
        logger.warning(f"pdfplumber falhou: {e}")
        return "", 0


def extract_text_pymupdf(pdf_bytes: bytes) -> tuple[str, int]:
    import fitz
    parts = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc[:30]:
            text = page.get_text()
            if text.strip():
                parts.append(text)
        return "\n\n".join(parts), len(doc)
    except Exception as e:
        logger.warning(f"pymupdf falhou: {e}")
        return "", 0


async def extract_pdf_text(url: str) -> Optional[dict]:
    pdf_bytes, status = await download_pdf(url)
    if not pdf_bytes:
        logger.warning(f"PDF {url}: {status} — tentando extração de texto via proxy")
        proxy_text = await fetch_text_via_proxy(url)
        if proxy_text:
            return {
                "texto": proxy_text[:50000],
                "paginas": 0,
                "metodo": "proxy-text",
            }
        return {"texto": "", "paginas": 0, "metodo": "fail", "erro": status}

    texto, paginas = extract_text_pdfplumber(pdf_bytes)
    metodo = "pdfplumber"

    if len(texto.strip()) < 100:
        texto, paginas = extract_text_pymupdf(pdf_bytes)
        metodo = "pymupdf"

    if not texto.strip():
        logger.warning(f"Nenhum texto extraído de {url}")
        return {"texto": "", "paginas": paginas, "metodo": metodo, "erro": "PDF sem texto extraível (possivelmente escaneado)"}

    return {
        "texto": texto[:50000],
        "paginas": paginas,
        "metodo": metodo,
    }
