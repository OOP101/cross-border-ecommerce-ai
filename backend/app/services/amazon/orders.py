"""亚马逊订单服务。"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.config import settings
from app.core.amazon.sp_api_client import get_amazon_client

logger = logging.getLogger(__name__)


def get_recent_orders(
    marketplace_code: Optional[str] = None,
    days: int = 7,
    order_statuses: Optional[list] = None,
) -> list:
    """获取最近 N 天的订单。

    Args:
        marketplace_code: 站点代码
        days: 查询天数范围
        order_statuses: 订单状态过滤，如 ["Shipped", "Unshipped"]

    Returns:
        订单列表
    """
    if settings.AMAZON_MOCK_MODE:
        logger.info("[Mock] 返回模拟订单数据")
        now = datetime.utcnow()
        return [
            {
                "AmazonOrderId": "MOCK-001-1234567-1234567",
                "OrderStatus": "Shipped",
                "PurchaseDate": (now - timedelta(days=1)).isoformat(),
                "OrderTotal": {"CurrencyCode": "USD", "Amount": "89.99"},
                "ShippingAddress": {"City": "New York", "CountryCode": "US"},
            },
            {
                "AmazonOrderId": "MOCK-001-1234567-1234568",
                "OrderStatus": "Unshipped",
                "PurchaseDate": (now - timedelta(days=2)).isoformat(),
                "OrderTotal": {"CurrencyCode": "USD", "Amount": "149.50"},
                "ShippingAddress": {"City": "Los Angeles", "CountryCode": "US"},
            },
            {
                "AmazonOrderId": "MOCK-001-1234567-1234569",
                "OrderStatus": "Shipped",
                "PurchaseDate": (now - timedelta(days=3)).isoformat(),
                "OrderTotal": {"CurrencyCode": "USD", "Amount": "59.99"},
                "ShippingAddress": {"City": "Chicago", "CountryCode": "US"},
            },
        ]

    client = get_amazon_client(marketplace_code)
    orders_api = client.orders()

    created_after = (datetime.utcnow() - timedelta(days=days)).isoformat()

    params = {
        "created_after": created_after,
        "marketplace_ids": [client.marketplace_config["marketplace_id"]],
    }
    if order_statuses:
        params["order_statuses"] = order_statuses

    try:
        response = orders_api.get_orders(**params)
        orders = response.payload.get("Orders", [])
        logger.info(f"获取到 {len(orders)} 个订单（站点: {client.marketplace_code}）")
        return orders
    except Exception as e:
        logger.error(f"获取订单失败: {e}")
        raise


def get_order_detail(order_id: str, marketplace_code: Optional[str] = None) -> dict:
    """获取单个订单详情。

    Args:
        order_id: 亚马逊订单 ID
        marketplace_code: 站点代码

    Returns:
        订单详情
    """
    if settings.AMAZON_MOCK_MODE:
        logger.info(f"[Mock] 返回模拟订单详情 (order_id={order_id})")
        now = datetime.utcnow()
        return {
            "AmazonOrderId": order_id,
            "OrderStatus": "Shipped",
            "PurchaseDate": (now - timedelta(days=1)).isoformat(),
            "OrderTotal": {"CurrencyCode": "USD", "Amount": "89.99"},
            "ShippingAddress": {"City": "New York", "CountryCode": "US"},
        }

    client = get_amazon_client(marketplace_code)
    orders_api = client.orders()

    try:
        response = orders_api.get_order(order_id)
        return response.payload
    except Exception as e:
        logger.error(f"获取订单详情失败 (order_id={order_id}): {e}")
        raise


def get_order_items(order_id: str, marketplace_code: Optional[str] = None) -> list:
    """获取订单商品明细。

    Args:
        order_id: 亚马逊订单 ID
        marketplace_code: 站点代码

    Returns:
        订单商品列表
    """
    if settings.AMAZON_MOCK_MODE:
        logger.info(f"[Mock] 返回模拟订单商品 (order_id={order_id})")
        return [
            {
                "ASIN": "B08N5WRWNW",
                "Title": "Wireless Bluetooth Headphones",
                "QuantityOrdered": 1,
                "ItemPrice": {"CurrencyCode": "USD", "Amount": "89.99"},
            },
        ]

    client = get_amazon_client(marketplace_code)
    orders_api = client.orders()

    try:
        response = orders_api.get_order_items(order_id)
        return response.payload.get("OrderItems", [])
    except Exception as e:
        logger.error(f"获取订单商品失败 (order_id={order_id}): {e}")
        raise
