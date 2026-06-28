export interface Property {
  id: string;
  imovel_numero: string;
  uf: string;
  cidade: string;
  bairro?: string;
  endereco: string;
  preco: number;
  valor_avaliacao?: number;
  desconto_percentual?: number;
  aceita_financiamento: boolean;
  aceita_fgts: boolean;
  descricao?: string;
  modalidade?: string;
  link_acesso?: string;
  url_matricula?: string;
  url_edital?: string;
  fotos: string[];
  tipo_imovel?: string;
  area_m2?: number;
  quartos?: number;
  status_ocupacao?: string;
  data_leilao?: string;
  ipl_score?: number;
  ipl_score_margem?: number;
  ipl_score_risco?: number;
  ipl_classificacao?: string;
  updated_at?: string;
}

export interface PropertyDetail extends Property {
  analyses: Analysis[];
  legal_checks: LegalCheck[];
  legal_summary?: LegalSummary;
}

export interface Analysis {
  id: string;
  property_id: string;
  tipo: "matricula" | "edital" | "completo" | "dividas";
  resumo_executivo?: string;
  recomendacao?: string;
  nivel_risco?: string;
  risco_evicao: boolean;
  risco_divida_iptu: boolean;
  risco_divida_condominio: boolean;
  risco_ocupacao: boolean;
  risco_processo_judicial: boolean;
  risco_irregularidade: boolean;
  risco_ambiental: boolean;
  riscos_detalhados: RiscoItem[];
  dividas: DividaItem[];
  pontos_positivos: string[];
  score_risco?: number;
  modelo_ia?: string;
  erro_analise?: string;
  created_at?: string;
  // Debt-specific fields
  tem_iptu_pendente?: boolean;
  tem_condominio_pendente?: boolean;
  tem_contribuicao_melhoria?: boolean;
  tem_propter_rem?: boolean;
  total_dividas_estimado?: number;
  resumo_dividas?: string;
  alerta_comprador?: string;
  risco_dividas_score?: number;
  total_dividas_transferidas?: number;
  valor_total_transferido?: number;
  // Occupancy risk fields
  status_ocupacao?: string;
  ocupacao_risco_nivel?: string;
  ocupacao_prazo_desocupacao?: string;
  ocupacao_custo_estimado?: string;
  ocupacao_sinais?: OccupancySignal[];
}

export interface OccupancySignal {
  sinal: string;
  nivel: string;
  peso: number;
  descricao: string;
}

export interface DividaItem {
  tipo: string;
  descricao: string;
  valor_estimado?: number;
  valor_texto?: string;
  periodo?: string;
  responsavel?: string;
  severidade?: string;
  transferida_ao_comprador?: boolean;
  base_legal?: string;
  clausula_documento?: string;
  ocorrencia?: string;
}

export interface RiscoItem {
  tipo: string;
  descricao: string;
  severidade: "BAIXA" | "MEDIA" | "ALTA" | "CRITICA";
  responsavel?: string;
  clausula?: string;
  valor_estimado?: number;
}

export interface LegalCheck {
  id: string;
  property_id: string;
  tribunal: string;
  numero_processo?: string;
  classe_processual?: string;
  assunto?: string;
  tipo_risco?: string;
  severidade?: "BAIXA" | "MEDIA" | "ALTA" | "CRITICA";
  data_ajuizamento?: string;
  grau?: string;
  checked_at: string;
}

export interface LegalSummary {
  total_processos: number;
  tem_risco_critico: boolean;
  tipos_risco: string[];
  score_juridico: number;
  resumo: string;
}

export interface PropertyDetail extends Property {
  analyses: Analysis[];
  legal_checks: LegalCheck[];
  legal_summary?: LegalSummary;
}

export interface PropertiesResponse {
  data: Property[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Filters {
  uf?: string;
  cidade?: string;
  modalidade?: string;
  preco_min?: number;
  preco_max?: number;
  ipl_min?: number;
  aceita_fgts?: boolean;
  aceita_financiamento?: boolean;
  page?: number;
  page_size?: number;
  order_by?: string;
  order_dir?: string;
}

export type IplClassificacao = "Excelente" | "Bom" | "Regular" | "Ruim" | "Crítico";
