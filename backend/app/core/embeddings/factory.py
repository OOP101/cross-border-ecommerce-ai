"""Embedding 工厂：根据配置返回实现（懒加载，缺失依赖时降级为 mock）。"""
import logging
from functools import lru_cache

from app.config import settings
from .base import BaseEmbedding
from .mock import MockEmbedding

logger = logging.getLogger(__name__)


@lru_cache
def get_embedding() -> BaseEmbedding:
    provider = settings.EMBEDDING_PROVIDER

    if provider == "openai_compatible":
        if not settings.EMBEDDING_API_KEY:
            logger.warning("EMBEDDING_PROVIDER=openai_compatible 但未配置 EMBEDDING_API_KEY，回退到 mock")
            return MockEmbedding(settings.EMBEDDING_DIM)
        try:
            from .openai_compatible import OpenAICompatibleEmbedding

            return OpenAICompatibleEmbedding(
                api_key=settings.EMBEDDING_API_KEY,
                base_url=settings.EMBEDDING_BASE_URL,
                model=settings.EMBEDDING_MODEL,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("初始化 embedding 失败：%s，回退到 mock", e)
            return MockEmbedding(settings.EMBEDDING_DIM)

    if provider == "sentence_transformers":
        try:
            from .sentence_transformers_embedding import SentenceTransformersEmbedding

            return SentenceTransformersEmbedding(settings.EMBEDDING_MODEL)
        except Exception as e:  # noqa: BLE001
            logger.warning("初始化 sentence-transformers 失败：%s，回退到 mock", e)
            return MockEmbedding(settings.EMBEDDING_DIM)

    return MockEmbedding(settings.EMBEDDING_DIM)
