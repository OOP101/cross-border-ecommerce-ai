"""亚马逊报表服务。"""
import logging
from typing import Optional

from app.core.amazon.sp_api_client import get_amazon_client

logger = logging.getLogger(__name__)


def create_report(
    report_type: str,
    marketplace_code: Optional[str] = None,
    data_start_time: Optional[str] = None,
    data_end_time: Optional[str] = None,
) -> dict:
    """创建报表请求。

    常用报表类型:
    - GET_FLAT_FILE_OPEN_LISTINGS_DATA: 在售商品报表
    - GET_AFN_INVENTORY_DATA: FBA 库存报表
    - GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL: 订单报表
    - GET_BUSINESS_REPORTS_BY_ASIN: 业务报表（按 ASIN）

    Args:
        report_type: 报表类型
        marketplace_code: 站点代码
        data_start_time: 数据开始时间（ISO 格式）
        data_end_time: 数据结束时间（ISO 格式）

    Returns:
        报表请求信息（包含 reportId）
    """
    client = get_amazon_client(marketplace_code)
    reports_api = client.reports()

    body = {
        "reportType": report_type,
        "marketplaceIds": [client.marketplace_config["marketplace_id"]],
    }
    if data_start_time:
        body["dataStartTime"] = data_start_time
    if data_end_time:
        body["dataEndTime"] = data_end_time

    try:
        response = reports_api.create_report(body)
        report_id = response.payload.get("reportId")
        logger.info(f"报表创建成功 (report_id={report_id}, type={report_type})")
        return response.payload
    except Exception as e:
        logger.error(f"创建报表失败: {e}")
        raise


def get_report(report_id: str, marketplace_code: Optional[str] = None) -> dict:
    """获取报表状态。

    Args:
        report_id: 报表 ID
        marketplace_code: 站点代码

    Returns:
        报表状态信息
    """
    client = get_amazon_client(marketplace_code)
    reports_api = client.reports()

    try:
        response = reports_api.get_report(report_id)
        return response.payload
    except Exception as e:
        logger.error(f"获取报表状态失败 (report_id={report_id}): {e}")
        raise


def get_report_document(report_document_id: str, marketplace_code: Optional[str] = None) -> dict:
    """获取报表文档（下载 URL）。

    Args:
        report_document_id: 报表文档 ID
        marketplace_code: 站点代码

    Returns:
        报表文档信息（包含下载 URL）
    """
    client = get_amazon_client(marketplace_code)
    reports_api = client.reports()

    try:
        response = reports_api.get_report_document(report_document_id)
        return response.payload
    except Exception as e:
        logger.error(f"获取报表文档失败 (document_id={report_document_id}): {e}")
        raise
