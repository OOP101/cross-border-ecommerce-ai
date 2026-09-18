"""订单数据与 AI 模块联动服务。

核心功能：
1. 订单智能分析 — 基于订单数据生成销售洞察
2. 热销商品文案生成 — 从热销订单中提取商品信息，自动生成营销文案
3. 客服订单查询 — 智能客服可查询订单上下文
4. 翻译联动 — 订单商品描述多语言翻译
"""
import logging
from collections import Counter
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.llm.base import extract_usage
from app.core.llm.factory import get_llm
from app.db.models import ApiUsage
from app.services.amazon import orders as amazon_orders

logger = logging.getLogger(__name__)


def analyze_order_trends(
    db: Session,
    marketplace_code: Optional[str] = None,
    days: int = 7,
) -> Dict:
    """基于订单数据生成智能销售分析。

    分析维度：
    - 订单量趋势
    - 热销商品 Top N
    - 客单价分析
    - 订单状态分布

    Returns:
        包含 AI 生成的分析结论和原始数据
    """
    # 1. 拉取订单数据
    order_list = amazon_orders.get_recent_orders(
        marketplace_code=marketplace_code, days=days
    )

    if not order_list:
        return {
            "analysis": "暂无订单数据",
            "stats": {"total_orders": 0},
        }

    # 2. 基础统计
    total_orders = len(order_list)
    total_amount = sum(
        float(o.get("OrderTotal", {}).get("Amount", 0))
        for o in order_list
        if o.get("OrderTotal")
    )
    avg_order_value = total_amount / total_orders if total_orders > 0 else 0

    # 3. 订单状态分布
    status_counter = Counter(o.get("OrderStatus", "Unknown") for o in order_list)
    status_distribution = dict(status_counter)

    # 4. 热销商品分析（需要拉取订单明细）
    product_counter = Counter()
    for order in order_list[:20]:  # 限制分析前 20 个订单，避免 API 调用过多
        order_id = order.get("AmazonOrderId")
        if order_id:
            try:
                items = amazon_orders.get_order_items(order_id, marketplace_code)
                for item in items:
                    title = item.get("Title", "Unknown")
                    quantity = int(item.get("QuantityOrdered", 1))
                    product_counter[title] += quantity
            except Exception as e:
                logger.warning(f"获取订单明细失败 (order_id={order_id}): {e}")

    top_products = product_counter.most_common(10)

    # 5. AI 生成分析结论
    llm = get_llm()
    prompt = f"""你是一名跨境电商数据分析师，请基于以下订单数据生成简洁的销售分析报告：

【数据概览】
- 统计周期：最近 {days} 天
- 订单总数：{total_orders}
- 总销售额：{total_amount:.2f}
- 平均客单价：{avg_order_value:.2f}

【订单状态分布】
{status_distribution}

【热销商品 Top 10】
{chr(10).join(f'{i+1}. {name}（销量: {qty}）' for i, (name, qty) in enumerate(top_products))}

请输出：
1. 一句话总结当前销售状况
2. 2-3 条关键洞察（如趋势、问题、机会）
3. 1-2 条可执行的建议

用中文回答，简洁专业。"""

    result = llm.generate(prompt, task="amazon_analysis")
    analysis_text = result.content

    # 记录 API 调用
    prompt_tokens, completion_tokens = extract_usage(result, prompt, analysis_text)
    db.add(
        ApiUsage(
            endpoint="/amazon/ai/analyze",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
    )
    db.commit()

    return {
        "analysis": analysis_text,
        "stats": {
            "total_orders": total_orders,
            "total_amount": round(total_amount, 2),
            "avg_order_value": round(avg_order_value, 2),
            "status_distribution": status_distribution,
            "top_products": [{"name": name, "quantity": qty} for name, qty in top_products],
        },
    }


def generate_copywriting_from_orders(
    db: Session,
    marketplace_code: Optional[str] = None,
    days: int = 7,
    top_n: int = 5,
    target_language: str = "en",
) -> List[Dict]:
    """基于热销订单自动生成营销文案。

    流程：
    1. 拉取最近订单，统计热销商品
    2. 提取商品信息（名称、品类、卖点）
    3. 调用文案生成服务，为每个热销商品生成多语言文案

    Returns:
        每个热销商品的文案生成结果
    """
    # 1. 获取热销商品
    order_list = amazon_orders.get_recent_orders(
        marketplace_code=marketplace_code, days=days
    )

    product_counter = Counter()
    product_info = {}  # asin -> {title, category, ...}

    for order in order_list[:30]:
        order_id = order.get("AmazonOrderId")
        if order_id:
            try:
                items = amazon_orders.get_order_items(order_id, marketplace_code)
                for item in items:
                    asin = item.get("ASIN", "")
                    title = item.get("Title", "Unknown")
                    quantity = int(item.get("QuantityOrdered", 1))
                    product_counter[asin] += quantity
                    if asin not in product_info:
                        product_info[asin] = {
                            "title": title,
                            "asin": asin,
                        }
            except Exception as e:
                logger.warning(f"获取订单明细失败: {e}")

    # 2. 取 Top N 热销商品
    top_asins = [asin for asin, _ in product_counter.most_common(top_n)]

    # 3. 为每个商品生成文案
    from app.services import copywriting as copy_service

    results = []
    for asin in top_asins:
        info = product_info.get(asin, {})
        title = info.get("title", "")
        if not title:
            continue

        try:
            # 调用文案生成服务
            copy_result = copy_service.generate_copywriting(
                db,
                copy_type="product",
                product_name=title,
                category="",  # 可从 catalog 补充
                selling_points="",
                target_market=marketplace_code or "US",
                target_language=target_language,
            )
            results.append({
                "asin": asin,
                "title": title,
                "copywriting": copy_result,
            })
        except Exception as e:
            logger.error(f"生成文案失败 (asin={asin}): {e}")
            results.append({
                "asin": asin,
                "title": title,
                "error": str(e),
            })

    return results


def get_order_context_for_chat(
    order_id: str,
    marketplace_code: Optional[str] = None,
) -> Dict:
    """为智能客服获取订单上下文信息。

    当用户咨询订单相关问题时，客服系统可调用此函数获取订单详情，
    作为 RAG 上下文的一部分，让 AI 客服能回答订单相关问题。

    Returns:
        订单上下文（包含订单详情、商品列表、物流状态等）
    """
    try:
        order = amazon_orders.get_order_detail(order_id, marketplace_code)
        items = amazon_orders.get_order_items(order_id, marketplace_code)

        # 构建上下文文本
        context_parts = [
            f"【订单信息】",
            f"订单号: {order.get('AmazonOrderId', order_id)}",
            f"订单状态: {order.get('OrderStatus', '未知')}",
            f"下单时间: {order.get('PurchaseDate', '未知')}",
            f"订单金额: {order.get('OrderTotal', {}).get('Amount', '未知')} {order.get('OrderTotal', {}).get('CurrencyCode', '')}",
            f"收货地址: {order.get('ShippingAddress', {}).get('City', '')} {order.get('ShippingAddress', {}).get('CountryCode', '')}",
            "",
            "【商品列表】",
        ]

        for item in items:
            context_parts.append(
                f"- {item.get('Title', '未知商品')} x{item.get('QuantityOrdered', 1)} "
                f"(ASIN: {item.get('ASIN', '')})"
            )

        return {
            "order_id": order_id,
            "context_text": "\n".join(context_parts),
            "order_data": order,
            "items": items,
        }
    except Exception as e:
        logger.error(f"获取订单上下文失败: {e}")
        return {
            "order_id": order_id,
            "context_text": f"无法获取订单信息: {e}",
            "error": str(e),
        }


def translate_order_descriptions(
    db: Session,
    asin_list: List[str],
    target_language: str = "zh",
    marketplace_code: Optional[str] = None,
) -> List[Dict]:
    """批量翻译订单中的商品描述。

    用于将亚马逊商品描述翻译为目标语言，方便国内运营团队查看。

    Returns:
        每个 ASIN 的翻译结果
    """
    from app.services import translation as translate_service
    from app.services.amazon import products as amazon_products

    results = []
    for asin in asin_list:
        try:
            # 获取商品详情
            item = amazon_products.get_catalog_item(asin, marketplace_code)
            title = item.get("title", "")

            if title:
                # 调用翻译服务
                trans_result = translate_service.translate(
                    db,
                    text=title,
                    source_language="en",
                    target_language=target_language,
                )
                results.append({
                    "asin": asin,
                    "original": title,
                    "translation": trans_result.get("translation", ""),
                    "source": trans_result.get("source", "llm"),
                })
            else:
                results.append({
                    "asin": asin,
                    "original": "",
                    "translation": "",
                    "error": "无法获取商品标题",
                })
        except Exception as e:
            logger.error(f"翻译商品失败 (asin={asin}): {e}")
            results.append({
                "asin": asin,
                "error": str(e),
            })

    return results
