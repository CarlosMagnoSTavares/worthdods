"""
Análise de documentos (matrícula/edital) via OpenRouter.
Extrai riscos jurídicos e retorna JSON estruturado.
"""

import httpx
import json
import logging
from typing import Optional
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
- Baseie-se APENAS no texto fornecido"""

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
- Se não houver informação clara, assuma o pior caso (proteção ao investidor)"""


async def analyze_document(texto: str, tipo: str) -> Optional[dict]:
    prompt_template = PROMPT_MATRICULA if tipo == "matricula" else PROMPT_EDITAL
    prompt = prompt_template.format(texto=texto[:40000])

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://worthdods.com.br",
                    "X-Title": "Worthdods",
                },
                json={
                    "model": settings.OPENROUTER_MODEL_PRIMARY,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                },
            )

            data = resp.json()

            if "error" in data:
                return {"erro": data["error"].get("message", str(data["error"]))}

            content = data["choices"][0]["message"]["content"]

            # Extrair JSON do conteúdo (pode haver texto antes/depois)
            content = content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(content)

            return {
                "resultado": parsed,
                "modelo": data.get("model", settings.OPENROUTER_MODEL_PRIMARY),
                "tokens": data.get("usage", {}).get("total_tokens", 0),
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error na análise {tipo}: {e}")
            return {"erro": f"Resposta da IA não é JSON válido: {e}"}
        except Exception as e:
            logger.error(f"Erro análise {tipo}: {e}")
            return {"erro": str(e)}
