"""管理后台 API：系统状态、模型配置、审计日志。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.auth import require_user
from app.config import settings
from app.core.llm.factory import get_llm, llm_failover_models
from app.core.vector_store.factory import get_vector_store
from app.db.models import AuditLog, KnowledgeDoc
from app.db.session import get_db

router = APIRouter()


@router.get("/status")
def status(_user: dict = Depends(require_user)):
    """系统运行状态。"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "llm_failover_models": llm_failover_models(),
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "vector_store": settings.VECTOR_STORE,
        "auth_required": settings.AUTH_REQUIRED,
        "llm_impl": get_llm().name,
        "vector_count": get_vector_store().count(),
    }


@router.get("/knowledge-stats")
def knowledge_stats(_user: dict = Depends(require_user), db: Session = Depends(get_db)):
    """知识库统计。"""
    total = db.query(KnowledgeDoc).count()
    chunks = get_vector_store().count()
    return {"documents": total, "chunks": chunks}


@router.get("/audit")
def audit_logs(_user: dict = Depends(require_user), limit: int = 50, db: Session = Depends(get_db)):
    """审计日志列表。"""
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return {
        "logs": [
            {"id": r.id, "actor": r.actor, "action": r.action, "detail": r.detail,
             "created_at": r.created_at.isoformat()}
            for r in rows
        ]
    }
