"""数据洞察与智能营销统计服务。"""
import json
import logging
from collections import Counter
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import ApiUsage, Conversation, Feedback

logger = logging.getLogger(__name__)


def dashboard(db: Session, tenant_id: str = "default") -> Dict:
    """核心运营看板数据（按租户隔离）。"""
    total_conversations = (
        db.query(func.count(Conversation.id))
        .filter(Conversation.tenant_id == tenant_id)
        .scalar() or 0
    )
    avg_latency = (
        db.query(func.avg(Conversation.latency_ms))
        .filter(Conversation.tenant_id == tenant_id)
        .scalar() or 0
    )
    avg_rating = (
        db.query(func.avg(Feedback.rating))
        .join(Conversation, Feedback.conversation_id == Conversation.id)
        .filter(Conversation.tenant_id == tenant_id)
        .scalar() or 0
    )

    # 意图分布
    intent_rows = (
        db.query(Conversation.intent, func.count(Conversation.intent))
        .filter(Conversation.tenant_id == tenant_id)
        .group_by(Conversation.intent)
        .all()
    )
    intent_distribution = [{"intent": i, "count": c} for i, c in intent_rows] or []

    # Token 消耗：ApiUsage 暂为平台级口径（未按租户拆分），后续为该表加租户列后接入过滤
    total_prompt = db.query(func.sum(ApiUsage.prompt_tokens)).scalar() or 0
    total_completion = db.query(func.sum(ApiUsage.completion_tokens)).scalar() or 0

    # 近 7 日对话趋势
    trend = _daily_trend(db, tenant_id=tenant_id)

    return {
        "kpi": {
            "total_conversations": total_conversations,
            "avg_latency_ms": round(avg_latency, 1),
            "avg_rating": round(avg_rating, 2),
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
        },
        "intent_distribution": intent_distribution,
        "conversation_trend": trend,
    }


def _daily_trend(db: Session, days: int = 7, tenant_id: str = "default") -> List[dict]:
    rows = (
        db.query(func.date(Conversation.created_at), func.count(Conversation.id))
        .filter(Conversation.tenant_id == tenant_id)
        .group_by(func.date(Conversation.created_at))
        .order_by(func.date(Conversation.created_at).desc())
        .limit(days)
        .all()
    )
    return [{"date": str(d), "count": c} for d, c in reversed(rows)]


def top_questions(db: Session, limit: int = 10, tenant_id: str = "default") -> List[dict]:
    rows = (
        db.query(Conversation.user_msg, func.count(Conversation.user_msg))
        .filter(Conversation.tenant_id == tenant_id)
        .group_by(Conversation.user_msg)
        .order_by(func.count(Conversation.user_msg).desc())
        .limit(limit)
        .all()
    )
    return [{"question": q, "count": c} for q, c in rows]
