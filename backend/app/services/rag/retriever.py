"""混合检索器：向量检索 + BM25 关键词检索 + RRF 融合 + 可选重排序。"""
import logging
from typing import List, Optional

from app.config import settings
from app.core.embeddings.base import BaseEmbedding
from app.core.vector_store.base import BaseVectorStore
from app.utils.text_utils import tokenize
from .bm25 import BM25
from .rerank import rerank

logger = logging.getLogger(__name__)

_RRF_K = 60

# BM25 索引缓存：(租户, 语料指纹) -> BM25 实例。
# 知识库文档增删时由 knowledge 服务调用 invalidate_bm25_cache() 失效。
_bm25_cache: dict = {}


def invalidate_bm25_cache() -> None:
    """知识库发生增删后调用，强制下次检索重建 BM25 索引。"""
    _bm25_cache.clear()


def _get_bm25(all_items: List[dict], tenant_id: Optional[str] = None) -> BM25:
    fingerprint = (tenant_id or "", tuple(item["id"] for item in all_items))
    cached = _bm25_cache.get(fingerprint)
    if cached is not None:
        return cached
    bm25 = BM25()
    bm25.fit([tokenize(item["text"]) for item in all_items])
    # 防御：仅保留最新一份，避免并发增删导致缓存堆积
    _bm25_cache.clear()
    _bm25_cache[fingerprint] = bm25
    return bm25


def _tenant_filter(items: List[dict], tenant_id: Optional[str]) -> List[dict]:
    """按租户过滤检索候选；无 tenant_id 标记的历史数据视为 default 租户。"""
    if not tenant_id:
        return items
    return [
        item for item in items
        if (item.get("metadata") or {}).get("tenant_id", "default") == tenant_id
    ]


class HybridRetriever:
    """组合向量相似度与 BM25，避免单一检索遗漏。"""

    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedding: BaseEmbedding,
        top_k: int = 5,
        weight_vector: float = 0.6,
        weight_bm25: float = 0.4,
        enable_rerank: bool = False,
    ):
        self.vector_store = vector_store
        self.embedding = embedding
        self.top_k = top_k
        self.weight_vector = weight_vector
        self.weight_bm25 = weight_bm25
        self.enable_rerank = enable_rerank

    def retrieve(self, query: str, top_k: Optional[int] = None, tenant_id: Optional[str] = None) -> List[dict]:
        top_k = top_k or self.top_k
        if self.vector_store.count() == 0:
            return []

        # 1) 向量检索（多租户：检索后按租户过滤候选）
        q_emb = self.embedding.embed_query(query)
        vec_results = _tenant_filter(
            self.vector_store.search(q_emb, top_k=min(top_k * 3, 50)), tenant_id
        )

        # 2) BM25 关键词检索（索引按租户+语料指纹缓存，增删文档时失效）
        all_items = _tenant_filter(self.vector_store.list_all(), tenant_id)
        if not all_items:
            return []
        bm25 = _get_bm25(all_items, tenant_id)
        bm25_scores = bm25.get_scores(tokenize(query))
        bm25_ranked = sorted(
            range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
        )[: min(top_k * 3, 50)]

        # 3) RRF 融合
        fused: dict = {}
        for rank, item in enumerate(vec_results):
            cid = item["id"]
            fused.setdefault(cid, {"item": item, "score": 0.0})
            fused[cid]["score"] += self.weight_vector / (_RRF_K + rank + 1)

        for rank, idx in enumerate(bm25_ranked):
            item = all_items[idx]
            cid = item["id"]
            fused.setdefault(cid, {"item": item, "score": 0.0})
            fused[cid]["score"] += self.weight_bm25 / (_RRF_K + rank + 1)

        ranked = sorted(fused.values(), key=lambda x: x["score"], reverse=True)[:top_k]

        results = []
        for entry in ranked:
            item = entry["item"]
            item = dict(item)
            item["score"] = round(entry["score"], 4)
            results.append(item)

        # 4) 可选重排序
        if self.enable_rerank:
            results = rerank(query, results)

        return results


def get_retriever() -> HybridRetriever:
    """获取全局检索器单例。"""
    from app.core.embeddings.factory import get_embedding
    from app.core.vector_store.factory import get_vector_store

    return HybridRetriever(
        vector_store=get_vector_store(),
        embedding=get_embedding(),
        top_k=settings.RAG_TOP_K,
        weight_vector=settings.HYBRID_WEIGHT_VECTOR,
        weight_bm25=settings.HYBRID_WEIGHT_BM25,
        enable_rerank=settings.ENABLE_RERANK,
    )
