import re
from typing import Optional


def parse_brl(value: str) -> Optional[float]:
    """Converte 'R$ 150.000,00' para 150000.0"""
    if not value:
        return None
    cleaned = re.sub(r"[R$\s]", "", value).replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def format_brl(value: float) -> str:
    """Formata float para 'R$ 150.000,00'"""
    formatted = f"{value:_.2f}".replace("_", ".").replace(".", ",", 1)
    # Fix: replace last dot before decimals with comma
    # Python format: 150000.00 -> "150,000.00" -> need BRL format
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def parse_discount_pct(value: str) -> Optional[float]:
    """Converte '39,56%' para 39.56"""
    if not value:
        return None
    cleaned = value.strip().replace("%", "").replace(",", ".")
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def build_matricula_url(uf: str, imovel_numero: str) -> str:
    return f"https://venda-imoveis.caixa.gov.br/editais/matricula/{uf}/{imovel_numero}.pdf"


def truncate_text(text: str, max_chars: int = 40000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[TEXTO TRUNCADO PARA ANÁLISE]"
