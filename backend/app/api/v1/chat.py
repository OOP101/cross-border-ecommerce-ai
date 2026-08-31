"""智能客服 API。"""
import json
import time

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.llm.base import extract_usage
from app.core.llm.factory import get_llm
from app.api.v1.auth import require_user
from app.db.models import Feedback
from app.db.session import SessionLocal, get_db
from app.models.schemas import ChatRequest, FeedbackRequest
from app.services import chat as chat_service

router = APIRouter()


@router.post("")
def chat(req: ChatRequest, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    """RAG 智能问答（一次性返回）。"""
    return chat_service.answer(
        db,
        session_id=req.session_id,
        message=req.message,
        history=req.history,
        tenant_id=user["tenant_id"],
    )


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/stream")
def chat_stream(req: ChatRequest, user: dict = Depends(require_user)):
    """RAG 智能问答（SSE 流式）。

    事件序列：
      delta: {"text": "..."}  —— 增量回答片段，可多条
      meta : {"conversation_id", "intent", "need_human", "sources", "latency_ms"}
    """
    session_id = req.session_id or "default"
    tenant_id = user["tenant_id"]

    def event_gen():
        start = time.time()
        # 意图识别与检索在流开始前完成（耗时可忽略），LLM 生成逐段推送
        prepared = chat_service.prepare(req.message, req.history, tenant_id=tenant_id)

        if prepared["need_human"]:
            answer_text = chat_service.HUMAN_HANDOFF_TEXT
            yield _sse("delta", {"text": answer_text})
        else:
            answer_text = ""
            for piece in get_llm().generate_stream(
                prepared["prompt"], system=chat_service.SYSTEM_PROMPT, task="chat"
            ):
                answer_text += piece
                yield _sse("delta", {"text": piece})

        latency_ms = int((time.time() - start) * 1000)
        # 流式接口暂无法拿到服务端 usage，按估算降级（见 core.llm.base.extract_usage）
        prompt_tokens, completion_tokens = extract_usage(None, prepared["prompt"], answer_text)

        # 流式响应结束后依赖注入的 db 已关闭，这里使用独立会话落库
        db = SessionLocal()
        try:
            conversation_id = chat_service.persist(
                db,
                session_id=session_id,
                message=req.message,
                answer_text=answer_text,
                intent=prepared["intent"],
                sources=prepared["sources"],
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                endpoint="/chat/stream",
                tenant_id=tenant_id,
            )
        finally:
            db.close()

        yield _sse(
            "meta",
            {
                "conversation_id": conversation_id,
                "intent": prepared["intent"],
                "need_human": prepared["need_human"],
                "sources": prepared["sources"],
                "latency_ms": latency_ms,
            },
        )

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/feedback")
def feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    """提交满意度反馈。"""
    fb = Feedback(conversation_id=req.conversation_id, rating=req.rating, comment=req.comment)
    db.add(fb)
    db.commit()
    return {"ok": True, "id": fb.id}
