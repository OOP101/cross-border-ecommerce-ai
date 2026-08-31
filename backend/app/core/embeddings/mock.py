"""离线 Mock Embedding：基于字符 n-gram 哈希，无需下载模型，相似文本得到相似向量。

用于演示 RAG 检索流程；生产环境请切换到真实嵌入模型。
"""
import hashlib
import math
from typing import List

from .base import BaseEmbedding


class MockEmbedding(BaseEmbedding):
    name = "mock"

    def __init__(self, dim: int = 384):
        self.dim = dim

    def _embed_one(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        text = text.lower()
        for n in (2, 3):
            for i in range(len(text) - n + 1):
                gram = text[i : i + n]
                h = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16)
                vec[h % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_one(t) for t in texts]
