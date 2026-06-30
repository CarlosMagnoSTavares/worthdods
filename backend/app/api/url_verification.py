from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.url_verifier import (
    verify_url,
    get_legitimate_platforms,
    get_scam_indicators,
    format_verification_result
)

router = APIRouter(prefix="/verification", tags=["url-verification"])


class URLVerificationRequest(BaseModel):
    """Request model for URL verification."""
    url: str


class URLVerificationResponse(BaseModel):
    """Response model for URL verification."""
    url: str
    is_legitimate: bool
    platform: Optional[str]
    risk_level: str
    risk_factors: List[str]
    recommendations: List[str]
    details: Dict[str, Any]


@router.post("/verify-url", response_model=URLVerificationResponse)
async def verify_auction_url(request: URLVerificationRequest):
    """
    Verify an auction URL for legitimacy.
    
    This endpoint checks if a URL belongs to a known legitimate auction platform
    and flags suspicious characteristics that may indicate scam or clone sites.
    """
    result = verify_url(request.url)
    return format_verification_result(result)


@router.get("/legitimate-platforms")
async def list_legitimate_platforms():
    """
    Get list of known legitimate auction platforms.
    
    Returns a list of verified auction platforms with their official domains
    and warnings about common scam tactics.
    """
    platforms = get_legitimate_platforms()
    return {
        "platforms": platforms,
        "count": len(platforms),
        "note": "This list is maintained based on official sources and may not be exhaustive"
    }


@router.get("/scam-indicators")
async def list_scam_indicators():
    """
    Get list of common scam indicators for auction websites.
    
    Returns a list of red flags and warning signs that may indicate
    a fraudulent auction website.
    """
    indicators = get_scam_indicators()
    return {
        "indicators": indicators,
        "count": len(indicators),
        "note": "Use these indicators to evaluate auction websites"
    }


@router.post("/batch-verify")
async def batch_verify_urls(urls: List[str]):
    """
    Verify multiple auction URLs at once.
    
    This endpoint allows verifying multiple URLs in a single request,
    useful for checking a list of auction links.
    """
    if len(urls) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 URLs can be verified in a single request"
        )
    
    results = []
    for url in urls:
        result = verify_url(url)
        results.append(format_verification_result(result))
    
    return {
        "results": results,
        "total": len(results),
        "legitimate_count": sum(1 for r in results if r["is_legitimate"]),
        "suspicious_count": sum(1 for r in results if r["risk_level"] in ["high", "critical"])
    }