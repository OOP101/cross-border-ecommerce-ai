"""Embedding 抽象层。"""
from abc import ABC, abstractmethod
from typing import List


class BaseEmbedding(ABC):
    """嵌入模型接口。"""

    name: str = "base"

    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """将文本列表向量化。"""

    def embed_query(self, text: str) -> List[float]:
        """单条查询向量化。"""
        return self.embed([text])[0]
