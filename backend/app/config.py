from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://medrag:medrag@localhost:5432/medrag"
    hf_token: str = ""
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    llm_model: str = "Qwen/Qwen3-8B"
    audit_log_path: str = "./data/audit.jsonl"
    log_level: str = "INFO"


settings = Settings()
