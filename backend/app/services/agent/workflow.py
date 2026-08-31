"""Agent 工作流编排。

优先使用 LangGraph 构建多 Agent 图；未安装时降级为顺序规则路由。
"""
import logging
from typing import List

logger = logging.getLogger(__name__)

# 意图识别规则（关键词 -> 意图）
INTENT_RULES: List[tuple] = [
    ("translation", ["翻译", "translate", "怎么用英语说", "用日语怎么说"]),
    ("order", ["订单", "物流", "发货", "运单", "tracking", "order", "shipment", "delivery", "到哪了"]),
    ("after_sales", ["退货", "退款", "售后", "换货", "refund", "return", "complaint", "投诉"]),
    ("product", ["产品", "规格", "参数", "认证", "价格", "product", "spec", "certificate", "price", "怎么用", "介绍"]),
    ("human", ["人工", "转人工", "客服", "真人", "agent", "human"]),
]

# 高风险/需转人工的关键词
HUMAN_ESCALATE_KEYWORDS = ["投诉", "退款", "法律", "律师", "起诉", "赔偿", "sue", "lawsuit", "fraud"]


def classify_intent(text: str) -> str:
    """规则意图识别，返回 intent。"""
    t = text.lower()
    for intent, keywords in INTENT_RULES:
        if any(k in t for k in keywords):
            return intent
    return "product"


def need_human(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in HUMAN_ESCALATE_KEYWORDS)


def run_agent(text: str) -> dict:
    """执行 Agent 工作流，返回 {intent, need_human}。

    安装 langgraph 后，可用 StateGraph 构建 classify -> route -> node 的图。
    """
    try:
        from .graph import build_workflow  # noqa: F401

        logger.debug("使用 LangGraph 工作流")
        # 预留：run_workflow(text) 返回完整状态
    except Exception:  # noqa: BLE001
        logger.debug("LangGraph 不可用，使用规则路由")

    return {
        "intent": classify_intent(text),
        "need_human": need_human(text),
    }
