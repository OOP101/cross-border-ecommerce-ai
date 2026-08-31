"""重排序：heuristic（默认，零依赖）与 cross_encoder（真实重排模型）两种实现。

通过配置 RERANK_PROVIDER 切换：
- heuristic：关键词覆盖率 + 向量得分加权，无需额外依赖；
- cross_encoder：sentence-transformers CrossEncoder（如 BAAI/bge-reranker），
  对 (query, 文档) 联合编码打分，精度更高；未安装依赖时自动回退 heuristic。
"""
import logging
from typing import List

from app.config import settings
from app.utils.text_utils import tokenize

logger = logging.getLogger(__name__)

_cross_encoder = None
_cross_encoder_failed = False


def _get_cross_encoder():
    """惰性加载交叉编码器；加载失败时返回 None（调用方回退 heuristic）。"""
    global _cross_encoder, _cross_encoder_failed
    if _cross_encoder is not None or _cross_encoder_failed:
        return _cross_encoder
    try:
        from sentence_transformers import CrossEncoder

        _cross_encoder = CrossEncoder(settings.RERANK_MODEL, max_length=512)
        logger.info("已加载重排序模型: %s", settings.RERANK_MODEL)
    except Exception as e:  # noqa: BLE001
        _cross_encoder_failed = True
        logger.warning("加载 cross_encoder 失败（%s），回退 heuristic 重排。", e)
    return _cross_encoder


def _rerank_cross_encoder(query: str, items: List[dict]) -> List[dict]:
    model = _get_cross_encoder()
    if model is None:
        return _rerank_heuristic(query, items)
    pairs = [(query, item.get("text", "")) for item in items]
    scores = model.predict(pairs)
    scored = []
    for item, s in zip(items, scores):
        entry = dict(item)
        entry["_rerank_score"] = float(s)
        scored.append(entry)
    scored.sort(key=lambda x: x["_rerank_score"], reverse=True)
    return scored


def _rerank_heuristic(query: str, items: List[dict]) -> List[dict]:
    q_tokens = set(tokenize(query))
    scored = []
    for item in items:
        entry = dict(item)
        doc_tokens = tokenize(entry.get("text", ""))
        if not doc_tokens:
            entry["_rerank_score"] = entry.get("score", 0.0)
        else:
            coverage = len(q_tokens & set(doc_tokens)) / len(q_tokens) if q_tokens else 0.0
            entry["_rerank_score"] = 0.5 * entry.get("score", 0.0) + 0.5 * coverage
        scored.append(entry)
    scored.sort(key=lambda x: x["_rerank_score"], reverse=True)
    return scored


def rerank(query: str, items: List[dict]) -> List[dict]:
    """对候选片段重排序。内部打分字段不写入返回结果，避免泄漏到 API 响应。"""
    if not items:
        return items
    provider = settings.RERANK_PROVIDER
    if provider == "cross_encoder":
        scored = _rerank_cross_encoder(query, items)
    else:
        scored = _rerank_heuristic(query, items)
    for entry in scored:
        entry.pop("_rerank_score", None)
    return scored
