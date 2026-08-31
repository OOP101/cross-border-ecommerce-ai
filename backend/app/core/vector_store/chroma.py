"""Chroma 向量库适配器（生产推荐，需安装 chromadb）。"""
import logging
from typing import List, Optional

from .base import BaseVectorStore

logger = logging.getLogger(__name__)


class ChromaVectorStore(BaseVectorStore):
    name = "chroma"

    def __init__(self, persist_dir: str, collection: str = "knowledge_base"):
        import chromadb

        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(name=collection)

    def add(self, ids, texts, embeddings, metadatas=None):
        metadatas = metadatas or [{}] * len(ids)
        self.collection.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

    def search(self, embedding, top_k=5):
        res = self.collection.query(query_embeddings=[embedding], n_results=top_k, include=["documents", "metadatas", "distances"])
        ids = res["ids"][0]
        docs = res["documents"][0] if res.get("documents") else []
        metas = res["metadatas"][0] if res.get("metadatas") else []
        dists = res["distances"][0] if res.get("distances") else []
        results = []
        for i, cid in enumerate(ids):
            results.append({
                "id": cid,
                "text": docs[i] if i < len(docs) else "",
                "score": float(1.0 - dists[i]) if i < len(dists) else 0.0,
                "metadata": metas[i] if i < len(metas) else {},
            })
        return results

    def list_all(self):
        res = self.collection.get(include=["documents", "metadatas"])
        return [
            {"id": res["ids"][i], "text": res["documents"][i], "metadata": res["metadatas"][i]}
            for i in range(len(res["ids"]))
        ]

    def delete(self, ids):
        if ids:
            self.collection.delete(ids=ids)

    def count(self):
        return self.collection.count()
