# Worthdods — Build Prompt Completo para IA

> **Instrução para a IA que vai construir este projeto:** Leia este documento inteiro antes de escrever qualquer linha de código. Siga a ordem de implementação ao final. Não pule etapas. Cada seção contém decisões técnicas deliberadas — não as substitua por alternativas sem necessidade.

---

## 1. Visão Geral do Projeto

**Nome:** Worthdods  
**Tagline:** "O score de arrematação mais preciso do Brasil"  
**Domínio:** Análise de imóveis em leilão com IA  
**Mercado:** Investidores em leilões imobiliários no Brasil  
**Diferencial vs. concorrente (leilaoninja.com):** Análise profunda do **edital** e da **matrícula** via IA — o concorrente não faz isso. O concorrente cobra R$ 97/mês e tem dados imprecisos. Worthdods entrega análise jurídica automatizada do documento que realmente importa.

### O que o sistema faz

1. **Agrega** todos os imóveis em leilão da Caixa Econômica Federal (27 estados) via CSV público
2. **Calcula** o Score de Arrematação (IPL — Índice de Potencial de Leilão) com base em desconto e risco
3. **Analisa** a matrícula do imóvel via IA (evicção, ônus, histórico de propriedade)
4. **Analisa** o edital do leilão via IA (dívidas, ocupação, riscos jurídicos, FGTS)
5. **Pesquisa** processos judiciais via CNJ Datajud (API pública gratuita)
6. **Entrega** um relatório claro: "Compra segura / Atenção / Fuja"

### Usuário-alvo

Investidores pessoas físicas que participam de leilões imobiliários, pagam entre R$ 30–100/mês em ferramentas, e perdem horas analisando documentos manualmente. Geralmente alunos de cursos de leilão (mercado: 8.000–10.000 alunos só no curso de referência).

---

## 2. Stack Técnica (Imutável para MVP)

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| Backend | FastAPI (Python 3.11) | Async nativo, ideal para I/O-bound (PDFs, APIs externas) |
| Frontend | Next.js 14 (App Router) + TypeScript | SSR para SEO, Vercel free tier é superior ao Render para frontend |
| Banco de dados | Supabase (PostgreSQL 15) | Auth incluso, RLS, Storage, API REST automática |
| IA | OpenRouter API (modelos gratuitos) | 200 req/dia grátis — suficiente para MVP |
| PDF Parsing | pdfplumber (Python) | Melhor para PDFs de cartório (texto selecionável) |
| OCR Fallback | pymupdf (fitz) | Para PDFs escaneados/imagem |
| HTTP Client | httpx (async) | Para download de CSVs e PDFs da Caixa |
| Task Queue | APScheduler (in-process) | Cron para ingestão noturna — sem Redis no free tier |
| Deploy Backend | Render Web Service (free) | 750h/mês, 512MB RAM, `$PORT` automático |
| Deploy Frontend | Vercel (free) | Melhor opção para Next.js, sem sleep |
| CI/CD | GitHub Actions (free) | Build e deploy automático |

> **Nota Render:** O serviço dorme após 15min sem tráfego. Configure UptimeRobot (gratuito) para pingar `/health` a cada 5 minutos após o deploy.

> **Nota Supabase:** Pausa após 1 semana sem atividade. Configure um GitHub Actions para fazer ping semanal.

---

## 3. Fontes de Dados

### 3.1 Caixa Econômica Federal — Principal fonte (GRATUITA, SEM AUTH)

**CSV de imóveis por estado:**
```
GET https://venda-imoveis.caixa.gov.br/listaweb/Lista_imoveis_{UF}.csv
```
- Funciona para todos os 27 UFs: SP, RJ, MG, RS, PR, SC, BA, GO, PE, CE, MA, PA, AM, ES, RN, PB, PI, AL, SE, RO, MT, MS, AC, AP, RR, TO, DF
- Delimitado por ponto-e-vírgula (`;`), encoding UTF-8 com BOM
- Colunas: `N° do imóvel; UF; Cidade; Bairro; Endereço; Preço; Valor de avaliação; Desconto; Financiamento; Descrição; Modalidade de venda; Link de acesso`
- Atualizado diariamente pela Caixa
- Primeira linha: cabeçalho de geração (ex: `"Gerado em 29/04/2026"`) — pular ao parsear

**PDF da Matrícula (sem auth, URL direta):**
```
GET https://venda-imoveis.caixa.gov.br/editais/matricula/{UF}/{N_IMOVEL}.pdf
```
Exemplo: `https://venda-imoveis.caixa.gov.br/editais/matricula/SP/8787708191049.pdf`

**PDF do Edital (sem auth, URL construída via link_acesso):**
```
GET https://venda-imoveis.caixa.gov.br/editais/{CODIGO_EDITAL}.PDF
```
O código do edital é extraído do campo `Link de acesso` do CSV, que aponta para a página de detalhe. O link do edital está na página de detalhe — fazer parse do HTML da página para extrair o link do edital.

**Página de detalhe do imóvel:**
```
GET https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnOrigem=index&hdnimovel={N_IMOVEL}
```
Usar `httpx` + `BeautifulSoup` para extrair: link do edital, fotos, informações adicionais, status de ocupação.

### 3.2 CNJ Datajud — Processos Judiciais (GRATUITO)

**Base URL:** `https://api-publica.datajud.cnj.jus.br/`

**API Key pública:**
```
Authorization: APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==
```

**Busca por tribunal (ElasticSearch DSL):**
```
POST https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal}/_search
Content-Type: application/json
Authorization: APIKey {key}

{
  "query": {
    "match": { "numeroProcesso": "0000001-11.2020.8.26.0001" }
  }
}
```

Tribunais disponíveis: `tjsp`, `tjrj`, `tjmg`, `tjrs`, `tjpr`, `tjsc`, `tjba`, `tjgo`, `trf1`, `trf2`, `trf3`, `trf4`, `trf5`, `trf6`, `stj`, `stf`, e todos os outros estados.

Para busca por endereço/imóvel: usar busca por texto livre no campo `assunto` e cruzar com dados do imóvel.

### 3.3 OpenRouter — IA (GRATUITO, 200 req/dia)

**Base URL:** `https://openrouter.ai/api/v1`  
**Autenticação:** `Authorization: Bearer {OPENROUTER_API_KEY}`

**Modelos gratuitos recomendados:**

| Uso | Model ID | Context |
|-----|----------|---------|
| Análise de matrícula/edital (PDFs longos) | `google/gemma-2-27b-it:free` | 8K |
| Análise jurídica complexa | `meta-llama/llama-3.3-70b-instruct:free` | 66K |
| OCR de PDFs escaneados (vision) | `google/gemma-3-27b-it:free` | 131K |
| Fallback geral | `openrouter/free` | auto |

