"""亚马逊 SP-API 集成接口。"""
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.api.v1.auth import require_user
from app.config import settings
from app.core.amazon import auth as amazon_auth
from app.core.amazon.marketplaces import list_marketplaces
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.amazon import ai_bridge, inventory, orders, products, reports

router = APIRouter()


# ============ OAuth 授权 ============


@router.get("/oauth/authorize", summary="发起亚马逊 OAuth 授权")
def authorize(marketplace: str = "US", user: dict = Depends(require_user)):
    """生成亚马逊授权 URL，前端跳转到该 URL 进行卖家授权。"""
    state = secrets.token_urlsafe(16)
    url = amazon_auth.get_authorization_url(state=state)
    return {"authorization_url": url, "state": state, "marketplace": marketplace}


@router.get("/oauth/callback", summary="OAuth 授权回调")
async def oauth_callback(
    spapi_oauth_code: str = Query(..., alias="spapi_oauth_code"),
    state: Optional[str] = None,
):
    """亚马逊授权回调，用授权码换取 refresh_token。

    注意：实际生产中应将 refresh_token 加密存储到数据库，关联到用户/租户。
    """
    try:
        token_data = await amazon_auth.exchange_authorization_code(spapi_oauth_code)
        return {
            "ok": True,
            "message": "授权成功",
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data.get("expires_in"),
            "token_type": token_data.get("token_type"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"授权失败: {e}")


# ============ 站点管理 ============


@router.get("/marketplaces", summary="列出支持的亚马逊站点")
def get_marketplaces(user: dict = Depends(require_user)):
    """返回所有支持的亚马逊站点及其 Marketplace ID。"""
    return {"marketplaces": list_marketplaces()}


# ============ 订单 ============


@router.get("/orders", summary="获取最近订单")
def get_orders(
    marketplace: Optional[str] = None,
    days: int = 7,
    user: dict = Depends(require_user),
):
    """获取指定站点最近 N 天的订单列表。"""
    try:
        result = orders.get_recent_orders(marketplace_code=marketplace, days=days)
        return {"orders": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单失败: {e}")


@router.get("/orders/{order_id}", summary="获取订单详情")
def get_order_detail(order_id: str, marketplace: Optional[str] = None, user: dict = Depends(require_user)):
    """获取单个订单的详细信息。"""
    try:
        return orders.get_order_detail(order_id, marketplace_code=marketplace)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单详情失败: {e}")


@router.get("/orders/{order_id}/items", summary="获取订单商品明细")
def get_order_items(order_id: str, marketplace: Optional[str] = None, user: dict = Depends(require_user)):
    """获取订单中的商品列表。"""
    try:
        result = orders.get_order_items(order_id, marketplace_code=marketplace)
        return {"items": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单商品失败: {e}")


# ============ 商品 ============


@router.get("/catalog/search", summary="搜索亚马逊商品目录")
def search_catalog(
    keywords: str,
    marketplace: Optional[str] = None,
    page_size: int = 10,
    user: dict = Depends(require_user),
):
    """在亚马逊目录中搜索商品。"""
    try:
        result = products.search_catalog_items(
            keywords=keywords, marketplace_code=marketplace, page_size=page_size
        )
        return {"items": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索商品失败: {e}")


@router.get("/catalog/{asin}", summary="获取商品详情")
def get_catalog_item(asin: str, marketplace: Optional[str] = None, user: dict = Depends(require_user)):
    """通过 ASIN 获取商品详情。"""
    try:
        return products.get_catalog_item(asin, marketplace_code=marketplace)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取商品详情失败: {e}")


# ============ 库存 ============


@router.get("/inventory/summary", summary="获取 FBA 库存汇总")
def get_inventory_summary(
    marketplace: Optional[str] = None, user: dict = Depends(require_user)
):
    """获取 FBA 库存汇总信息。"""
    try:
        result = inventory.get_inventory_summary(marketplace_code=marketplace)
        return {"summaries": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取库存汇总失败: {e}")


# ============ 报表 ============


@router.post("/reports", summary="创建报表请求")
def create_report(
    report_type: str,
    marketplace: Optional[str] = None,
    data_start_time: Optional[str] = None,
    data_end_time: Optional[str] = None,
    user: dict = Depends(require_user),
):
    """创建亚马逊报表请求。

    常用报表类型:
    - GET_FLAT_FILE_OPEN_LISTINGS_DATA: 在售商品
    - GET_AFN_INVENTORY_DATA: FBA 库存
    - GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL: 全部订单
    - GET_BUSINESS_REPORTS_BY_ASIN: 业务报表（按 ASIN）
    """
    try:
        result = reports.create_report(
            report_type=report_type,
            marketplace_code=marketplace,
            data_start_time=data_start_time,
            data_end_time=data_end_time,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建报表失败: {e}")


@router.get("/reports/{report_id}", summary="获取报表状态")
def get_report_status(report_id: str, marketplace: Optional[str] = None, user: dict = Depends(require_user)):
    """查询报表的处理状态。"""
    try:
        return reports.get_report(report_id, marketplace_code=marketplace)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报表状态失败: {e}")


@router.get("/reports/documents/{document_id}", summary="获取报表文档")
def get_report_document(
    document_id: str, marketplace: Optional[str] = None, user: dict = Depends(require_user)
):
    """获取报表文档的下载 URL。"""
    try:
        return reports.get_report_document(document_id, marketplace_code=marketplace)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报表文档失败: {e}")


# ============ AI 联动功能 ============


@router.get("/ai/analyze-orders", summary="订单数据智能分析")
def analyze_orders_with_ai(
    marketplace: Optional[str] = None,
    days: int = 7,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user),
):
    """基于订单数据生成 AI 销售分析报告。

    分析维度：
    - 订单量趋势
    - 热销商品 Top N
    - 客单价分析
    - 订单状态分布
    - AI 生成的洞察和建议
    """
    try:
        return ai_bridge.analyze_order_trends(
            db, marketplace_code=marketplace, days=days
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"订单分析失败: {e}")


@router.post("/ai/generate-copy-from-orders", summary="基于热销订单生成文案")
def generate_copy_from_orders(
    marketplace: Optional[str] = None,
    days: int = 7,
    top_n: int = 5,
    target_language: str = "en",
    db: Session = Depends(get_db),
    user: dict = Depends(require_user),
):
    """从热销订单中提取商品信息，自动生成营销文案。

    流程：
    1. 拉取最近订单，统计热销商品
    2. 提取商品信息（名称、ASIN）
    3. 为每个热销商品生成多语言营销文案
    """
    try:
        results = ai_bridge.generate_copywriting_from_orders(
            db,
            marketplace_code=marketplace,
            days=days,
            top_n=top_n,
            target_language=target_language,
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文案生成失败: {e}")


@router.get("/ai/order-context/{order_id}", summary="获取订单上下文（客服用）")
def get_order_context_for_chat(
    order_id: str,
    marketplace: Optional[str] = None,
    user: dict = Depends(require_user),
):
    """为智能客服获取订单上下文信息。

    当用户咨询订单相关问题时，客服系统可调用此接口获取订单详情，
    作为 RAG 上下文的一部分，让 AI 客服能回答订单相关问题。
    """
    try:
        return ai_bridge.get_order_context_for_chat(
            order_id, marketplace_code=marketplace
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订单上下文失败: {e}")


@router.post("/ai/translate-order-descriptions", summary="批量翻译商品描述")
def translate_order_descriptions(
    asin_list: list[str],
    target_language: str = "zh",
    marketplace: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user),
):
    """批量翻译订单中的商品描述。

    用于将亚马逊商品描述翻译为目标语言，方便国内运营团队查看。
    """
    try:
        results = ai_bridge.translate_order_descriptions(
            db,
            asin_list=asin_list,
            target_language=target_language,
            marketplace_code=marketplace,
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {e}")
