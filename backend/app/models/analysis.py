from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RiscoItem(BaseModel):
    tipo: str
    descricao: str
    severidade: str
    responsavel: Optional[str] = "NAO_INFORMADO"
    clausula: Optional[str] = None
    valor_estimado: Optional[float] = None


class DividaItem(BaseModel):
    tipo: str
    descricao: str
    valor_estimado: Optional[float] = None
    valor_texto: Optional[str] = None
    periodo: Optional[str] = None
    responsavel: Optional[str] = "NAO_INFORMADO"
    severidade: Optional[str] = "NAO_INFORMADO"
    transferida_ao_comprador: bool = False
    base_legal: Optional[str] = None
    clausula_documento: Optional[str] = None
    ocorrencia: Optional[str] = "NAO_ENCONTRADO"


class DividasResult(BaseModel):
    dividas: List[DividaItem] = []
    tem_iptu_pendente: bool = False
    tem_condominio_pendente: bool = False
    tem_contribuicao_melhoria: bool = False
    tem_propter_rem: bool = False
    total_dividas_estimado: float = 0.0
    resumo_dividas: Optional[str] = None
    alerta_comprador: Optional[str] = None


class AnalysisResult(BaseModel):
    resumo_executivo: Optional[str] = None
    recomendacao: Optional[str] = None
    nivel_risco: Optional[str] = None
    risco_evicao: bool = False
    risco_divida_iptu: bool = False
    risco_divida_condominio: bool = False
    risco_ocupacao: bool = False
    risco_processo_judicial: bool = False
    risco_irregularidade: bool = False
    risco_ambiental: bool = False
    riscos_detalhados: List[dict] = []
    pontos_positivos: List[str] = []
    score_risco: float = 5.0


class AnalysisResponse(BaseModel):
    id: str
    property_id: str
    tipo: str
    resumo_executivo: Optional[str] = None
    recomendacao: Optional[str] = None
    nivel_risco: Optional[str] = None
    risco_evicao: bool = False
    risco_divida_iptu: bool = False
    risco_divida_condominio: bool = False
    risco_ocupacao: bool = False
    risco_processo_judicial: bool = False
    risco_irregularidade: bool = False
    risco_ambiental: bool = False
    riscos_detalhados: List[dict] = []
    pontos_positivos: List[str] = []
    score_risco: Optional[float] = None
    modelo_ia: Optional[str] = None
    created_at: Optional[datetime] = None
    erro_analise: Optional[str] = None

    class Config:
        from_attributes = True


class DividasResponse(BaseModel):
    id: str
    property_id: str
    dividas: List[dict] = []
    tem_iptu_pendente: bool = False
    tem_condominio_pendente: bool = False
    tem_contribuicao_melhoria: bool = False
    tem_propter_rem: bool = False
    total_dividas_estimado: float = 0.0
    resumo_dividas: Optional[str] = None
    alerta_comprador: Optional[str] = None
    modelo_ia: Optional[str] = None
    created_at: Optional[datetime] = None
    erro_analise: Optional[str] = None

    class Config:
        from_attributes = True
