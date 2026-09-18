"""亚马逊站点配置。"""
from typing import Dict


# 各站点 Marketplace ID 和区域配置
MARKETPLACES: Dict[str, Dict] = {
    "US": {
        "marketplace_id": "ATVPDKIKX0DER",
        "region": "us-east-1",
        "endpoint": "https://sellingpartnerapi-na.amazon.com",
        "currency": "USD",
        "name": "美国",
    },
    "CA": {
        "marketplace_id": "A2EUQ1WTGCTBG2",
        "region": "us-east-1",
        "endpoint": "https://sellingpartnerapi-na.amazon.com",
        "currency": "CAD",
        "name": "加拿大",
    },
    "UK": {
        "marketplace_id": "A1F83G8C2ARO7P",
        "region": "eu-west-1",
        "endpoint": "https://sellingpartnerapi-eu.amazon.com",
        "currency": "GBP",
        "name": "英国",
    },
    "DE": {
        "marketplace_id": "A1PA6795UKMFR9",
        "region": "eu-west-1",
        "endpoint": "https://sellingpartnerapi-eu.amazon.com",
        "currency": "EUR",
        "name": "德国",
    },
    "FR": {
        "marketplace_id": "A13V1IB3VIYZZH",
        "region": "eu-west-1",
        "endpoint": "https://sellingpartnerapi-eu.amazon.com",
        "currency": "EUR",
        "name": "法国",
    },
    "IT": {
        "marketplace_id": "APJ6JRA9NG5V4",
        "region": "eu-west-1",
        "endpoint": "https://sellingpartnerapi-eu.amazon.com",
        "currency": "EUR",
        "name": "意大利",
    },
    "ES": {
        "marketplace_id": "A1RKKUPIHCS9HS",
        "region": "eu-west-1",
        "endpoint": "https://sellingpartnerapi-eu.amazon.com",
        "currency": "EUR",
        "name": "西班牙",
    },
    "JP": {
        "marketplace_id": "A1VC38T7YXB528",
        "region": "us-west-2",
        "endpoint": "https://sellingpartnerapi-fe.amazon.com",
        "currency": "JPY",
        "name": "日本",
    },
    "AU": {
        "marketplace_id": "A39IBJ37TRP1C6",
        "region": "us-west-2",
        "endpoint": "https://sellingpartnerapi-fe.amazon.com",
        "currency": "AUD",
        "name": "澳大利亚",
    },
    "IN": {
        "marketplace_id": "A21TJRUUN4KGV",
        "region": "us-west-2",
        "endpoint": "https://sellingpartnerapi-fe.amazon.com",
        "currency": "INR",
        "name": "印度",
    },
}


def get_marketplace(code: str) -> Dict:
    """获取指定站点配置。"""
    if code not in MARKETPLACES:
        raise ValueError(f"不支持的站点: {code}，可选: {list(MARKETPLACES.keys())}")
    return MARKETPLACES[code]


def list_marketplaces() -> Dict[str, Dict]:
    """列出所有支持的站点。"""
    return MARKETPLACES
