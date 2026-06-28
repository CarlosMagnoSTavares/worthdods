"""
Análise de documentos (matrícula/edital) via OpenRouter.
Extrai riscos jurídicos e retorna JSON estruturado.
"""

import httpx
import json
import logging
from typing import Optional, List
from app.config import settings

logger = logging.getLogger(__name__)

PROMPT_MATRICULA = """Você é especialista em análise de matrículas de imóveis para leilões no Brasil.

Analise a matrícula abaixo e retorne um JSON estruturado.

MATRÍCULA:
{texto}

Responda APENAS com JSON válido neste formato:
{{
  "resumo_executivo": "Resumo em 3 linhas do histórico e situação atual do imóvel",
  "proprietario_atual": "Nome do proprietário conforme matrícula",
  "cadeia_dominial_ok": true,
  "consolidacao_caixa": true,
  "riscos": [
    {{
      "tipo": "EVICAO|ONUS|HIPOTECA|PENHORA|ALIENACAO_FIDUCIARIA|SERVIDAO|RESTRICAO_JUDICIAL|OUTRO",
      "descricao": "Descrição clara do risco",
      "severidade": "BAIXA|MEDIA|ALTA|CRITICA",
      "responsavel": "COMPRADOR|VENDEDOR|NAO_INFORMADO",
      "clausula": "Trecho relevante da matrícula"
    }}
  ],
  "dividas": [
    {{
      "tipo": "IPTU|CONDOMINIO|CONTRIBUICAO_MELHORIA|PROPTER_REM|HIPOTECA|PENHORA|OUTRO",
      "descricao": "Descrição específica da dívida ou ônus registrado",
      "valor_estimado": null,
      "periodo": "Período a que se refere",
      "responsavel": "COMPRADOR|VENDEDOR|NAO_INFORMADO",
      "severidade": "BAIXA|MEDIA|ALTA|CRITICA",
      "clausula": "Trecho relevante da matrícula",
      "garantia_comprador": false
    }}
  ],
  "pontos_positivos": ["aspectos positivos encontrados"],
  "risco_evicao": false,
  "score_risco": 8.5,
  "recomendacao": "COMPRAR|ANALISAR_COM_CUIDADO|EVITAR",
  "nivel_risco": "BAIXO|MEDIO|ALTO|CRITICO"
}}

REGRAS:
- risco_evicao = true se a matrícula NÃO garante proteção ao comprador
- consolidacao_caixa = true se a Caixa já consolidou a propriedade (positivo para comprador)
- score_risco: 10 = sem riscos, diminua conforme gravidade
- Baseie-se APENAS no texto fornecido

REGRAS PARA DÍVIDAS (campo "dividas"):
- Extraia TODAS as dívidas, ônus e gravames registrados na matrícula
- IPTU: débitos de IPTU, certidões negativas pendentes, inscrições em dívida ativa
- CONDOMINIO: cotas condominiais em atraso, débitos de condomínio
- CONTRIBUICAO_MELHORIA: contribuições de melhoria que incidam sobre o imóvel
- PROPTER_REM: obrigações propter rem que acompanham o imóvel
- HIPOTECA/PENHORA: gravames judiciais ou convencionais
- Se houver penhora ou hipoteca, avalie se afeta a comercialização do imóvel
- Se valor não for mencionado, deixe null — NÃO invente valores"""

