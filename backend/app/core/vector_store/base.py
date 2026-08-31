"""向量库抽象层。"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseVectorStore(ABC):
    name: str = "base"

    @abstractmethod
    def add(self, ids: List[str], texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[dict]] = None) -> None:
        """新增/覆盖向量。"""

    @abstractmethod
    def search(self, embedding: List[float], top_k: int = 5) -> List[dict]:
        """按相似度检索，返回 [{id, text, score, metadata}]。"""

    @abstractmethod
    def list_all(self) -> List[dict]:
        """返回全部条目（用于 BM25 全量构建）。"""

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """删除指定条目。"""

    @abstractmethod
    def count(self) -> int:
        """条目数量。"""
