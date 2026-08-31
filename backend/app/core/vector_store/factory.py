"""向量库工厂：根据配置返回实现（懒加载，缺失依赖时降级为 memory）。"""
import logging
from functools import lru_cache
from pathlib import Path

from app.config import settings
from .base import BaseVectorStore
from .memory import MemoryVectorStore

logger = logging.getLogger(__name__)

MEMORY_INDEX_PATH = Path(settings.DATA_DIR) / "index" / "vector_store.json"


@lru_cache
def get_vector_store() -> BaseVectorStore:
    provider = settings.VECTOR_STORE

    if provider == "chroma":
        try:
            from .chroma import ChromaVectorStore

            return ChromaVectorStore(settings.CHROMA_PERSIST_DIR)
        except Exception as e:  # noqa: BLE001
            logger.warning("初始化 Chroma 失败：%s，回退到 memory", e)

    # memory 默认持久化到 data/index/vector_store.json，保证重启后数据不丢
    return MemoryVectorStore(persist_path=str(MEMORY_INDEX_PATH))
