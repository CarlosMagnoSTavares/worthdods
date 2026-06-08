from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PropertyBase(BaseModel):
    imovel_numero: str
    uf: str
    cidade: str
    bairro: Optional[str] = None
    endereco: str
    preco: float
    valor_avaliacao: Optional[float] = None
    desconto_percentual: Optional[float] = None
    aceita_financiamento: bool = False
    aceita_fgts: bool = False
    descricao: Optional[str] = None
    modalidade: Optional[str] = None
    link_acesso: Optional[str] = None
    url_matricula: Optional[str] = None
    url_edital: Optional[str] = None
    tipo_imovel: Optional[str] = None
    area_m2: Optional[float] = None
    quartos: Optional[int] = None
    status_ocupacao: Optional[str] = None
    ipl_score: Optional[float] = None
    ipl_classificacao: Optional[str] = None


class PropertySummary(PropertyBase):
    id: str
    fotos: List[str] = []
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PropertyDetail(PropertySummary):
    ipl_score_margem: Optional[float] = None
    ipl_score_risco: Optional[float] = None
    data_leilao: Optional[datetime] = None
    analyses: List[dict] = []
    legal_checks: List[dict] = []

    class Config:
        from_attributes = True


class PropertyAnalysisResult(BaseModel):
    ipl_score: float
    ipl_score_margem: float
    ipl_score_risco: float
    ipl_classificacao: str
