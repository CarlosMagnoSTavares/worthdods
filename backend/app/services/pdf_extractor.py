"""
Download e extração de texto de PDFs da Caixa.
pdfplumber para PDFs com texto selecionável; pymupdf para fallback.
"""

import httpx
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def download_pdf(url: str) -> Optional[bytes]:
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 Worthdods/1.0"})
            if resp.status_code == 200 and resp.content[:4] == b"%PDF":
                return resp.content
    except Exception as e:
        logger.warning(f"Download PDF falhou {url}: {e}")
    return None


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
    pdf_bytes = await download_pdf(url)
    if not pdf_bytes:
        return None

    texto, paginas = extract_text_pdfplumber(pdf_bytes)
    metodo = "pdfplumber"

    if len(texto.strip()) < 100:
        texto, paginas = extract_text_pymupdf(pdf_bytes)
        metodo = "pymupdf"

    if not texto.strip():
        logger.warning(f"Nenhum texto extraído de {url}")
        return None

    return {
        "texto": texto[:50000],
        "paginas": paginas,
        "metodo": metodo,
    }
