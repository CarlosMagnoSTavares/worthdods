from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL_PRIMARY: str = "poolside/laguna-m.1:free"
    OPENROUTER_MODEL_VISION: str = "google/gemma-3-27b-it:free"

    CNJ_API_KEY: str = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    ADMIN_SECRET: str = "worthdods-admin-change-me"

    CAIXA_CSV_BASE_URL: str = "https://venda-imoveis.caixa.gov.br/listaweb/Lista_imoveis_{uf}.csv"
    CAIXA_DETAIL_BASE_URL: str = "https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp"
    CAIXA_MATRICULA_BASE_URL: str = "https://venda-imoveis.caixa.gov.br/editais/matricula"

    UFS_ATIVAS: str = "SP,RJ,MG,RS,PR,SC,GO,BA"

    @property
    def ufs_list(self) -> List[str]:
        return [uf.strip() for uf in self.UFS_ATIVAS.split(",") if uf.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
