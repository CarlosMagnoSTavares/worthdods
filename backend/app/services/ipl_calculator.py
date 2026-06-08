def score_margem(preco: float, avaliacao: float) -> float:
    if avaliacao <= 0:
        return 5.0
    desconto = (avaliacao - preco) / avaliacao
    if desconto >= 0.50: return 10.0
    if desconto >= 0.40: return 9.0
    if desconto >= 0.35: return 8.0
    if desconto >= 0.30: return 7.0
    if desconto >= 0.25: return 6.0
    if desconto >= 0.20: return 5.0
    if desconto >= 0.15: return 4.0
    if desconto >= 0.10: return 3.0
    if desconto >= 0.05: return 2.0
    return 1.0


def score_risco_from_analysis(analysis: dict) -> float:
    score = 10.0
    riscos = analysis.get("riscos", [])

    deducoes = {
        "EVICAO": 4.0,
        "DIVIDA_IPTU": 2.0,
        "DIVIDA_CONDOMINIO": 2.0,
        "OCUPACAO": 2.0,
        "PROCESSO_JUDICIAL": 1.5,
        "IRREGULARIDADE": 1.0,
        "AMBIENTAL": 1.0,
    }

    riscos_vistos = set()
    for risco in riscos:
        tipo = risco.get("tipo", "")
        responsavel = risco.get("responsavel", "NAO_INFORMADO")
        if responsavel == "VENDEDOR":
            continue
        if tipo in deducoes and tipo not in riscos_vistos:
            severidade = risco.get("severidade", "MEDIA")
            mult = {"BAIXA": 0.3, "MEDIA": 0.7, "ALTA": 1.0, "CRITICA": 1.3}.get(severidade, 1.0)
            score -= deducoes[tipo] * mult
            riscos_vistos.add(tipo)

    return max(0.0, min(10.0, round(score, 2)))


def calcular_ipl(score_margem_val: float, score_risco_val: float, score_oportunidade: float = 5.0) -> float:
    return round(score_margem_val * 0.6 + score_risco_val * 0.3 + score_oportunidade * 0.1, 2)


def classificar_ipl(ipl: float) -> str:
    if ipl >= 8.0: return "Excelente"
    if ipl >= 6.0: return "Bom"
    if ipl >= 4.0: return "Regular"
    if ipl >= 2.0: return "Ruim"
    return "Crítico"


def ipl_cor(classificacao: str) -> str:
    cores = {
        "Excelente": "#1a6b3c",
        "Bom": "#4a7c2f",
        "Regular": "#b8860b",
        "Ruim": "#c0642b",
        "Crítico": "#c0392b",
    }
    return cores.get(classificacao, "#6b6055")
