-- =====================================================
-- WORTHDODS — Supabase Migrations
-- Execute no Supabase SQL Editor na ordem abaixo
-- =====================================================

-- Migration 001: Extensions
create extension if not exists "uuid-ossp";
create extension if not exists "pg_trgm";

-- Migration 002: Properties
create table if not exists public.properties (
  id uuid primary key default uuid_generate_v4(),
  imovel_numero text not null unique,
  uf char(2) not null,
  cidade text not null,
  bairro text,
  endereco text not null,
  preco numeric(15,2) not null,
  valor_avaliacao numeric(15,2),
  desconto_percentual numeric(5,2),
  aceita_financiamento boolean default false,
  aceita_fgts boolean default false,
  descricao text,
  modalidade text,
  link_acesso text,
  url_matricula text,
  url_edital text,
  fotos jsonb default '[]'::jsonb,
  tipo_imovel text,
  area_m2 numeric(10,2),
  quartos integer,
  status_ocupacao text,
  data_leilao timestamp with time zone,
  ipl_score numeric(4,2),
  ipl_score_margem numeric(4,2),
  ipl_score_risco numeric(4,2),
  ipl_classificacao text,
  fonte text default 'caixa',
  ativo boolean default true,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

create index if not exists idx_properties_uf on public.properties(uf);
create index if not exists idx_properties_cidade on public.properties(cidade);
create index if not exists idx_properties_ipl on public.properties(ipl_score desc);
create index if not exists idx_properties_preco on public.properties(preco);
create index if not exists idx_properties_updated on public.properties(updated_at desc);
create index if not exists idx_properties_ativo on public.properties(ativo);

-- Migration 003: AI Analyses
create table if not exists public.property_analyses (
  id uuid primary key default uuid_generate_v4(),
  property_id uuid not null references public.properties(id) on delete cascade,
  tipo text not null check (tipo in ('matricula', 'edital', 'completo')),
  texto_extraido text,
  paginas_extraidas integer,
  resumo_executivo text,
  recomendacao text,
  nivel_risco text,
  risco_evicao boolean default false,
  risco_divida_iptu boolean default false,
  risco_divida_condominio boolean default false,
  risco_ocupacao boolean default false,
  risco_processo_judicial boolean default false,
  risco_irregularidade boolean default false,
  risco_ambiental boolean default false,
  riscos_detalhados jsonb default '[]'::jsonb,
  pontos_positivos jsonb default '[]'::jsonb,
  clausulas_relevantes jsonb default '[]'::jsonb,
  score_risco numeric(4,2),
  modelo_ia text,
  tokens_usados integer,
  analise_versao text default '1.0',
  erro_analise text,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now(),
  unique(property_id, tipo)
);

create index if not exists idx_analyses_property on public.property_analyses(property_id);
create index if not exists idx_analyses_tipo on public.property_analyses(tipo);

-- Migration 004: Legal Checks
create table if not exists public.legal_checks (
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

create index if not exists idx_legal_property on public.legal_checks(property_id);

-- Migration 005: Sync Logs
create table if not exists public.sync_logs (
  id uuid primary key default uuid_generate_v4(),
  tipo text not null,
  uf text,
  status text not null,
  registros_processados integer default 0,
  registros_novos integer default 0,
  registros_atualizados integer default 0,
  erro text,
  iniciado_em timestamp with time zone default now(),
  finalizado_em timestamp with time zone
);

-- Migration 006: User Favorites
create table if not exists public.user_favorites (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  property_id uuid not null references public.properties(id) on delete cascade,
  notas text,
  created_at timestamp with time zone default now(),
  unique(user_id, property_id)
);

create index if not exists idx_favorites_user on public.user_favorites(user_id);

-- Migration 007: User Credits
create table if not exists public.user_credits (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade unique,
  creditos_total integer default 5,
  creditos_usados integer default 0,
  plano text default 'free',
  updated_at timestamp with time zone default now()
);

-- Migration 008: RLS Policies
alter table public.properties enable row level security;
alter table public.property_analyses enable row level security;
alter table public.legal_checks enable row level security;
alter table public.user_favorites enable row level security;
alter table public.user_credits enable row level security;
alter table public.sync_logs enable row level security;

-- Properties: leitura pública
create policy "properties_public_read" on public.properties
  for select using (true);

-- Somente service_role pode inserir/atualizar properties
create policy "properties_service_write" on public.properties
  for all using (auth.role() = 'service_role');

-- Analyses: leitura pública (cache compartilhado)
create policy "analyses_public_read" on public.property_analyses
  for select using (true);

create policy "analyses_service_write" on public.property_analyses
  for all using (auth.role() = 'service_role');

-- Legal checks: leitura pública
create policy "legal_checks_public_read" on public.legal_checks
  for select using (true);

create policy "legal_checks_service_write" on public.legal_checks
  for all using (auth.role() = 'service_role');

-- Favorites: apenas o próprio usuário
create policy "favorites_own" on public.user_favorites
  for all using (auth.uid() = user_id);

-- Credits: apenas o próprio usuário
create policy "credits_own" on public.user_credits
  for select using (auth.uid() = user_id);

-- Sync logs: apenas service_role
create policy "sync_logs_service_only" on public.sync_logs
  for all using (auth.role() = 'service_role');

-- Migration 009: Updated_at trigger
create or replace function update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger properties_updated_at
  before update on public.properties
  for each row execute function update_updated_at();

create trigger analyses_updated_at
  before update on public.property_analyses
  for each row execute function update_updated_at();
