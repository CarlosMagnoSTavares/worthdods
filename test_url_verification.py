#!/usr/bin/env python3
"""
Test script for the URL verification service.
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.url_verifier import (
    verify_url,
    get_legitimate_platforms,
    get_scam_indicators
)

def test_url_verification():
    """Test the URL verification service with sample URLs."""
    print("Testing URL Verification Service")
    print("=" * 60)
    
    # Test URLs
    test_urls = [
        # Legitimate URLs
        "https://venda-imoveis.caixa.gov.br/sistema/imovel.asp",
        "https://leiloes.caixa.gov.br/",
        "https://leiloes.bb.com.br/",
        "https://leiloes.itau.com.br/",
        
        # Suspicious URLs
        "https://caixa-leiloes.com/sistema/imovel.asp",
        "https://leiloes-caixa.com.br/",
        "https://bb-leiloes.com/",
        "http://leiloes.itau.com.br/",  # HTTP only
        
        # Unknown URLs
        "https://example.com/leilao",
        "https://random-site.com/auction",
    ]
    
    for url in test_urls:
        print(f"\nVerifying: {url}")
        print("-" * 60)
        
        result = verify_url(url)
        
        print(f"  Legitimate: {result.is_legitimate}")
        print(f"  Platform: {result.platform or 'Unknown'}")
        print(f"  Risk Level: {result.risk_level}")
        
        if result.risk_factors:
            print(f"  Risk Factors:")
            for factor in result.risk_factors[:3]:  # Show first 3
                print(f"    - {factor}")
        
        if result.recommendations:
            print(f"  Recommendations:")
            for rec in result.recommendations[:2]:  # Show first 2
                print(f"    - {rec}")
    
    print("\n" + "=" * 60)
    print("Testing Legitimate Platforms List")
    print("=" * 60)
    
    platforms = get_legitimate_platforms()
    print(f"Number of legitimate platforms: {len(platforms)}")
    for key, info in platforms.items():
        print(f"  {info['name']}: {', '.join(info['domains'][:2])}")
    
    print("\n" + "=" * 60)
    print("Testing Scam Indicators List")
    print("=" * 60)
    
    indicators = get_scam_indicators()
    print(f"Number of scam indicators: {len(indicators)}")
    for indicator in indicators[:5]:  # Show first 5
        print(f"  - {indicator}")
    
    print("\nURL verification tests completed successfully!")

if __name__ == "__main__":
    test_url_verification()