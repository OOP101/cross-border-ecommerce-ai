"""RAG 智能客服服务：意图识别 -> 检索 -> 上下文构建 -> 生成 -> 溯源。"""
import json
import logging
import time
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.llm.base import extract_usage
from app.core.llm.factory import get_llm
from app.db.models import ApiUsage, Conversation
from app.services.agent.workflow import run_agent
from app.services.rag.retriever import get_retriever

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一名专业的国际贸易客服助手，精通多语言沟通。"
    "请基于提供的知识库片段回答问题；若知识库无相关信息，请如实说明并建议转人工。"
    "回答需准确、简洁、可溯源。"
)

HUMAN_HANDOFF_TEXT = "您的问题涉及较高风险，已为您转接人工客服，请稍候。"


def _build_context(retrieved: List[dict]) -> str:
    if not retrieved:
        return "（知识库为空）"
    parts = []
    for i, item in enumerate(retrieved, 1):
        src = item.get("metadata", {}).get("source", "未知来源")
        parts.append(f"[片段{i} · 来源:{src}]\n{item['text']}")
    return "\n\n".join(parts)


def _build_history_block(history: Optional[List[dict]]) -> str:
    if not history:
        return ""
    lines = []
    for h in history[-6:]:
        content = (h.get("content") or "").strip()
        if not content:
            continue
        role = "用户" if h.get("role") == "user" else "助手"
        lines.append(f"{role}:{content}")
    return "\n".join(lines)


def prepare(message: str, history: Optional[List[dict]] = None, tenant_id: str = "default") -> dict:
    """意图识别 + 检索 + Prompt 构建（不含 LLM 调用与落库），同步/流式共用。

    检索限定在当前租户的知识库内，防止跨租户知识泄漏。
    """
    agent = run_agent(message)
    retrieved = get_retriever().retrieve(message, tenant_id=tenant_id)
    context = _build_context(retrieved)

    history_block = _build_history_block(history)
    prompt = (
        f"【知识库上下文】\n{context}\n\n"
        f"【对话历史】\n{history_block or '（无）'}\n\n"
        f"【当前问题】\n{message}\n\n"
        f"【当前意图】{agent['intent']}\n"
        "请生成回答。"
    )

    sources = [
        {
            "source": item.get("metadata", {}).get("source", "未知"),
            "score": item.get("score", 0.0),
            "text": item["text"][:120],
        }
        for item in retrieved
    ]
    return {
        "intent": agent["intent"],
        "need_human": agent["need_human"],
        "prompt": prompt,
        "sources": sources,
    }


def persist(
    db: Session,
    session_id: str,
    message: str,
    answer_text: str,
    intent: str,
    sources: List[dict],
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: int,
    endpoint: str = "/chat",
    tenant_id: str = "default",
) -> int:
    """落库对话与用量，返回会话记录 id。"""
    conv = Conversation(
        tenant_id=tenant_id,
        session_id=session_id,
        user_msg=message,
        bot_msg=answer_text,
        intent=intent,
        sources=json.dumps(sources, ensure_ascii=False),
        latency_ms=latency_ms,
    )
    db.add(conv)
    db.flush()
    db.add(
        ApiUsage(
            endpoint=endpoint,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
        )
    )
    db.commit()
    return conv.id


def answer(
    db: Session,
    session_id: str,
    message: str,
    history: Optional[List[dict]] = None,
    tenant_id: str = "default",
) -> dict:
    start = time.time()

    prepared = prepare(message, history, tenant_id=tenant_id)
    intent = prepared["intent"]
    need_human = prepared["need_human"]

    if need_human:
        answer_text = HUMAN_HANDOFF_TEXT
        result = None
    else:
        result = get_llm().generate(prepared["prompt"], system=SYSTEM_PROMPT, task="chat")
        answer_text = result.content

    latency_ms = int((time.time() - start) * 1000)
    prompt_tokens, completion_tokens = extract_usage(result, prepared["prompt"], answer_text)
    conversation_id = persist(
        db,
        session_id=session_id,
        message=message,
        answer_text=answer_text,
        intent=intent,
        sources=prepared["sources"],
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=latency_ms,
        tenant_id=tenant_id,
    )

    return {
        "answer": answer_text,
        "conversation_id": conversation_id,
        "intent": intent,
        "need_human": need_human,
        "sources": prepared["sources"],
        "latency_ms": latency_ms,
    }