**Formato de chamada (compatível com OpenAI SDK):**
```python
import httpx

response = await client.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://worthdods.com.br",
        "X-Title": "Worthdods"
    },
    json={
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
)
```

---

## 4. Regra de Negócio — Score de Arrematação (IPL)

O IPL é um score de 0 a 10 calculado assim:

```
IPL = (score_margem × 0.6) + (score_risco × 0.3) + (score_oportunidade × 0.1)
```

### 4.1 Score de Margem (0–10) — 60% do IPL

Baseado no desconto em relação ao valor de avaliação da Caixa:

```python
def score_margem(preco: float, avaliacao: float) -> float:
    if avaliacao <= 0:
        return 5.0
    desconto = (avaliacao - preco) / avaliacao
    if desconto >= 0.50: return 10.0
    if desconto >= 0.40: return 9.0
    if desconto >= 0.30: return 7.0
    if desconto >= 0.20: return 5.0
    if desconto >= 0.10: return 3.0
    return 1.0
```

### 4.2 Score de Risco (0–10) — 30% do IPL

Extraído pela IA ao analisar matrícula + edital. Pontos de dedução:

| Risco | Dedução |
|-------|---------|
| Evicção de direitos NÃO coberta pelo vendedor | -4 pontos |
| Dívidas de IPTU transferidas ao comprador | -2 pontos |
| Dívidas de condomínio transferidas ao comprador | -2 pontos |
| Imóvel ocupado (sem previsão de desocupação) | -2 pontos |
| Processo judicial ativo sobre o imóvel | -1.5 pontos |
| Construção irregular / embargo | -1 ponto |
| Restrição ambiental | -1 ponto |

Score de risco começa em 10 e desconta os riscos encontrados. Mínimo 0.

### 4.3 Score de Oportunidade (0–10) — 10% do IPL

Para MVP, usar valor fixo de **5.0** (neutro). Em versões futuras: cruzar com dados do bairro (ZAP, IBGE).

### 4.4 Classificação Final

| IPL | Classificação | Cor |
|-----|--------------|-----|
| 8.0 – 10.0 | Excelente — Compra recomendada | Verde |
| 6.0 – 7.9 | Bom — Vale analisar | Amarelo-verde |
| 4.0 – 5.9 | Regular — Atenção necessária | Amarelo |
| 2.0 – 3.9 | Ruim — Alto risco | Laranja |
| 0.0 – 1.9 | Crítico — Fuja | Vermelho |

---

## 5. Schema do Banco de Dados (Supabase / PostgreSQL)

Execute estas migrations em ordem no Supabase SQL Editor:

```sql
-- Migration 001: Extensions
create extension if not exists "uuid-ossp";
create extension if not exists "pg_trgm"; -- Para busca full-text

-- Migration 002: Properties table
create table public.properties (
  id uuid primary key default uuid_generate_v4(),
  imovel_numero text not null unique,  -- N° do imóvel da Caixa
  uf char(2) not null,
  cidade text not null,
  bairro text,
  endereco text not null,
  preco numeric(15,2) not null,
  valor_avaliacao numeric(15,2),
  desconto_percentual numeric(5,2),      -- (avaliacao - preco) / avaliacao * 100
  aceita_financiamento boolean default false,
  aceita_fgts boolean default false,
  descricao text,
  modalidade text,                        -- "Leilão SFI", "Venda Online", etc.
  link_acesso text,                       -- URL da página de detalhe na Caixa
  url_matricula text,                     -- URL direta do PDF da matrícula
  url_edital text,                        -- URL direta do PDF do edital
  fotos jsonb default '[]'::jsonb,        -- Array de URLs de fotos
  tipo_imovel text,                       -- "Apartamento", "Casa", "Terreno", etc.
  area_m2 numeric(10,2),
  quartos integer,
  status_ocupacao text,                   -- "Ocupado", "Desocupado", "Desconhecido"
  data_leilao timestamp with time zone,
  ipl_score numeric(4,2),                 -- Score 0-10 (calculado)
  ipl_score_margem numeric(4,2),
  ipl_score_risco numeric(4,2),
  ipl_classificacao text,                 -- "Excelente", "Bom", "Regular", "Ruim", "Crítico"
  fonte text default 'caixa',
  ativo boolean default true,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

create index idx_properties_uf on public.properties(uf);
create index idx_properties_cidade on public.properties(cidade);
create index idx_properties_ipl on public.properties(ipl_score desc);
create index idx_properties_preco on public.properties(preco);
create index idx_properties_updated on public.properties(updated_at desc);
create index idx_properties_search on public.properties using gin(to_tsvector('portuguese', coalesce(endereco,'') || ' ' || coalesce(bairro,'') || ' ' || coalesce(cidade,'')));

-- Migration 003: AI Analysis table
create table public.property_analyses (
  id uuid primary key default uuid_generate_v4(),
  property_id uuid not null references public.properties(id) on delete cascade,
  tipo text not null check (tipo in ('matricula', 'edital', 'completo')),
  
  -- Texto extraído do PDF
  texto_extraido text,
  paginas_extraidas integer,
  
  -- Resultados da análise IA
  resumo_executivo text,                  -- Resumo em 3-5 linhas para o usuário
  recomendacao text,                      -- "COMPRAR", "ANALISAR_COM_CUIDADO", "EVITAR"
  nivel_risco text,                       -- "BAIXO", "MEDIO", "ALTO", "CRITICO"
  
  -- Flags de risco (booleanos para filtros rápidos)
  risco_evicao boolean default false,
  risco_divida_iptu boolean default false,
  risco_divida_condominio boolean default false,
  risco_ocupacao boolean default false,
  risco_processo_judicial boolean default false,
  risco_irregularidade boolean default false,
  risco_ambiental boolean default false,
  
  -- Detalhes estruturados
  riscos_detalhados jsonb default '[]'::jsonb,  -- Array de {tipo, descricao, severidade}
  pontos_positivos jsonb default '[]'::jsonb,   -- Array de strings
  clausulas_relevantes jsonb default '[]'::jsonb, -- Trechos do documento com análise
  
  -- Score de risco calculado
  score_risco numeric(4,2),
  
  -- Metadata da análise
  modelo_ia text,                         -- Model ID usado
  tokens_usados integer,
  analise_versao text default '1.0',
  erro_analise text,                      -- Se a análise falhou
  
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now(),
  
  unique(property_id, tipo)
);

create index idx_analyses_property on public.property_analyses(property_id);
create index idx_analyses_tipo on public.property_analyses(tipo);

-- Migration 004: Legal Checks table
create table public.legal_checks (
  id uuid primary key default uuid_generate_v4(),
  property_id uuid not null references public.properties(id) on delete cascade,
  tribunal text not null,
  numero_processo text,
  classe_processual text,
  assunto text,
  data_ajuizamento date,
  ultima_movimentacao text,
  status_processo text,
  grau text,
  raw_data jsonb,
  checked_at timestamp with time zone default now(),
  
  unique(property_id, tribunal, numero_processo)
);

create index idx_legal_property on public.legal_checks(property_id);

-- Migration 005: Sync Log table
create table public.sync_logs (
  id uuid primary key default uuid_generate_v4(),
  tipo text not null,            -- 'caixa_csv', 'analise_ia', 'legal_check'
  uf text,
  status text not null,          -- 'running', 'completed', 'failed'
  registros_processados integer default 0,
  registros_novos integer default 0,
  registros_atualizados integer default 0,
  erro text,
  iniciado_em timestamp with time zone default now(),
  finalizado_em timestamp with time zone
);

-- Migration 006: User Favorites (para quando Auth estiver ativo)
create table public.user_favorites (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  property_id uuid not null references public.properties(id) on delete cascade,
  notas text,
  created_at timestamp with time zone default now(),
  unique(user_id, property_id)
);

create index idx_favorites_user on public.user_favorites(user_id);

-- Migration 007: User Credits
create table public.user_credits (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade unique,
  creditos_total integer default 5,       -- 5 análises grátis no cadastro
  creditos_usados integer default 0,
  plano text default 'free',              -- 'free', 'basic', 'pro'
  updated_at timestamp with time zone default now()
);

-- Migration 008: Row Level Security (RLS)
alter table public.properties enable row level security;
alter table public.property_analyses enable row level security;
alter table public.legal_checks enable row level security;
alter table public.user_favorites enable row level security;
alter table public.user_credits enable row level security;
alter table public.sync_logs enable row level security;

-- Properties: leitura pública
create policy "properties_public_read" on public.properties
  for select using (true);

-- Analyses: leitura pública (análise já feita é pública — modelo de cache compartilhado)
create policy "analyses_public_read" on public.property_analyses
  for select using (true);

-- Legal checks: leitura pública
create policy "legal_checks_public_read" on public.legal_checks
  for select using (true);

-- Favorites: apenas o próprio usuário
create policy "favorites_own" on public.user_favorites
  for all using (auth.uid() = user_id);

-- Credits: apenas o próprio usuário
create policy "credits_own" on public.user_credits
  for select using (auth.uid() = user_id);

-- Sync logs: apenas service role (backend)
create policy "sync_logs_service_only" on public.sync_logs
  for all using (false);  -- Bloqueado para usuários — apenas service_role do backend acessa

-- Migration 009: Trigger para updated_at
create or replace function update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger properties_updated_at before update on public.properties
  for each row execute function update_updated_at();

create trigger analyses_updated_at before update on public.property_analyses
  for each row execute function update_updated_at();
```