PROMPT_DIVIDAS = """Você é especialista em identificação de débitos e encumbrâncias em documentos de leilão imobiliário brasileiro.

Analise o texto abaixo (pode ser edital ou matrícula) e extraia TODOS os débitos, taxas e obrigações financeiras que o comprador/arrematante pode herdar.

TEXTO:
{texto}

Responda APENAS com JSON válido neste formato:
{{
  "dividas": [
    {{
      "tipo": "IPTU|CONDOMINIO|CONTRIBUICAO_MELHORIA|PROPTER_REM|IPTU_TRANSFERIDO|CONDOMINIO_TRANSFERIDO|ALUGUEL_ATRASADO|TAXA_LIXO|CND_NAO_OBTIDA|OUTRO",
      "descricao": "Descrição clara e específica da dívida ou obrigação",
      "valor_estimado": null,
      "valor_texto": "R$ 1.234,56" ou "Não informado",
      "periodo": "2024-2025" ou "Não informado",
      "responsavel": "COMPRADOR|VENDEDOR|AMBOS|NAO_INFORMADO",
      "severidade": "BAIXA|MEDIA|ALTA|CRITICA",
      "transferida_ao_comprador": true,
      "base_legal": "Art. 130 CC" ou "",
      "clausula_documento": "Trecho exato do documento que menciona este débito",
      "ocorrencia": "MENCIONADO|VALOR_ESPECIFICO|NAO_ENCONTRADO"
    }}
  ],
  "tem_iptu_pendente": false,
  "tem_condominio_pendente": false,
  "tem_contribuicao_melhoria": false,
  "tem_propter_rem": false,
  "total_dividas_estimado": 0.0,
  "resumo_dividas": "Resumo das dívidas encontradas em 2-3 linhas",
  "alerta_comprador": "Mensagem de alerta clara sobre o impacto financeiro para o comprador"
}}

REGRAS CRÍTICAS:
- Identifique dívidas MESMO quando o documento diz que "não há débitos" — procure contradições
- IPTU: imposto municipal que pode estar pendente e ser transferido por propter rem
- Condomínio: taxas condominiais atrasadas são obrigação propter rem e seguem o imóvel
- Contribuição de melhoria: taxa cobrada por melhorias públicas (asfalto, praça, etc.)
- Propter rem: dívidas que "grudam" no imóvel e se transferem ao novo proprietário
- Se não houver valor específico, coloque null em valor_estimado mas NÃO ignore o débito
- transferida_ao_comprador = true quando o edital NÃO isenta o comprador ou quando a obrigação é propter rem
- Priorize a proteção do comprador: na dúvida, marque como transferida ao comprador"""

PROMPT_EDITAL = """Você é especialista em análise de editais de leilão imobiliário no Brasil.

Analise o edital abaixo e identifique TODOS os riscos para o comprador/arrematante.

EDITAL:
{texto}

Responda APENAS com JSON válido neste formato:
{{
  "resumo_executivo": "Resumo em 3-5 linhas com os pontos mais importantes para o arrematante",
  "status_ocupacao": "OCUPADO|DESOCUPADO|DESCONHECIDO",
  "aceita_fgts": true,
  "aceita_financiamento": true,
  "valor_minimo_1_leilao": null,
  "valor_minimo_2_leilao": null,
  "data_1_leilao": null,
  "data_2_leilao": null,
  "riscos": [
    {{
      "tipo": "EVICAO|DIVIDA_IPTU|DIVIDA_CONDOMINIO|DIVIDA_AGUA|OCUPACAO|PROCESSO_JUDICIAL|IRREGULARIDADE|AMBIENTAL|OUTRO",
      "descricao": "Descrição clara — QUEM paga esta dívida (comprador ou vendedor)?",
      "severidade": "BAIXA|MEDIA|ALTA|CRITICA",
      "responsavel": "COMPRADOR|VENDEDOR|NAO_INFORMADO",
      "valor_estimado": null,
      "clausula": "Trecho exato do edital"
    }}
  ],
  "dividas": [
    {{
      "tipo": "IPTU|CONDOMINIO|CONTRIBUICAO_MELHORIA|PROPTER_REM|IPTU_ALTERADO|OUTRO",
      "descricao": "Descrição específica da dívida ou ônus",
      "valor_estimado": null,
      "periodo": "Período a que se refere (ex: 2024-2025, em atraso desde 01/2024)",
      "responsavel": "COMPRADOR|VENDEDOR|NAO_INFORMADO",
      "severidade": "BAIXA|MEDIA|ALTA|CRITICA",
      "clausula": "Trecho exato do edital que menciona esta dívida",
      "garantia_comprador": false
    }}
  ],
  "risco_evicao": false,
  "risco_divida_iptu": false,
  "risco_divida_condominio": false,
  "risco_ocupacao": false,
  "risco_processo_judicial": false,
  "risco_irregularidade": false,
  "risco_ambiental": false,
  "pontos_positivos": ["aspectos favoráveis ao comprador"],
  "score_risco": 8.0,
  "recomendacao": "COMPRAR|ANALISAR_COM_CUIDADO|EVITAR",
  "nivel_risco": "BAIXO|MEDIO|ALTO|CRITICO"
}}

REGRAS CRÍTICAS:
- risco_evicao = true se o edital limita ou exclui indenização por evicção
- risco_divida_iptu = true se IPTU pendente é transferido ao comprador
- risco_divida_condominio = true se dívida de condomínio é transferida ao comprador
- risco_ocupacao = true se imóvel está ocupado E o edital não garante desocupação

REGRAS PARA DÍVIDAS (campo "dividas"):
- Extraia TODAS as dívidas, ônus e encargos mencionados no edital, mesmo que sejam genéricos
- IPTU: busque menções a IPTU, imposto predial, débitos tributários, certidões negativas
- CONDOMINIO: busque cotas condominiais, débitos de condomínio, contribuições ordinárias/extraordinárias
- CONTRIBUICAO_MELHORIA: busque contribuições de melhoria, obras de infraestrutura que geram ônus ao adquirente
- PROPTER_REM: busque obrigações propter rem (débitos que "seguem o imóvel" independentemente do proprietário)
- Se o edital diz que o comprador assume dívidas, garantia_comprador = true
- Se há cláusula de "imissão na posse em X dias", registre o período
- Se valor não for mencionado, deixe null — NÃO invente valores
- Se não houver informação clara, assuma o pior caso (proteção ao investidor)"""


