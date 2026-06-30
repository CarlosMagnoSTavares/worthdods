#!/usr/bin/env python3
"""
Test script for the total cost calculator.
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.total_cost_calculator import (
    CostInputs,
    calcular_custo_total,
    gerar_resumo_custos,
    formatar_moeda
)

def test_cost_calculator():
    """Test the total cost calculator with sample data."""
    print("Testing Total Cost Calculator")
    print("=" * 50)
    
    # Sample property data
    inputs = CostInputs(
        preco_lance=250000.0,  # R$ 250,000 winning bid
        valor_avaliacao=400000.0,  # R$ 400,000 market value
        uf="SP",
        cidade="São Paulo",
        status_ocupacao="ocupado",
        area_m2=80.0,
        idade_imovel_anos=25,
        condicao_imovel="regular",
        dividas_iptu=5000.0,
        dividas_condominio=3000.0,
        dividas_outros=0.0
    )
    
    # Calculate costs
    breakdown = calcular_custo_total(inputs)
    resumo = gerar_resumo_custos(breakdown)
    
    print(f"Property Details:")
    print(f"  Location: {inputs.cidade}, {inputs.uf}")
    print(f"  Area: {inputs.area_m2} m²")
    print(f"  Age: {inputs.idade_imovel_anos} years")
    print(f"  Condition: {inputs.condicao_imovel}")
    print(f"  Occupancy: {inputs.status_ocupacao}")
    print()
    
    print(f"Cost Breakdown:")
    print(f"  Winning Bid: {formatar_moeda(breakdown.preco_lance)}")
    print(f"  Auction Commission (5%): {formatar_moeda(breakdown.comissao_leilao)}")
    print(f"  ITBI (3%): {formatar_moeda(breakdown.itbi)}")
    print(f"  Registration Fees (2%): {formatar_moeda(breakdown.registro_cartorio)}")
    print(f"  Eviction Costs: {formatar_moeda(breakdown.custos_evicao)}")
    print(f"  Reform Budget: {formatar_moeda(breakdown.orcamento_reforma)}")
    print(f"  Outstanding Debts: {formatar_moeda(breakdown.dividas_pendentes)}")
    print()
    
    print(f"Summary:")
    print(f"  Total Cost: {formatar_moeda(breakdown.custo_total)}")
    print(f"  Market Value: {formatar_moeda(breakdown.valor_mercado)}")
    print(f"  Profit Margin: {breakdown.margem_lucro_pct:.1f}%")
    print(f"  ROI Indicator: {breakdown.roi_indicador}")
    print()
    
    # Test with different scenario
    print("=" * 50)
    print("Testing with better scenario (lower costs)")
    print("=" * 50)
    
    inputs2 = CostInputs(
        preco_lance=200000.0,
        valor_avaliacao=350000.0,
        uf="RJ",
        cidade="Rio de Janeiro",
        status_ocupacao="desocupado",
        area_m2=100.0,
        idade_imovel_anos=15,
        condicao_imovel="bom",
        dividas_iptu=0.0,
        dividas_condominio=0.0,
        dividas_outros=0.0
    )
    
    breakdown2 = calcular_custo_total(inputs2)
    
    print(f"Property Details:")
    print(f"  Location: {inputs2.cidade}, {inputs2.uf}")
    print(f"  Area: {inputs2.area_m2} m²")
    print(f"  Age: {inputs2.idade_imovel_anos} years")
    print(f"  Condition: {inputs2.condicao_imovel}")
    print(f"  Occupancy: {inputs2.status_ocupacao}")
    print()
    
    print(f"Cost Breakdown:")
    print(f"  Winning Bid: {formatar_moeda(breakdown2.preco_lance)}")
    print(f"  Auction Commission (5%): {formatar_moeda(breakdown2.comissao_leilao)}")
    print(f"  ITBI (3%): {formatar_moeda(breakdown2.itbi)}")
    print(f"  Registration Fees (2%): {formatar_moeda(breakdown2.registro_cartorio)}")
    print(f"  Eviction Costs: {formatar_moeda(breakdown2.custos_evicao)}")
    print(f"  Reform Budget: {formatar_moeda(breakdown2.orcamento_reforma)}")
    print(f"  Outstanding Debts: {formatar_moeda(breakdown2.dividas_pendentes)}")
    print()
    
    print(f"Summary:")
    print(f"  Total Cost: {formatar_moeda(breakdown2.custo_total)}")
    print(f"  Market Value: {formatar_moeda(breakdown2.valor_mercado)}")
    print(f"  Profit Margin: {breakdown2.margem_lucro_pct:.1f}%")
    print(f"  ROI Indicator: {breakdown2.roi_indicador}")
    print()
    
    print("Cost calculator tests completed successfully!")

if __name__ == "__main__":
    test_cost_calculator()