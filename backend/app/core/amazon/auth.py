"""亚马逊 LWA OAuth 授权流程。"""
import logging
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# LWA 授权端点
LWA_AUTH_URL = "https://www.amazon.com/ap/oa"
LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"


def get_authorization_url(state: str = "") -> str:
    """生成 LWA 授权 URL，引导卖家跳转到亚马逊授权页面。

    Args:
        state: 防 CSRF 攻击的随机字符串

    Returns:
        完整的授权 URL
    """
    if settings.AMAZON_MOCK_MODE:
        logger.info("[Mock] 返回模拟授权 URL")
        return f"http://localhost:8009/api/v1/amazon/oauth/callback?spapi_oauth_code=mock_auth_code&state={state}"

    params = {
        "client_id": settings.AMAZON_LWA_CLIENT_ID,
        "scope": "sellingpartnerapi::orders sellingpartnerapi::products sellingpartnerapi::inventory sellingpartnerapi::reports",
        "response_type": "code",
        "redirect_uri": settings.AMAZON_OAUTH_REDIRECT_URI,
        "state": state,
    }
    return f"{LWA_AUTH_URL}?{urlencode(params)}"


async def exchange_authorization_code(auth_code: str) -> dict:
    """用授权码换取 refresh_token。

    Args:
        auth_code: 授权码（从回调 URL 中获取）

    Returns:
        包含 refresh_token、access_token 等信息的字典
    """
    if settings.AMAZON_MOCK_MODE:
        logger.info("[Mock] 返回模拟 token 数据")
        return {
            "access_token": "mock_access_token_xxxxx",
            "refresh_token": "mock_refresh_token_xxxxx",
            "token_type": "bearer",
            "expires_in": 3600,
        }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            LWA_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": auth_code,
                "client_id": settings.AMAZON_LWA_CLIENT_ID,
                "client_secret": settings.AMAZON_LWA_CLIENT_SECRET,
                "redirect_uri": settings.AMAZON_OAUTH_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: Optional[str] = None) -> str:
    """用 refresh_token 刷新 access_token。

    Args:
        refresh_token: 刷新令牌，若未提供则使用配置中的默认值

    Returns:
        新的 access_token
    """
    if settings.AMAZON_MOCK_MODE:
        logger.info("[Mock] 返回模拟 access_token")
        return "mock_access_token_xxxxx"

    token = refresh_token or settings.AMAZON_LWA_REFRESH_TOKEN
    if not token:
        raise ValueError("未提供 refresh_token，请先完成 OAuth 授权")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            LWA_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": token,
                "client_id": settings.AMAZON_LWA_CLIENT_ID,
                "client_secret": settings.AMAZON_LWA_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        data = response.json()
        return data["access_token"]
