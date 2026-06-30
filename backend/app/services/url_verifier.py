"""
URL Verification Service for Auction Platforms

Validates auction URLs to detect scam and clone sites.
Maintains a database of known legitimate auction platforms
and flags suspicious characteristics.
"""

from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from urllib.parse import urlparse
import re


@dataclass
class URLVerificationResult:
    """Result of URL verification."""
    url: str
    is_legitimate: bool
    platform: Optional[str]
    risk_level: str  # "low", "medium", "high", "critical"
    risk_factors: List[str]
    recommendations: List[str]
    details: Dict[str, Any]


# Known legitimate auction platforms in Brazil
LEGITIMATE_PLATFORMS = {
    "caixa": {
        "name": "Caixa Econômica Federal",
        "domains": [
            "caixa.gov.br",
            "venda-imoveis.caixa.gov.br",
            "leiloes.caixa.gov.br",
        ],
        "patterns": [
            r"leiloes\.caixa\.gov\.br",
            r"venda-imoveis\.caixa\.gov\.br",
        ],
        "warnings": [
            "CAIXA não envia boletos por e-mail, WhatsApp ou SMS",
            "Não pague para liberar oportunidade ou acelerar análise",
        ],
    },
    "bb": {
        "name": "Banco do Brasil",
        "domains": [
            "bb.com.br",
            "leiloes.bb.com.br",
            "venda-imoveis.bb.com.br",
        ],
        "patterns": [
            r"leiloes\.bb\.com\.br",
            r"venda-imoveis\.bb\.com\.br",
        ],
        "warnings": [],
    },
    "itau": {
        "name": "Itaú Unibanco",
        "domains": [
            "itau.com.br",
            "leiloes.itau.com.br",
        ],
        "patterns": [
            r"leiloes\.itau\.com\.br",
        ],
        "warnings": [],
    },
    "bradesco": {
        "name": "Bradesco",
        "domains": [
            "bradesco.com.br",
            "leiloes.bradesco.com.br",
        ],
        "patterns": [
            r"leiloes\.bradesco\.com\.br",
        ],
        "warnings": [],
    },
    "santander": {
        "name": "Santander",
        "domains": [
            "santander.com.br",
            "leiloes.santander.com.br",
        ],
        "patterns": [
            r"leiloes\.santander\.com\.br",
        ],
        "warnings": [],
    },
    "cra": {
        "name": "Conselho Regional de Administração",
        "domains": [
            "cra.org.br",
        ],
        "patterns": [
            r"cra\.org\.br",
        ],
        "warnings": [],
    },
}

# Suspicious patterns that indicate potential scam sites
SUSPICIOUS_PATTERNS = [
    # Domain spoofing patterns
    r"caixa-leiloes\.com",
    r"caixa-leiloes\.net",
    r"caixa-leiloes\.org",
    r"caixa-leiloes\.info",
    r"leiloes-caixa\.com",
    r"leiloes-caixa\.net",
    r"bb-leiloes\.com",
    r"bb-leiloes\.net",
    r"itau-leiloes\.com",
    r"bradesco-leiloes\.com",
    r"santander-leiloes\.com",
    
    # Generic scam patterns
    r"leilao.*gratuito",
    r"leilao.*promo",
    r"leilao.*oferta.*especial",
    r"leilao.*desconto.*garantido",
    r"leilao.*oportunidade.*unica",
    
    # Payment red flags
    r"pagar.*para.*liberar",
    r"pagar.*para.*acelerar",
    r"pagar.*para.*reservar",
    r"boleto.*whatsapp",
    r"boleto.*email",
    r"pix.*whatsapp",
    
    # Urgency tactics
    r"ultima.*oportunidade",
    r"apenas.*hoje",
    r"oferta.*limitada",
    r"vagas.*limitadas",
]