---

## 6. Backend — Estrutura de Arquivos

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory, lifespan, routers
│   ├── config.py                  # Settings via pydantic-settings
│   ├── database.py                # Supabase client singleton
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py              # Agrega todos os routers
│   │   ├── properties.py          # GET /properties, GET /properties/{id}
│   │   ├── analysis.py            # POST /properties/{id}/analyze, GET /properties/{id}/analysis
│   │   ├── legal.py               # GET /properties/{id}/legal
│   │   ├── favorites.py           # POST/DELETE /favorites (auth required)
│   │   ├── auth.py                # POST /auth/verify-token
│   │   └── admin.py               # POST /admin/sync (service role only)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── property.py            # Pydantic schemas para properties
│   │   ├── analysis.py            # Pydantic schemas para analysis
│   │   └── responses.py           # Schemas genéricos de resposta
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── caixa_ingestion.py     # Download e parse dos CSVs da Caixa
│   │   ├── pdf_extractor.py       # Download e extração de texto de PDFs
│   │   ├── ai_analyzer.py         # Chamadas ao OpenRouter + parsing das respostas
│   │   ├── ipl_calculator.py      # Cálculo do Score de Arrematação
│   │   ├── legal_checker.py       # Consulta ao CNJ Datajud
│   │   └── scheduler.py           # APScheduler — cron jobs
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py             # Funções utilitárias (parse de moeda BRL, etc.)
│
├── requirements.txt
├── render.yaml
├── .env.example
└── Dockerfile                     # Opcional — Render usa requirements.txt direto
```

---

## 7. Backend — Implementação Detalhada

### 7.1 `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str          # service_role key — nunca expor no frontend
    SUPABASE_ANON_KEY: str             # anon key — pode ir para o frontend
    
    # OpenRouter
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL_PRIMARY: str = "meta-llama/llama-3.3-70b-instruct:free"
    OPENROUTER_MODEL_VISION: str = "google/gemma-3-27b-it:free"
    
    # CNJ Datajud
    CNJ_API_KEY: str = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
    
    # App
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    
    # Caixa
    CAIXA_CSV_BASE_URL: str = "https://venda-imoveis.caixa.gov.br/listaweb/Lista_imoveis_{uf}.csv"
    CAIXA_DETAIL_BASE_URL: str = "https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp"
    CAIXA_MATRICULA_BASE_URL: str = "https://venda-imoveis.caixa.gov.br/editais/matricula"
    
    # Ingestão — quais UFs processar (pode reduzir para poupar recursos no MVP)
    UFS_ATIVAS: list[str] = ["SP", "RJ", "MG", "RS", "PR", "SC", "GO", "BA"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 7.2 `app/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.services.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(
    title="Worthdods API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://worthdods.com.br", "https://www.worthdods.com.br",
                   "http://localhost:3000"],  # Next.js dev
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "worthdods-api"}
```

### 7.3 `app/services/caixa_ingestion.py`

```python
"""
Faz download dos CSVs da Caixa para todos os estados configurados,
parseia as propriedades e faz upsert no Supabase.

Lógica de parse do CSV:
- Linha 0: "Gerado em dd/mm/yyyy" — pular
- Linha 1: cabeçalho — pular
- Linhas 2+: dados

Colunas (índice):
0: N° do imóvel
1: UF
2: Cidade
3: Bairro
4: Endereço
5: Preço (formato: "R$ 150.000,00")
6: Valor de avaliação (mesmo formato)
7: Desconto (formato: "25%" ou vazio)
8: Financiamento ("Sim"/"Não")
9: Descrição
10: Modalidade de venda
11: Link de acesso (URL da página de detalhe)

Parse de moeda BRL: remover "R$ ", substituir "." por "", substituir "," por ".", converter float
"""

import httpx
import csv
import io
from app.config import settings
from app.database import get_supabase

UFS = ["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
       "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"]

async def parse_brl(value: str) -> float | None:
    """Converte 'R$ 150.000,00' para 150000.00"""
    if not value:
        return None
    cleaned = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None

async def build_matricula_url(uf: str, imovel_numero: str) -> str:
    return f"https://venda-imoveis.caixa.gov.br/editais/matricula/{uf}/{imovel_numero}.pdf"

async def sync_uf(uf: str) -> dict:
    """Baixa e processa o CSV de um estado. Retorna stats."""
    url = settings.CAIXA_CSV_BASE_URL.format(uf=uf)
    stats = {"uf": uf, "processados": 0, "novos": 0, "atualizados": 0, "erros": 0}
    
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            stats["erros"] = 1
            return stats
        
        content = response.content.decode("utf-8-sig", errors="replace")
        reader = csv.reader(io.StringIO(content), delimiter=";")
        rows = list(reader)
    
    supabase = get_supabase()
    batch = []
    
    for row in rows[2:]:  # Pular linha de data e cabeçalho
        if len(row) < 11:
            continue
        
        imovel_numero = row[0].strip()
        if not imovel_numero:
            continue
        
        preco = await parse_brl(row[5])
        avaliacao = await parse_brl(row[6])
        
        desconto_str = row[7].strip().replace("%", "")
        desconto = float(desconto_str) if desconto_str else None
        if desconto is None and preco and avaliacao and avaliacao > 0:
            desconto = round((avaliacao - preco) / avaliacao * 100, 2)
        
        record = {
            "imovel_numero": imovel_numero,
            "uf": row[1].strip() or uf,
            "cidade": row[2].strip(),
            "bairro": row[3].strip() or None,
            "endereco": row[4].strip(),
            "preco": preco,
            "valor_avaliacao": avaliacao,
            "desconto_percentual": desconto,
            "aceita_financiamento": "sim" in row[8].lower() if row[8] else False,
            "aceita_fgts": "fgts" in row[9].lower() if row[9] else False,
            "descricao": row[9].strip() or None,
            "modalidade": row[10].strip() or None,
            "link_acesso": row[11].strip() if len(row) > 11 else None,
            "url_matricula": await build_matricula_url(uf, imovel_numero),
            "ativo": True,
        }
        
        # Calcular IPL básico (sem análise de IA — apenas margem)
        if preco and avaliacao and avaliacao > 0:
            from app.services.ipl_calculator import score_margem, classificar_ipl
            sm = score_margem(preco, avaliacao)
            ipl_basico = round(sm * 0.6 + 5.0 * 0.3 + 5.0 * 0.1, 2)  # risco=5 default
            record["ipl_score"] = ipl_basico
            record["ipl_score_margem"] = sm
            record["ipl_classificacao"] = classificar_ipl(ipl_basico)
        
        batch.append(record)
        stats["processados"] += 1
        
        if len(batch) >= 100:  # Upsert em lotes de 100
            result = supabase.table("properties").upsert(
                batch, on_conflict="imovel_numero"
            ).execute()
            batch = []
    
    if batch:
        supabase.table("properties").upsert(batch, on_conflict="imovel_numero").execute()
    
    return stats

async def sync_all_ufs():
    """Sincroniza todos os estados configurados. Chamado pelo scheduler."""
    import asyncio
    from app.database import get_supabase
    
    # Registrar início no log
    supabase = get_supabase()
    log = supabase.table("sync_logs").insert({
        "tipo": "caixa_csv", "status": "running"
    }).execute().data[0]
    
    total_processados = 0
    ufs = settings.UFS_ATIVAS
    
    # Processar UFs sequencialmente para não sobrecarregar a Caixa
    for uf in ufs:
        try:
            stats = await sync_uf(uf)
            total_processados += stats["processados"]
            await asyncio.sleep(2)  # Rate limiting
        except Exception as e:
            print(f"Erro ao sincronizar {uf}: {e}")
    
    supabase.table("sync_logs").update({
        "status": "completed",
        "registros_processados": total_processados,
        "finalizado_em": "now()"
    }).eq("id", log["id"]).execute()
```

### 7.4 `app/services/pdf_extractor.py`

```python
"""
Baixa PDFs da Caixa (matrícula ou edital) e extrai o texto.
Usa pdfplumber para PDFs com texto selecionável.
Usa pymupdf para OCR fallback em PDFs escaneados.
"""

import httpx
import pdfplumber
import fitz  # pymupdf
import io
from typing import Optional

async def download_pdf(url: str) -> Optional[bytes]:
    """Baixa um PDF e retorna os bytes. Retorna None se falhar."""
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        try:
            response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code == 200 and b"PDF" in response.content[:10]:
                return response.content
        except Exception:
            pass
    return None

def extract_text_pdfplumber(pdf_bytes: bytes) -> tuple[str, int]:
    """Extrai texto usando pdfplumber. Retorna (texto, num_paginas)."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        num_pages = len(pdf.pages)
        for page in pdf.pages[:30]:  # Máx 30 páginas para poupar tokens
            text = page.extract_text()
            if text:
                text_parts.append(text)
    return "\n\n".join(text_parts), num_pages

def extract_text_pymupdf(pdf_bytes: bytes) -> tuple[str, int]:
    """Fallback: extrai texto via pymupdf para PDFs problemáticos."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []
    for page in doc[:30]:
        text = page.get_text()
        if text.strip():
            text_parts.append(text)
    return "\n\n".join(text_parts), len(doc)

async def extract_pdf_text(url: str) -> Optional[dict]:
    """
    Pipeline completo: download → extração.
    Retorna dict com 'texto', 'paginas', 'metodo' ou None se falhar.
    """
    pdf_bytes = await download_pdf(url)
    if not pdf_bytes:
        return None
    
    # Tentar pdfplumber primeiro
    texto, paginas = extract_text_pdfplumber(pdf_bytes)
    metodo = "pdfplumber"
    
    # Se texto muito curto, tentar pymupdf
    if len(texto) < 100:
        texto, paginas = extract_text_pymupdf(pdf_bytes)
        metodo = "pymupdf"
    
    if not texto.strip():
        return None
    
    return {
        "texto": texto[:50000],  # Limitar a 50k chars para caber no contexto da IA
        "paginas": paginas,
        "metodo": metodo
    }
```

### 7.5 `app/services/ai_analyzer.py`

```python
"""
Analisa documentos (matrícula e edital) usando OpenRouter.
Extrai riscos jurídicos de forma estruturada.
"""

import httpx
import json
from app.config import settings

PROMPT_MATRICULA = """Você é um especialista em análise de matrículas de imóveis para leilões judiciais e extrajudiciais no Brasil.

Analise a matrícula abaixo e extraia as informações de forma estruturada.

MATRÍCULA DO IMÓVEL:
{texto}

Responda APENAS com um JSON válido neste formato exato:
{{
  "resumo_executivo": "Resumo em 3 linhas do histórico do imóvel e situação atual",
  "cadeia_dominial_ok": true,
  "nus_propietario_atual": "Nome do atual proprietário conforme matrícula",
  "riscos": [
    {{
      "tipo": "EVICAO|ONUS|HIPOTECA|PENHORA|ALIENACAO_FIDUCIARIA|SERVIDAO|RESTRICAO_JUDICIAL|OUTRO",
      "descricao": "Descrição clara do risco",
      "severidade": "BAIXA|MEDIA|ALTA|CRITICA",
      "clausula": "Trecho relevante da matrícula"
    }}
  ],
  "pontos_positivos": ["lista de aspectos positivos encontrados"],
  "risco_evicao": false,
  "consolidacao_caixa": true,
  "score_risco": 8.5,
  "recomendacao": "COMPRAR|ANALISAR_COM_CUIDADO|EVITAR",
  "nivel_risco": "BAIXO|MEDIO|ALTO|CRITICO"
}}

REGRAS:
- risco_evicao = true se matrícula NÃO garante proteção ao comprador
- consolidacao_caixa = true se Caixa já consolidou a propriedade (positivo)
- score_risco: 10 = sem riscos, diminua conforme gravidade dos riscos
- Seja objetivo e baseie-se APENAS no texto fornecido"""

PROMPT_EDITAL = """Você é um especialista em análise de editais de leilão imobiliário no Brasil, com foco em proteção do arrematante.

Analise o edital abaixo e identifique TODOS os riscos para o comprador.

EDITAL DO LEILÃO:
{texto}

Responda APENAS com um JSON válido neste formato exato:
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
- risco_evicao = true se edital diz "sem evicção" ou "comprador assume todos os riscos"
- risco_divida_iptu = true se edital transfere IPTU pendente ao comprador
- risco_divida_condominio = true se edital transfere dívida de condomínio ao comprador
- risco_ocupacao = true se imóvel está ocupado E edital não garante desocupação
- Se não houver informação, assuma o pior caso (mais proteção ao investidor)"""

async def analyze_document(texto: str, tipo: str) -> dict | None:
    """
    Envia texto para OpenRouter e retorna análise estruturada.
    tipo: 'matricula' | 'edital'
    """
    prompt_template = PROMPT_MATRICULA if tipo == "matricula" else PROMPT_EDITAL
    prompt = prompt_template.format(texto=texto[:40000])  # Limitar ao contexto
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://worthdods.com.br",
                    "X-Title": "Worthdods"
                },
                json={
                    "model": settings.OPENROUTER_MODEL_PRIMARY,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                }
            )
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            
            return {
                "resultado": parsed,
                "modelo": data.get("model", settings.OPENROUTER_MODEL_PRIMARY),
                "tokens": data.get("usage", {}).get("total_tokens", 0)
            }
        except Exception as e:
            return {"erro": str(e)}
```

### 7.6 `app/services/ipl_calculator.py`

```python
from app.models.property import PropertyAnalysisResult

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
    """Calcula score de risco com base nos flags da análise de IA."""
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
        
        # Só deduz se o responsável é o comprador ou não informado
        if responsavel == "VENDEDOR":
            continue
            
        if tipo in deducoes and tipo not in riscos_vistos:
            severidade = risco.get("severidade", "MEDIA")
            multiplicador = {"BAIXA": 0.3, "MEDIA": 0.7, "ALTA": 1.0, "CRITICA": 1.3}.get(severidade, 1.0)
            score -= deducoes[tipo] * multiplicador
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
```

### 7.7 `app/services/legal_checker.py`

```python
"""
Consulta processos judiciais via CNJ Datajud API pública.
"""

import httpx
from app.config import settings

CNJ_BASE_URL = "https://api-publica.datajud.cnj.jus.br"

# Mapeamento de UF para tribunais principais
UF_TRIBUNAIS = {
    "SP": ["tjsp", "trf3"],
    "RJ": ["tjrj", "trf2"],
    "MG": ["tjmg", "trf6"],
    "RS": ["tjrs", "trf4"],
    "PR": ["tjpr", "trf4"],
    "SC": ["tjsc", "trf4"],
    "BA": ["tjba", "trf1"],
    "GO": ["tjgo", "trf1"],
    # Adicionar outros estados conforme necessário
}

async def search_processes_by_address(property_id: str, uf: str, imovel_numero: str) -> list[dict]:
    """
    Busca processos relacionados ao imóvel no CNJ Datajud.
    Estratégia: buscar pelo número do imóvel nos campos de texto livre.
    """
    tribunais = UF_TRIBUNAIS.get(uf, [f"tj{uf.lower()}"])
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for tribunal in tribunais[:2]:  # Máx 2 tribunais por consulta para poupar API
            try:
                response = await client.post(
                    f"{CNJ_BASE_URL}/api_publica_{tribunal}/_search",
                    headers={
                        "Authorization": f"APIKey {settings.CNJ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "query": {
                            "bool": {
                                "should": [
                                    {"match": {"assunto": imovel_numero}},
                                    {"match_phrase": {"assunto": "alienação fiduciária"}},
                                    {"match_phrase": {"assunto": "busca e apreensão"}}
                                ]
                            }
                        },
                        "size": 5,
                        "_source": ["numeroProcesso", "classe", "assunto", 
                                   "dataAjuizamento", "movimentos", "grau"]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    hits = data.get("hits", {}).get("hits", [])
                    for hit in hits:
                        source = hit.get("_source", {})
                        results.append({
                            "property_id": property_id,
                            "tribunal": tribunal.upper(),
                            "numero_processo": source.get("numeroProcesso"),
                            "classe_processual": source.get("classe", {}).get("nome") if isinstance(source.get("classe"), dict) else source.get("classe"),
                            "assunto": str(source.get("assunto", ""))[:500],
                            "data_ajuizamento": source.get("dataAjuizamento"),
                            "grau": source.get("grau"),
                            "raw_data": source
                        })
            except Exception:
                continue
    
    return results
```

### 7.8 `app/services/scheduler.py`

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio

scheduler = AsyncIOScheduler()

def start_scheduler():
    from app.services.caixa_ingestion import sync_all_ufs
    
    # Sincronizar CSVs da Caixa todo dia às 3h da manhã (horário de Brasília = UTC-3)
    scheduler.add_job(
        lambda: asyncio.create_task(sync_all_ufs()),
        CronTrigger(hour=6, minute=0),  # 6h UTC = 3h Brasília
        id="sync_caixa",
        replace_existing=True
    )
    
    scheduler.start()

def stop_scheduler():
    scheduler.shutdown(wait=False)
```

### 7.9 `app/api/properties.py`

```python
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.database import get_supabase

router = APIRouter(prefix="/properties", tags=["properties"])

@router.get("")
async def list_properties(
    uf: Optional[str] = None,
    cidade: Optional[str] = None,
    modalidade: Optional[str] = None,
    preco_min: Optional[float] = None,
    preco_max: Optional[float] = None,
    ipl_min: Optional[float] = None,
    aceita_fgts: Optional[bool] = None,
    aceita_financiamento: Optional[bool] = None,
    search: Optional[str] = None,
    order_by: str = "ipl_score",
    order_dir: str = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100)
):
    supabase = get_supabase()
    query = supabase.table("properties").select(
        "id,imovel_numero,uf,cidade,bairro,endereco,preco,valor_avaliacao,"
        "desconto_percentual,aceita_financiamento,aceita_fgts,modalidade,"
        "tipo_imovel,area_m2,quartos,status_ocupacao,ipl_score,ipl_classificacao,"
        "link_acesso,url_matricula,fotos,data_leilao,updated_at",
        count="exact"
    ).eq("ativo", True)
    
    if uf: query = query.eq("uf", uf.upper())
    if cidade: query = query.ilike("cidade", f"%{cidade}%")
    if modalidade: query = query.ilike("modalidade", f"%{modalidade}%")
    if preco_min: query = query.gte("preco", preco_min)
    if preco_max: query = query.lte("preco", preco_max)
    if ipl_min: query = query.gte("ipl_score", ipl_min)
    if aceita_fgts is not None: query = query.eq("aceita_fgts", aceita_fgts)
    if aceita_financiamento is not None: query = query.eq("aceita_financiamento", aceita_financiamento)
    if search:
        query = query.text_search("endereco", search, config="portuguese")
    
    # Ordenação
    valid_order_fields = {"ipl_score", "preco", "desconto_percentual", "updated_at"}
    if order_by not in valid_order_fields:
        order_by = "ipl_score"
    query = query.order(order_by, desc=(order_dir == "desc"))
    
    # Paginação
    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)
    
    result = query.execute()
    
    return {
        "data": result.data,
        "total": result.count,
        "page": page,
        "page_size": page_size,
        "pages": (result.count + page_size - 1) // page_size if result.count else 0
    }

