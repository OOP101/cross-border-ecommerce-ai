"""亚马逊 SP-API 客户端封装。"""
import logging
from typing import Optional

from sp_api.api import Orders, CatalogItems, Inventories, Reports
from sp_api.base import Marketplaces

from app.config import settings
from app.core.amazon.marketplaces import get_marketplace

logger = logging.getLogger(__name__)


class AmazonSPAPIClient:
    """亚马逊 SP-API 客户端管理器。

    封装 python-amazon-sp-api 库，提供统一的 API 访问入口。
    支持多站点切换、自动处理认证和签名。
    """

    def __init__(self, marketplace_code: Optional[str] = None):
        """初始化客户端。

        Args:
            marketplace_code: 站点代码（US/EU/JP 等），默认使用配置中的站点
        """
        self.marketplace_code = marketplace_code or settings.AMAZON_DEFAULT_MARKETPLACE
        self.marketplace_config = get_marketplace(self.marketplace_code)

        # 构建 Credentials 配置
        self.credentials = dict(
            refresh_token=settings.AMAZON_LWA_REFRESH_TOKEN,
            lwa_app_client_id=settings.AMAZON_LWA_CLIENT_ID,
            lwa_client_secret=settings.AMAZON_LWA_CLIENT_SECRET,
            aws_access_key=settings.AMAZON_AWS_ACCESS_KEY,
            aws_secret_key=settings.AMAZON_AWS_SECRET_KEY,
            region=self.marketplace_config["region"],
            role_arn=settings.AMAZON_AWS_ROLE_ARN or None,
        )

    def _get_marketplace(self) -> Marketplaces:
        """获取 sp_api 的 Marketplaces 对象。"""
        return Marketplaces[self.marketplace_code]

    def orders(self) -> Orders:
        """获取 Orders API 客户端。"""
        return Orders(
            credentials=self.credentials,
            marketplace=self._get_marketplace(),
        )

    def catalog_items(self) -> CatalogItems:
        """获取 Catalog Items API 客户端。"""
        return CatalogItems(
            credentials=self.credentials,
            marketplace=self._get_marketplace(),
        )

    def inventories(self) -> Inventories:
        """获取 Inventories API 客户端。"""
        return Inventories(
            credentials=self.credentials,
            marketplace=self._get_marketplace(),
        )

    def reports(self) -> Reports:
        """获取 Reports API 客户端。"""
        return Reports(
            credentials=self.credentials,
            marketplace=self._get_marketplace(),
        )


def get_amazon_client(marketplace_code: Optional[str] = None) -> AmazonSPAPIClient:
    """获取 SP-API 客户端实例。"""
    return AmazonSPAPIClient(marketplace_code)