# Known scam indicators
SCAM_INDICATORS = [
    "Non-official domain claiming to be Caixa/bank",
    "Requests payment to unlock opportunities",
    "Sends boletos via WhatsApp/email",
    "Uses urgency tactics (limited time, limited spots)",
    "Domain registered recently (< 1 year)",
    "No SSL certificate (HTTP only)",
    "Poor website quality or design",
    "Missing contact information",
    "No physical address listed",
    "Requests personal information upfront",
]


def verify_url(url: str) -> URLVerificationResult:
    """
    Verify an auction URL for legitimacy.
    
    Args:
        url: The URL to verify
        
    Returns:
        URLVerificationResult with verification details
    """
    if not url:
        return URLVerificationResult(
            url=url,
            is_legitimate=False,
            platform=None,
            risk_level="high",
            risk_factors=["Empty URL provided"],
            recommendations=["Please provide a valid URL"],
            details={}
        )
    
    # Parse the URL
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
    except Exception as e:
        return URLVerificationResult(
            url=url,
            is_legitimate=False,
            platform=None,
            risk_level="high",
            risk_factors=[f"Invalid URL format: {str(e)}"],
            recommendations=["Please provide a valid URL"],
            details={}
        )
    
    # Check against legitimate platforms
    platform_match = None
    is_legitimate = False
    risk_factors = []
    recommendations = []
    details = {}
    
    # Check each legitimate platform
    for platform_key, platform_info in LEGITIMATE_PLATFORMS.items():
        for pattern in platform_info["patterns"]:
            if re.search(pattern, domain + path):
                platform_match = platform_info["name"]
                is_legitimate = True
                details["platform_info"] = platform_info
                break
        
        if is_legitimate:
            break
    
    # Check for suspicious patterns
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, domain + path, re.IGNORECASE):
            risk_factors.append(f"Suspicious pattern detected: {pattern}")
    
    # Check for domain spoofing
    for platform_key, platform_info in LEGITIMATE_PLATFORMS.items():
        for official_domain in platform_info["domains"]:
            if official_domain in domain and domain != official_domain:
                risk_factors.append(f"Possible domain spoofing: {domain} mimics {official_domain}")
                recommendations.append(f"Verify you are on the official {platform_info['name']} website")
    
    # Determine risk level
    if is_legitimate and not risk_factors:
        risk_level = "low"
    elif is_legitimate and risk_factors:
        risk_level = "medium"
    elif risk_factors:
        risk_level = "high"
    else:
        risk_level = "medium"
    
    # Generate recommendations
    if not is_legitimate:
        recommendations.append("This URL does not match known legitimate auction platforms")
        recommendations.append("Verify the website before providing any personal information")
        recommendations.append("Check for SSL certificate (HTTPS)")
        recommendations.append("Look for contact information and physical address")
    
    if risk_factors:
        recommendations.append("Exercise caution when using this website")
    
    # Check for HTTP only (no SSL)
    if parsed.scheme == "http":
        risk_factors.append("Website does not use HTTPS (no SSL certificate)")
        recommendations.append("Look for websites with HTTPS for better security")
    
    return URLVerificationResult(
        url=url,
        is_legitimate=is_legitimate,
        platform=platform_match,
        risk_level=risk_level,
        risk_factors=risk_factors,
        recommendations=recommendations,
        details=details
    )


def get_legitimate_platforms() -> Dict[str, Any]:
    """Get list of known legitimate auction platforms."""
    return LEGITIMATE_PLATFORMS


def get_scam_indicators() -> List[str]:
    """Get list of common scam indicators."""
    return SCAM_INDICATORS


def format_verification_result(result: URLVerificationResult) -> Dict[str, Any]:
    """Format verification result for API response."""
    return {
        "url": result.url,
        "is_legitimate": result.is_legitimate,
        "platform": result.platform,
        "risk_level": result.risk_level,
        "risk_factors": result.risk_factors,
        "recommendations": result.recommendations,
        "details": result.details,
    }