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
    "Referer": "https://venda-imoveis.caixa.gov.br/",
}


async def download_pdf(url: str) -> tuple[Optional[bytes], str]:
    """Retorna (bytes_ou_None, mensagem_de_status)."""
    try:
        async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=BROWSER_HEADERS)
            if resp.status_code != 200:
                return None, f"HTTP {resp.status_code} ao baixar PDF"
            content = resp.content
            if not content:
                return None, "Resposta vazia ao baixar PDF"
            if content[:4] != b"%PDF":
                ctype = resp.headers.get("content-type", "?")
                return None, f"Resposta não é PDF (content-type={ctype})"
            return content, "ok"
    except httpx.TimeoutException:
        return None, "Timeout ao baixar PDF"
    except Exception as e:
        logger.warning(f"Download PDF falhou {url}: {e}")
        return None, f"Erro ao baixar PDF: {e}"


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
        logger.warning(f"PDF {url}: {status}")
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
