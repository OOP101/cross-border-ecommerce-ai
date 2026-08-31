"""本地 sentence-transformers 嵌入（BGE/E5 等，需安装 sentence-transformers）。"""
from typing import List

from .base import BaseEmbedding


class SentenceTransformersEmbedding(BaseEmbedding):
    name = "sentence_transformers"

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()
