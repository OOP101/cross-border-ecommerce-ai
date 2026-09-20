"""亚马逊商品服务。"""
import logging
from typing import Optional

from app.config import settings
from app.core.amazon.sp_api_client import get_amazon_client

logger = logging.getLogger(__name__)


def search_catalog_items(
    keywords: str,
    marketplace_code: Optional[str] = None,
    page_size: int = 10,
) -> list:
    """在亚马逊目录中搜索商品。

    Args:
        keywords: 搜索关键词
        marketplace_code: 站点代码
        page_size: 返回数量

    Returns:
        商品列表
    """
    if settings.AMAZON_MOCK_MODE:
        logger.info(f"[Mock] 返回模拟商品搜索结果 (keywords={keywords})")
        return [
            {
                "asin": "B08N5WRWNW",
                "title": f"Mock Product - {keywords}",
                "brand": "MockBrand",
                "price": {"amount": 89.99, "currency_code": "USD"},
            },
        ]

    client = get_amazon_client(marketplace_code)
    catalog = client.catalog_items()

    try:
        response = catalog.search_catalog_items(
            keywords=keywords,
            marketplace_ids=[client.marketplace_config["marketplace_id"]],
            page_size=page_size,
        )
        items = response.payload.get("items", [])
        logger.info(f"搜索到 {len(items)} 个商品（关键词: {keywords}）")
        return items
    except Exception as e:
        logger.error(f"搜索商品失败: {e}")
        raise


def get_catalog_item(asin: str, marketplace_code: Optional[str] = None) -> dict:
    """获取单个商品详情（通过 ASIN）。

    Args:
        asin: 亚马逊标准识别号
        marketplace_code: 站点代码

    Returns:
        商品详情
    """
    if settings.AMAZON_MOCK_MODE:
        logger.info(f"[Mock] 返回模拟商品详情 (asin={asin})")
        return {
            "asin": asin,
            "title": "Mock Product Title",
            "brand": "MockBrand",
            "price": {"amount": 89.99, "currency_code": "USD"},
        }

    client = get_amazon_client(marketplace_code)
    catalog = client.catalog_items()

    try:
        response = catalog.get_catalog_item(
            asin=asin,
            marketplace_ids=[client.marketplace_config["marketplace_id"]],
        )
        return response.payload
    except Exception as e:
        logger.error(f"获取商品详情失败 (asin={asin}): {e}")
        raise
