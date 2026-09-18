"""亚马逊库存服务。"""
import logging
from typing import Optional

from app.core.amazon.sp_api_client import get_amazon_client

logger = logging.getLogger(__name__)


def get_inventory_summary(
    marketplace_code: Optional[str] = None,
    granularity_type: str = "Marketplace",
) -> list:
    """获取 FBA 库存汇总。

    Args:
        marketplace_code: 站点代码
        granularity_type: 粒度类型（Marketplace）

    Returns:
        库存汇总列表
    """
    client = get_amazon_client(marketplace_code)
    inventories = client.inventories()

    try:
        response = inventories.get_inventory_summary(
            granularity_type=granularity_type,
            marketplace_ids=[client.marketplace_config["marketplace_id"]],
        )
        summaries = response.payload.get("inventorySummaries", [])
        logger.info(f"获取到 {len(summaries)} 条库存汇总")
        return summaries
    except Exception as e:
        logger.error(f"获取库存汇总失败: {e}")
        raise
