"""应用配置（pydantic-settings）。所有配置可通过 .env 或环境变量覆盖。"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- 应用 ----
    APP_NAME: str = "国际贸易上市公司一站式智能服务平台"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # ---- LLM（默认 DeepSeek，通过 backend/.env 或环境变量覆盖）----
    LLM_PROVIDER: str = "openai_compatible"  # mock | openai_compatible
    LLM_API_KEY: str = ""  # 从 .env 读取；未配置时工厂自动回退 mock
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"
    LLM_MODEL: str = "deepseek-v4-pro"
    LLM_TEMPERATURE: float = 0.7
    LLM_TIMEOUT: float = 60.0
    # 故障转移备用端点：分号分隔的 "base_url|api_key|model" 列表。
    # 主端点连接失败/超时/429/5xx 时按序自动切换（见 core/llm/openai_compatible.py）。
    LLM_FAILOVER: str = ""

    # ---- Embedding ----
    EMBEDDING_PROVIDER: str = "mock"  # mock | openai_compatible
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    EMBEDDING_MODEL: str = "text-embedding-v3"
    EMBEDDING_DIM: int = 384

    # ---- 向量库 ----
    VECTOR_STORE: str = "memory"  # memory | chroma
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "data" / "chroma")

    # ---- 数据库 ----
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'app.db'}"

    # ---- RAG 参数 ----
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 128
    RAG_TOP_K: int = 5
    # 混合检索权重：基于评测集（52 条）实测——Mock Embedding 下向量路噪声较大，
    # 0.4/0.6 最优（Recall@3 100%、MRR 0.981）；接入真实 Embedding 后需用 scripts/eval_rag.py 重调
    HYBRID_WEIGHT_VECTOR: float = 0.4
    HYBRID_WEIGHT_BM25: float = 0.6
    ENABLE_RERANK: bool = False
    RERANK_PROVIDER: str = "heuristic"  # heuristic | cross_encoder
    RERANK_MODEL: str = "BAAI/bge-reranker-base"

    # ---- 鉴权（JWT；演示模式默认关闭，生产设为 True）----
    AUTH_REQUIRED: bool = False  # False=演示免登录；True=管理后台等接口需 Bearer 令牌
    JWT_SECRET_KEY: str = "dev-secret-change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # ---- CORS ----
    CORS_ORIGINS: list[str] = ["*"]

    # ---- 数据目录 ----
    DATA_DIR: str = str(BASE_DIR / "data")
    KNOWLEDGE_DIR: str = str(BASE_DIR / "data" / "knowledge")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