# Lista de modelos a tentar em ordem. Primeiro o configurado no env,
# depois fallbacks reconhecidamente estáveis e gratuitos no OpenRouter.
def _model_chain() -> List[str]:
    primary = (settings.OPENROUTER_MODEL_PRIMARY or "").strip()
    fallback = (settings.OPENROUTER_MODEL_FALLBACK or "").strip()
    extra_fallbacks = [
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemini-2.0-flash-exp:free",
        "deepseek/deepseek-chat-v3-0324:free",
    ]
    chain: List[str] = []
    for m in [primary, fallback, *extra_fallbacks]:
        if m and m not in chain:
            chain.append(m)
    return chain


def _extract_json(content: str) -> Optional[dict]:
    """Tenta extrair JSON de uma resposta de LLM, lidando com fences ```json e texto extra."""
    if not content:
        return None
    text = content.strip()

    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


async def _call_openrouter(client: httpx.AsyncClient, model: str, prompt: str) -> dict:
    """Faz uma chamada ao OpenRouter. Retorna dict com 'parsed' | 'erro' | 'status'."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }

    try:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://worthdods.com.br",
                "X-Title": "Worthdods",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    except httpx.TimeoutException as e:
        logger.warning(f"OpenRouter timeout model={model}: {e}")
        return {"erro": f"Timeout no modelo {model}", "status": 0}
    except Exception as e:
        logger.warning(f"OpenRouter request falhou model={model}: {e}")
        return {"erro": f"Erro de rede no modelo {model}: {e}", "status": 0}

    if resp.status_code >= 500:
        logger.warning(f"OpenRouter HTTP {resp.status_code} model={model}: {resp.text[:300]}")
        return {"erro": f"HTTP {resp.status_code} no modelo {model}", "status": resp.status_code}

    try:
        data = resp.json()
    except Exception as e:
        logger.error(f"OpenRouter resposta não-JSON model={model}: {e}; body={resp.text[:300]}")
        return {"erro": f"Resposta não-JSON do OpenRouter: {e}", "status": resp.status_code}

    if isinstance(data, dict) and data.get("error"):
        err = data["error"]
        msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
        logger.warning(f"OpenRouter error model={model}: {msg}")
        return {"erro": msg, "status": resp.status_code}

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        logger.error(f"OpenRouter sem 'choices' model={model}: {str(data)[:300]}")
        return {"erro": "Resposta sem 'choices' do OpenRouter", "status": resp.status_code}

    parsed = _extract_json(content)
    if parsed is None:
        logger.error(f"JSON inválido model={model}: {content[:300]}")
        return {"erro": "Resposta da IA não é JSON válido", "status": resp.status_code, "raw": content[:1000]}

    return {
        "parsed": parsed,
        "modelo": data.get("model", model),
        "tokens": (data.get("usage") or {}).get("total_tokens", 0),
        "status": resp.status_code,
    }


async def analyze_document(texto: str, tipo: str) -> Optional[dict]:
    if not settings.OPENROUTER_API_KEY:
        return {"erro": "OPENROUTER_API_KEY não configurada"}

    if tipo == "dividas":
        prompt_template = PROMPT_DIVIDAS
    elif tipo == "matricula":
        prompt_template = PROMPT_MATRICULA
    else:
        prompt_template = PROMPT_EDITAL
    prompt = prompt_template.format(texto=(texto or "")[:30000])

    last_err = "Falha desconhecida"
    chain = _model_chain()
    logger.info(f"Análise {tipo}: tentando {len(chain)} modelo(s): {chain}")

    async with httpx.AsyncClient(timeout=180.0) as client:
        for model in chain:
            result = await _call_openrouter(client, model, prompt)
            if "parsed" in result:
                logger.info(f"Análise {tipo} OK com modelo {model} ({result.get('tokens')} tokens)")
                return {
                    "resultado": result["parsed"],
                    "modelo": result.get("modelo", model),
                    "tokens": result.get("tokens", 0),
                }
            last_err = result.get("erro", last_err)
            logger.warning(f"Modelo {model} falhou ({last_err}); tentando próximo")

    return {"erro": last_err}
