"""LLM 工厂：根据配置返回对应实现（懒加载，缺失依赖时降级为 mock）。"""
import logging
from functools import lru_cache
from typing import List

from app.config import settings
from .base import BaseLLM
from .mock import MockLLM

logger = logging.getLogger(__name__)


def _parse_failover(raw: str) -> List[dict]:
    """解析 LLM_FAILOVER 配置："base_url|api_key|model;base_url|api_key|model"。"""
    endpoints = []
    for item in raw.split(";"):
        item = item.strip()
        if not item:
            continue
        parts = item.split("|")
        if len(parts) != 3 or not all(p.strip() for p in parts):
            logger.warning("LLM_FAILOVER 条目格式无效(应为 base_url|api_key|model)：%r", item)
            continue
        endpoints.append({"base_url": parts[0].strip(), "api_key": parts[1].strip(), "model": parts[2].strip()})
    return endpoints


@lru_cache
def get_llm() -> BaseLLM:
    provider = settings.LLM_PROVIDER
    if provider == "openai_compatible":
        if not settings.LLM_API_KEY:
            logger.warning("LLM_PROVIDER=openai_compatible 但未配置 LLM_API_KEY，回退到 mock")
            return MockLLM()
        try:
            from .openai_compatible import OpenAICompatibleLLM

            fallbacks = _parse_failover(settings.LLM_FAILOVER)
            if fallbacks:
                logger.info("LLM 故障转移已启用，备用端点: %s", [f["model"] for f in fallbacks])
            return OpenAICompatibleLLM(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_BASE_URL,
                model=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                timeout=settings.LLM_TIMEOUT,
                fallbacks=fallbacks,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("初始化 openai_compatible LLM 失败：%s，回退到 mock", e)
            return MockLLM()

    return MockLLM()


def llm_failover_models() -> List[str]:
    """管理后台展示用：备用端点模型列表。"""
    return [f["model"] for f in _parse_failover(settings.LLM_FAILOVER)]
