"""智能文案生成服务：商品描述 / 广告语 / 活动文案 / SEO 标签，多语言。"""
import asyncio
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.llm.base import extract_usage
from app.core.llm.factory import get_llm
from app.db.models import ApiUsage

logger = logging.getLogger(__name__)

_LANG_NAMES = {
    "en": "English", "fr": "French", "es": "Spanish", "ar": "Arabic",
    "ja": "Japanese", "ko": "Korean", "de": "German", "ru": "Russian",
    "pt": "Portuguese", "it": "Italian", "zh": "Chinese",
}


def _system(style: str, tone: str) -> str:
    return (
        f"你是一名资深的跨境电商营销文案专家。"
        f"请以【{style or '专业'}】风格、【{tone or '亲切'}】语气创作，"
        "文案需突出卖点、符合目标市场文化、可直接投放。"
    )


_SPEC = {
    "title": ("copywriting_title", "请生成商品标题。"),
    "description": ("copywriting_description", "请生成商品详情描述。"),
    "ad": ("copywriting_ad", "请生成一条适用于 Google/Facebook 投放的广告语。"),
    "campaign": ("copywriting_title", "请生成促销活动主题文案。"),
    "keywords": ("copywriting_keywords", "请生成 SEO 关键词标签（逗号分隔）。"),
}

_TYPE_KEYS = {
    "ad": ["ad"],
    "campaign": ["campaign"],
    "keywords": ["keywords"],
    "product": ["title", "description", "keywords"],
    "all": ["title", "description", "ad", "keywords"],
}


async def generate_copywriting_async(
    db: Session,
    copy_type: str,
    product_name: str,
    category: Optional[str] = "",
    selling_points: Optional[str] = "",
    target_market: Optional[str] = "",
    target_language: str = "en",
    style: Optional[str] = "",
    tone: Optional[str] = "",
) -> dict:
    """生成营销文案，copy_type: product | ad | campaign | keywords | all。

    多段文案（product/all）通过 asyncio.gather 并发调用 LLM，延迟约为最慢一段。
    """
    lang_name = _LANG_NAMES.get(target_language, target_language)
    base = (
        f"商品名称：{product_name}\n"
        f"品类：{category}\n"
        f"卖点关键词：{selling_points}\n"
        f"目标市场：{target_market}\n"
        f"目标语言：{target_language}（{lang_name}）\n"
    )

    llm = get_llm()
    system = _system(style, tone)
    usage_rows: List[ApiUsage] = []

    async def _gen(task: str, extra: str) -> str:
        r = await llm.agenerate(base + extra, system=system, task=task)
        prompt_tokens, completion_tokens = extract_usage(r, base + extra, r.content)
        usage_rows.append(
            ApiUsage(endpoint="/copywriting", prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
        )
        return r.content

    keys = _TYPE_KEYS.get(copy_type, _TYPE_KEYS["all"])
    results = await asyncio.gather(*(_gen(*_SPEC[k]) for k in keys))

    for row in usage_rows:
        db.add(row)
    db.commit()
    return dict(zip(keys, results))


def generate_copywriting(db: Session, **kwargs) -> dict:
    """同步入口（批量等场景使用），内部复用并发的异步实现。"""
    return asyncio.run(generate_copywriting_async(db, **kwargs))


def generate_batch(db: Session, products: List[dict], target_language: str = "en") -> List[dict]:
    """批量生成多商品多语言文案。"""
    results = []
    for p in products:
        try:
            r = generate_copywriting(
                db,
                copy_type="product",
                product_name=p.get("name", ""),
                selling_points=p.get("selling_points", ""),
                target_market=p.get("target_market", ""),
                target_language=target_language,
            )
            results.append({"name": p.get("name"), "ok": True, "result": r})
        except Exception as e:  # noqa: BLE001
            results.append({"name": p.get("name"), "ok": False, "error": str(e)})
    db.commit()
    return results