@router.get("/{property_id}")
async def get_property(property_id: str):
    supabase = get_supabase()
    result = supabase.table("properties").select("*").eq("id", property_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    
    # Buscar análises existentes
    analyses = supabase.table("property_analyses").select("*").eq("property_id", property_id).execute()
    legal = supabase.table("legal_checks").select("*").eq("property_id", property_id).execute()
    
    return {
        **result.data,
        "analyses": analyses.data,
        "legal_checks": legal.data
    }
```

### 7.10 `app/api/analysis.py`

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.database import get_supabase
from app.services.pdf_extractor import extract_pdf_text
from app.services.ai_analyzer import analyze_document
from app.services.ipl_calculator import score_risco_from_analysis, calcular_ipl, score_margem, classificar_ipl
from app.services.legal_checker import search_processes_by_address

router = APIRouter(prefix="/properties", tags=["analysis"])

async def run_full_analysis(property_id: str):
    """Executa análise completa em background."""
    supabase = get_supabase()
    
    # Buscar dados do imóvel
    prop = supabase.table("properties").select("*").eq("id", property_id).single().execute().data
    if not prop:
        return
    
    score_risco_final = 5.0  # Default
    
    # 1. Analisar Matrícula
    if prop.get("url_matricula"):
        pdf_data = await extract_pdf_text(prop["url_matricula"])
        if pdf_data and pdf_data.get("texto"):
            resultado = await analyze_document(pdf_data["texto"], "matricula")
            if resultado and not resultado.get("erro"):
                analise = resultado["resultado"]
                sr = score_risco_from_analysis(analise)
                
                supabase.table("property_analyses").upsert({
                    "property_id": property_id,
                    "tipo": "matricula",
                    "texto_extraido": pdf_data["texto"][:10000],
                    "paginas_extraidas": pdf_data["paginas"],
                    "resumo_executivo": analise.get("resumo_executivo"),
                    "recomendacao": analise.get("recomendacao"),
                    "nivel_risco": analise.get("nivel_risco"),
                    "risco_evicao": analise.get("risco_evicao", False),
                    "riscos_detalhados": analise.get("riscos", []),
                    "pontos_positivos": analise.get("pontos_positivos", []),
                    "score_risco": sr,
                    "modelo_ia": resultado.get("modelo"),
                    "tokens_usados": resultado.get("tokens"),
                }, on_conflict="property_id,tipo").execute()
                
                score_risco_final = sr
    
    # 2. Analisar Edital
    if prop.get("url_edital"):
        pdf_data = await extract_pdf_text(prop["url_edital"])
        if pdf_data and pdf_data.get("texto"):
            resultado = await analyze_document(pdf_data["texto"], "edital")
            if resultado and not resultado.get("erro"):
                analise = resultado["resultado"]
                sr = score_risco_from_analysis(analise)
                
                supabase.table("property_analyses").upsert({
                    "property_id": property_id,
                    "tipo": "edital",
                    "texto_extraido": pdf_data["texto"][:10000],
                    "paginas_extraidas": pdf_data["paginas"],
                    "resumo_executivo": analise.get("resumo_executivo"),
                    "recomendacao": analise.get("recomendacao"),
                    "nivel_risco": analise.get("nivel_risco"),
                    "risco_evicao": analise.get("risco_evicao", False),
                    "risco_divida_iptu": analise.get("risco_divida_iptu", False),
                    "risco_divida_condominio": analise.get("risco_divida_condominio", False),
                    "risco_ocupacao": analise.get("risco_ocupacao", False),
                    "risco_processo_judicial": analise.get("risco_processo_judicial", False),
                    "risco_irregularidade": analise.get("risco_irregularidade", False),
                    "risco_ambiental": analise.get("risco_ambiental", False),
                    "riscos_detalhados": analise.get("riscos", []),
                    "pontos_positivos": analise.get("pontos_positivos", []),
                    "score_risco": sr,
                    "modelo_ia": resultado.get("modelo"),
                    "tokens_usados": resultado.get("tokens"),
                }, on_conflict="property_id,tipo").execute()
                
                score_risco_final = min(score_risco_final, sr)  # Usar o mais conservador
    
    # 3. Buscar processos judiciais
    legal_results = await search_processes_by_address(
        property_id, prop["uf"], prop["imovel_numero"]
    )
    if legal_results:
        supabase.table("legal_checks").upsert(
            legal_results, on_conflict="property_id,tribunal,numero_processo"
        ).execute()
        score_risco_final = max(0, score_risco_final - 1.5)  # Penalizar por processos encontrados
    
    # 4. Recalcular IPL final com score de risco real
    if prop.get("preco") and prop.get("valor_avaliacao"):
        sm = score_margem(prop["preco"], prop["valor_avaliacao"])
        ipl_final = calcular_ipl(sm, score_risco_final)
        supabase.table("properties").update({
            "ipl_score": ipl_final,
            "ipl_score_risco": score_risco_final,
            "ipl_classificacao": classificar_ipl(ipl_final),
        }).eq("id", property_id).execute()


@router.post("/{property_id}/analyze")
async def trigger_analysis(property_id: str, background_tasks: BackgroundTasks):
    """Inicia análise em background. Resposta imediata."""
    supabase = get_supabase()
    
    # Verificar se imóvel existe
    prop = supabase.table("properties").select("id,imovel_numero,uf,url_matricula,url_edital").eq("id", property_id).single().execute()
    if not prop.data:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    
    # Verificar se análise já foi feita recentemente
    existing = supabase.table("property_analyses").select("id,created_at").eq("property_id", property_id).execute()
    if existing.data:
        from datetime import datetime, timezone, timedelta
        last_analysis = max(r["created_at"] for r in existing.data)
        # Parse datetime e verificar se foi há menos de 24h
        # Se sim, retornar análise existente
    
    background_tasks.add_task(run_full_analysis, property_id)
    
    return {
        "message": "Análise iniciada",
        "property_id": property_id,
        "status": "processing"
    }

@router.get("/{property_id}/analysis")
async def get_analysis(property_id: str):
    supabase = get_supabase()
    result = supabase.table("property_analyses").select("*").eq("property_id", property_id).execute()
    return {"analyses": result.data}
```

### 7.11 `requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
pydantic-settings==2.3.4
supabase==2.5.1
httpx==0.27.0
pdfplumber==0.11.1
pymupdf==1.24.5
beautifulsoup4==4.12.3
lxml==5.2.2
APScheduler==3.10.4
python-multipart==0.0.9
```

### 7.12 `render.yaml`

```yaml
services:
  - type: web
    name: worthdods-api
    env: python
    region: oregon
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
      - key: SUPABASE_ANON_KEY
        sync: false
      - key: OPENROUTER_API_KEY
        sync: false
      - key: ENVIRONMENT
        value: production
```

---

## 8. Frontend — Estrutura (Next.js 14)

```
frontend/
├── app/
│   ├── layout.tsx                 # Root layout com providers
│   ├── page.tsx                   # Landing page
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── (app)/
│   │   ├── layout.tsx             # Layout com sidebar/navbar
│   │   ├── dashboard/page.tsx     # Lista de imóveis com filtros
│   │   ├── imovel/
│   │   │   └── [id]/page.tsx      # Detalhe do imóvel + análise
│   │   └── favoritos/page.tsx
├── components/
│   ├── ui/                        # shadcn/ui components
│   ├── PropertyCard.tsx           # Card de imóvel com IPL badge
│   ├── IplBadge.tsx               # Badge colorido com score
│   ├── RiskFlags.tsx              # Strip de flags de risco
│   ├── AnalysisPanel.tsx          # Painel de análise IA
│   ├── FiltersPanel.tsx           # Painel lateral de filtros
│   └── PropertyMap.tsx            # Mapa OpenStreetMap
├── lib/
│   ├── supabase.ts                # Cliente Supabase
│   ├── api.ts                     # Wrapper para API do backend
│   └── utils.ts                   # Formatação BRL, etc.
├── hooks/
│   ├── useProperties.ts           # React Query hook para imóveis
│   └── useAnalysis.ts             # Hook para análise
├── types/
│   └── index.ts                   # TypeScript interfaces
├── public/
│   └── logo.svg
├── .env.local.example
├── next.config.js
├── tailwind.config.ts
└── package.json
```

---

## 9. Frontend — Componentes Principais

### 9.1 `PropertyCard.tsx`

Exibe um card de imóvel com:
- Foto (ou placeholder com ícone de casa)
- Endereço, bairro, cidade/UF
- Preço formatado em BRL (ex: `R$ 150.000,00`)
- Valor de avaliação e desconto percentual (ex: `Desconto: 35%`)
- **IPL Badge**: número grande (ex: `7.8`) com cor de fundo baseada na classificação
- Tags horizontais: `FGTS` | `Financiamento` | `Ocupado/Desocupado` | modalidade
- Botão "Ver Análise"

### 9.2 `IplBadge.tsx`

```tsx
const colors = {
  "Excelente": "bg-green-500",
  "Bom": "bg-lime-500",
  "Regular": "bg-yellow-500",
  "Ruim": "bg-orange-500",
  "Crítico": "bg-red-500",
};

export function IplBadge({ score, classificacao }: { score: number; classificacao: string }) {
  return (
    <div className={`${colors[classificacao]} text-white rounded-lg p-3 text-center`}>
      <div className="text-2xl font-bold">{score.toFixed(1)}</div>
      <div className="text-xs font-medium">{classificacao}</div>
      <div className="text-xs opacity-75">Score IPL</div>
    </div>
  );
}
```

### 9.3 `RiskFlags.tsx`

Barra horizontal com ícones coloridos para cada risco:
- 🟢 Evicção coberta / 🔴 Evicção não coberta
- 🟢 Sem dívidas IPTU / 🔴 IPTU com comprador
- 🟢 Sem dívidas cond. / 🔴 Condomínio com comprador
- 🟢 Desocupado / 🔴 Ocupado
- 🟢 Sem processos / 🔴 Processos ativos
- 🟡 Sem análise (quando análise ainda não foi feita)

### 9.4 Página de Detalhe `[id]/page.tsx`

Layout de duas colunas:
- **Coluna esquerda (2/3):**
  - Carrossel de fotos
  - Endereço completo
  - Tabs: `Resumo` | `Análise IA` | `Matrícula` | `Edital` | `Processos Judiciais`
  - Tab Análise IA: resumo executivo, riscos detalhados (accordion), pontos positivos
  - Tab Matrícula / Edital: texto extraído + link para PDF original
  - Tab Processos: tabela de processos encontrados no Datajud
  
- **Coluna direita (1/3):**
  - IPL Badge grande
  - Risk Flags strip
  - Caixa de valores (preço, avaliação, desconto)
  - Tags: FGTS, Financiamento, Modalidade
  - Botão `🔍 Analisar Agora` (destaca créditos restantes)
  - Link para página original da Caixa
  - Link para Google Maps com endereço

### 9.5 `FiltersPanel.tsx`

Filtros laterais no dashboard:
- Estado (select com 27 UFs)
- Cidade (text input com autocomplete)
- Faixa de preço (range slider: R$0 – R$2.000.000)
- IPL Score mínimo (slider: 0–10)
- Modalidade (checkbox: Leilão SFI, Venda Online, etc.)
- Aceita FGTS (toggle)
- Aceita Financiamento (toggle)
- Já analisado (toggle — filtrar só imóveis com análise IA completa)

---

## 10. Variáveis de Ambiente

### Backend `.env`

```env
# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...  # service_role — NUNCA expor
SUPABASE_ANON_KEY=eyJ...

# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-...

# CNJ Datajud (chave pública — pode commitar)
CNJ_API_KEY=cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==

# App
ENVIRONMENT=production
UFS_ATIVAS=SP,RJ,MG,RS,PR,SC,GO,BA
```

### Frontend `.env.local`

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=https://worthdods-api.onrender.com
```

---

## 11. Configurações Adicionais

### GitHub Actions — Supabase Keep-Alive

Criar `.github/workflows/keepalive.yml`:

```yaml
name: Supabase Keep-Alive
on:
  schedule:
    - cron: '0 12 * * 1'  # Toda segunda-feira ao meio-dia UTC
  workflow_dispatch:

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Supabase
        run: curl -f "${{ secrets.NEXT_PUBLIC_SUPABASE_URL }}/rest/v1/properties?limit=1" -H "apikey: ${{ secrets.SUPABASE_ANON_KEY }}" || true
```

### UptimeRobot (configurar manualmente após deploy)

- Criar monitor HTTP(s) para: `https://worthdods-api.onrender.com/health`
- Intervalo: 5 minutos
- Método: GET
- Alerta: email quando cair

---

## 12. Roteiro de Implementação (Ordem Exata)

### Fase 1 — Infraestrutura (Dia 1)

1. Criar projeto no Supabase (Free tier)
2. Executar todas as migrations SQL na ordem (seção 5)
3. Criar conta no OpenRouter, gerar API key
4. Criar repositório GitHub com pastas `backend/` e `frontend/`
5. Configurar secrets no GitHub

### Fase 2 — Backend Core (Dia 1-2)

6. Criar estrutura de arquivos do backend (seção 6)
7. Implementar `config.py`, `database.py`, `main.py`
8. Implementar `caixa_ingestion.py` — **testar primeiro com apenas UF=SP**
9. Verificar dados chegando no Supabase
10. Implementar `pdf_extractor.py` — testar com URL de matrícula real
11. Implementar `ai_analyzer.py` — testar com texto de 500 palavras
12. Implementar `ipl_calculator.py`
13. Implementar todos os endpoints da API
14. Testar `/api/v1/properties` retornando dados

### Fase 3 — Deploy Backend (Dia 2)

15. Push para GitHub
16. Criar Web Service no Render apontando para `/backend`
17. Configurar variáveis de ambiente no Render
18. Verificar `/health` respondendo
19. Configurar UptimeRobot
20. Testar endpoint público: `https://worthdods-api.onrender.com/api/v1/properties`

### Fase 4 — Frontend (Dia 3-4)

21. `npx create-next-app@latest frontend --typescript --tailwind --app`
22. Instalar dependências: `@supabase/supabase-js`, `@tanstack/react-query`, `shadcn/ui`
23. Implementar landing page (simples para MVP)
24. Implementar dashboard com listagem e filtros
25. Implementar página de detalhe do imóvel
26. Implementar componente de análise IA
27. Testar fluxo completo: listar → filtrar → ver detalhe → solicitar análise

### Fase 5 — Deploy Frontend (Dia 4)

28. Conectar repositório GitHub no Vercel
29. Configurar variáveis de ambiente no Vercel
30. Deploy
31. Testar fluxo completo em produção

### Fase 6 — Primeira Ingestão Real (Dia 5)

32. Chamar manualmente `POST /api/v1/admin/sync` para ingestão inicial
33. Verificar dados de SP, RJ, MG no Supabase
34. Selecionar 5 imóveis manualmente e disparar análise IA
35. Verificar scores IPL calculados
36. Validar análises contra os documentos reais

### Fase 7 — Autenticação (Dia 5-6)

37. Ativar Auth no Supabase (Email/Password + Google OAuth)
38. Implementar páginas de login/signup no frontend
39. Implementar tabela `user_credits` e lógica de créditos
40. Proteger endpoint `POST /analyze` para usuários autenticados

---

## 13. Decisões Técnicas que NÃO devem ser alteradas no MVP

1. **Não usar Redis** — APScheduler in-process é suficiente para o free tier
2. **Não usar ONR API** — matrícula da Caixa já está no CSV/URL direta
3. **Não usar ZAP/VivaReal** — valor de avaliação da Caixa é suficiente para MVP
4. **Não usar JUDIT ou Escavador** — CNJ Datajud gratuito é suficiente para MVP
5. **Não usar Celery/Worker** — BackgroundTasks do FastAPI é suficiente para volume de MVP
6. **Não usar Docker** no Render free — aumenta tempo de build sem benefício
7. **Frontend no Vercel, não Render** — Vercel não tem sleep para Next.js
8. **Análises são públicas (cache compartilhado)** — primeira pessoa que analisa um imóvel paga com crédito, todos veem o resultado. Isso reduz custo de IA.

---

## 14. Métricas de Sucesso do MVP

- [ ] 10+ imóveis com análise completa (matrícula + edital + processos)
- [ ] Score IPL calculado para 100+ imóveis
- [ ] Tempo de análise completa < 3 minutos por imóvel
- [ ] Dashboard carrega em < 3 segundos
- [ ] 0 erros 500 em produção por 48h consecutivas
- [ ] Pelo menos 1 imóvel onde o sistema identificou corretamente um risco real

---

## 15. Glossário de Termos do Domínio

| Termo | Definição |
|-------|-----------|
| Arrematante | Quem compra o imóvel no leilão |
| Edital | Documento legal com todas as regras do leilão de um imóvel específico |
| Matrícula | Registro do imóvel no cartório — histórico completo de propriedade |
| Evicção | Perda do imóvel por decisão judicial posterior; "evicção coberta" = vendedor devolve dinheiro |
| IPTU | Imposto predial territorial urbano — pode ser transferido ao comprador se o edital permitir |
| Condomínio | Taxas de condomínio atrasadas — podem ser transferidas ao comprador |
| Consolidação | Processo pelo qual a Caixa recuperou a propriedade do devedor — positivo para o arrematante |
| SFI | Sistema Financeiro Imobiliário — modalidade de leilão da Caixa |
| FGTS | Fundo de Garantia — pode ser usado para comprar imóveis em leilão quando o edital permite |
| IPL | Índice de Potencial de Leilão — o score de 0-10 calculado pelo Worthdods |
| Leilão 1 / Leilão 2 | Dois momentos do leilão; no segundo, o preço mínimo é menor (geralmente 50% da avaliação) |
