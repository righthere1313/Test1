from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TeachingAgent Knowledge Base Service"
    API_V1_STR: str = "/api/v1"

    RAW_STORAGE_DIR: str = "data/raw"
    PROCESSED_STORAGE_DIR: str = "data/processed"
    METADATA_DB_PATH: str = "data/db/metadata.db"
    CHROMA_DB_DIR: str = "data/chroma"
    COLLECTION_NAME: str = "kb_chunks"
    
    # Chroma 服务器模式配置（Docker 环境使用）
    CHROMA_USE_SERVER: bool = False
    CHROMA_SERVER_HOST: str = "localhost"
    CHROMA_SERVER_PORT: int = 8000

    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    USE_LOCAL_EMBEDDING: bool = True
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RERANKER_BATCH_SIZE: int = 8

    OPENAI_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    OPENAI_MODEL: str = "qwen-plus"
    OPENAI_API_KEY: str | None = None

    DASHSCOPE_API_KEY: str | None = None
    OSS_ACCESS_KEY_ID: str | None = None
    OSS_ACCESS_KEY_SECRET: str | None = None
    OSS_BUCKET_NAME: str | None = None
    OSS_ENDPOINT: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()
