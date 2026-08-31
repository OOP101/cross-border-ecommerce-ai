"""数据洞察与智能营销 API。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.auth import require_user
from app.db.session import get_db
from app.services import analytics as analytics_service

router = APIRouter()


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), user: dict = Depends(require_user)):
    """运营看板核心指标（按租户隔离）。"""
    return analytics_service.dashboard(db, user["tenant_id"])


@router.get("/top-questions")
def top_questions(limit: int = 10, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    """高频问题 Top N（按租户隔离）。"""
    return {"questions": analytics_service.top_questions(db, limit, user["tenant_id"])}
