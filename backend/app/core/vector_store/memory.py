"""内存向量库：基于 numpy 余弦相似度，支持 JSON 持久化。适合开发与演示。"""
import json
import logging
from pathlib import Path
from typing import List, Optional

import numpy as np

from .base import BaseVectorStore

logger = logging.getLogger(__name__)


class MemoryVectorStore(BaseVectorStore):
    name = "memory"

    def __init__(self, persist_path: Optional[str] = None):
        self.persist_path = Path(persist_path) if persist_path else None
        self._ids: List[str] = []
        self._texts: List[str] = []
        self._metas: List[dict] = []
        self._emb: List[np.ndarray] = []
        self._norm_matrix: Optional[np.ndarray] = None  # 归一化向量矩阵缓存
        self._load()

    # ---- 缓存 ----
    def _invalidate_matrix(self) -> None:
        self._norm_matrix = None

    def _get_norm_matrix(self) -> np.ndarray:
        """惰性构建行归一化向量矩阵；add/delete/加载后由 _invalidate_matrix 失效。"""
        if self._norm_matrix is None:
            if self._emb:
                M = np.stack(self._emb)
                norms = np.linalg.norm(M, axis=1)
                norms[norms == 0] = 1.0
                self._norm_matrix = M / norms[:, None]
            else:
                self._norm_matrix = np.zeros((0, 0), dtype=np.float32)
        return self._norm_matrix

    # ---- 持久化 ----
    def _load(self):
        if not self.persist_path or not self.persist_path.exists():
            return
        try:
            data = json.loads(self.persist_path.read_text(encoding="utf-8"))
            self._ids = data.get("ids", [])
            self._texts = data.get("texts", [])
            self._metas = data.get("metas", [])
            self._emb = [np.array(e, dtype=np.float32) for e in data.get("emb", [])]
            self._invalidate_matrix()
        except Exception as e:  # noqa: BLE001
            logger.warning("加载向量库失败：%s", e)

    def _save(self):
        if not self.persist_path:
            return
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "ids": self._ids,
            "texts": self._texts,
            "metas": self._metas,
            "emb": [e.tolist() for e in self._emb],
        }
        self.persist_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    # ---- 接口实现 ----
    def add(self, ids, texts, embeddings, metadatas=None):
        metadatas = metadatas or [{}] * len(ids)
        changed = False
        for i, t, e, m in zip(ids, texts, embeddings, metadatas):
            if i in self._ids:
                idx = self._ids.index(i)
                self._texts[idx] = t
                self._metas[idx] = m or {}
                self._emb[idx] = np.array(e, dtype=np.float32)
            else:
                self._ids.append(i)
                self._texts.append(t)
                self._metas.append(m or {})
                self._emb.append(np.array(e, dtype=np.float32))
            changed = True
        if changed:
            self._invalidate_matrix()
            self._save()

    def search(self, embedding, top_k=5):
        if not self._emb:
            return []
        q = np.asarray(embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return []
        q = q / q_norm
        M = self._get_norm_matrix()
        sims = M @ q
        top_k = min(top_k, len(sims))
        order = np.argsort(-sims)[:top_k]
        return [
            {
                "id": self._ids[i],
                "text": self._texts[i],
                "score": float(sims[i]),
                "metadata": self._metas[i],
            }
            for i in order
        ]

    def list_all(self):
        return [
            {"id": self._ids[i], "text": self._texts[i], "metadata": self._metas[i]}
            for i in range(len(self._ids))
        ]

    def delete(self, ids):
        id_set = set(ids)
        keep = [idx for idx, x in enumerate(self._ids) if x not in id_set]
        if len(keep) != len(self._ids):
            self._ids = [self._ids[i] for i in keep]
            self._texts = [self._texts[i] for i in keep]
            self._metas = [self._metas[i] for i in keep]
            self._emb = [self._emb[i] for i in keep]
            self._invalidate_matrix()
            self._save()

    def count(self):
        return len(self._ids)
