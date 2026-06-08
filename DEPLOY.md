# Worthdods — Guia de Deploy

## Pré-requisitos

- Conta no [Supabase](https://supabase.com) (gratuito)
- Conta no [Render](https://render.com) (gratuito)
- Conta no [Vercel](https://vercel.com) (gratuito)
- Conta no [GitHub](https://github.com) para o repositório
- OpenRouter já configurado (chave em `backend/.env`)

---

## Passo 1 — Supabase

1. Acesse https://supabase.com/dashboard → **New Project**
2. Anote o **Project URL** e as chaves:
   - `Settings > API > Project URL`
   - `Settings > API > anon (public)` → `SUPABASE_ANON_KEY`
   - `Settings > API > service_role (secret)` → `SUPABASE_SERVICE_KEY`

3. Abra o **SQL Editor** e execute o arquivo `supabase_migrations.sql` completo (cole todo o conteúdo e clique Run)

4. ✅ **JÁ FEITO** — `backend/.env` preenchido e migrations executadas automaticamente.
   - Supabase URL: `https://llqqilbcpqhbzlzdpfrv.supabase.co`
   - 2.951 imóveis de SP já no banco
   - 6 tabelas criadas com RLS

---

## Passo 2 — GitHub

1. Crie um repositório no GitHub (ex: `worthdods`)
2. Na pasta `C:\Users\User\Desktop\CMST\LEILAO\`, execute:
```bash
git init
git add .
git commit -m "Initial commit — Worthdods MVP"
git remote add origin https://github.com/SEU_USUARIO/worthdods.git
git push -u origin main
```

3. Em **Settings > Secrets and Variables > Actions**, adicione:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `BACKEND_URL` (preencher após deploy no Render)

---

## Passo 3 — Deploy Backend no Render

1. Acesse https://dashboard.render.com → **New > Web Service**
2. Conecte o repositório GitHub
3. Configure:
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Em **Environment Variables**, adicione:
   - `SUPABASE_URL` → URL do projeto Supabase
   - `SUPABASE_SERVICE_KEY` → service_role key
   - `SUPABASE_ANON_KEY` → anon key
   - `OPENROUTER_API_KEY` → (use a chave do arquivo `backend/.env`)
   - `ADMIN_SECRET` → crie uma senha forte
   - `ENVIRONMENT` → `production`
   - `UFS_ATIVAS` → `SP,RJ,MG,RS,PR,SC,GO,BA`

5. Clique **Deploy**. Aguarde ~5 min.

6. Teste: acesse `https://NOME-DO-SEU-SERVICE.onrender.com/health`
   - Deve retornar: `{"status":"ok","service":"worthdods-api"}`

7. **Primeira ingestão de dados** — após deploy, execute:
```bash
curl -X POST https://NOME.onrender.com/api/v1/admin/sync \
  -H "X-Admin-Key: SUA_ADMIN_SECRET"
```

---

## Passo 4 — Deploy Frontend no Vercel

1. Acesse https://vercel.com → **New Project**
2. Importe o repositório GitHub
3. Configure:
   - **Root Directory:** `frontend`
   - **Framework:** `Next.js`
4. Em **Environment Variables**, adicione:
   - `NEXT_PUBLIC_SUPABASE_URL` → URL do Supabase
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` → anon key
   - `NEXT_PUBLIC_API_URL` → URL do Render (ex: `https://worthdods-api.onrender.com`)

5. Clique **Deploy**

---

## Passo 5 — UptimeRobot (evitar sleep do Render)

1. Acesse https://uptimerobot.com → **Add New Monitor**
2. Tipo: **HTTP(s)**
3. URL: `https://NOME.onrender.com/health`
4. Intervalo: **5 minutos**

---

## Endpoints da API

| Endpoint | Descrição |
|----------|-----------|
| `GET /health` | Status do serviço |
| `GET /api/v1/properties` | Listar imóveis (com filtros) |
| `GET /api/v1/properties/{id}` | Detalhe do imóvel + análises |
| `POST /api/v1/properties/{id}/analyze` | Iniciar análise IA |
| `GET /api/v1/properties/{id}/analysis` | Buscar análise existente |
| `GET /api/v1/properties/stats` | Estatísticas gerais |
| `POST /api/v1/admin/sync` | Sincronizar CSVs da Caixa (requer X-Admin-Key) |
| `GET /api/v1/admin/sync/logs` | Logs de sincronização |

### Filtros do `GET /properties`:
- `uf`, `cidade`, `modalidade`
- `preco_min`, `preco_max`
- `ipl_min` (Score IPL mínimo)
- `aceita_fgts`, `aceita_financiamento` (true/false)
- `order_by` (ipl_score, preco, desconto_percentual, updated_at)
- `order_dir` (asc/desc)
- `page`, `page_size`

---

## Estrutura do Projeto

```
LEILAO/
├── backend/                # FastAPI → Render
│   ├── app/
│   │   ├── api/            # Endpoints
│   │   ├── services/       # Lógica de negócio
│   │   ├── models/         # Schemas Pydantic
│   │   └── utils/          # Helpers
│   ├── requirements.txt
│   └── render.yaml
├── frontend/               # Next.js → Vercel
│   ├── app/                # App Router
│   ├── components/         # Componentes React
│   ├── lib/                # API client, utils
│   └── types/              # TypeScript types
├── supabase_migrations.sql # Execute no Supabase SQL Editor
├── .github/workflows/      # Keep-alive automático
└── .gitignore
```

---

## Score IPL — Como funciona

```
IPL = (score_margem × 0.6) + (score_risco × 0.3) + (score_oportunidade × 0.1)
```

| Score Margem | Desconto |
|---|---|
| 10 | ≥50% |
| 9 | ≥40% |
| 8 | ≥35% |
| 7 | ≥30% |
| 5 | ≥20% |
| 3 | ≥10% |

| IPL | Classificação |
|---|---|
| 8.0–10.0 | Excelente 🟢 |
| 6.0–7.9 | Bom 🟡 |
| 4.0–5.9 | Regular 🟠 |
| 2.0–3.9 | Ruim 🔴 |
| 0.0–1.9 | Crítico ⛔ |
