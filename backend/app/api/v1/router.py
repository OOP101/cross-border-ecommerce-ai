"""v1 路由聚合。"""
from fastapi import APIRouter

from app.api.v1 import admin, analytics, auth, chat, copywriting, knowledge, translation

api_router = APIRouter()
api_router.include_router(copywriting.router, prefix="/copywriting", tags=["文案生成"])
api_router.include_router(translation.router, prefix="/translation", tags=["翻译引擎"])
api_router.include_router(chat.router, prefix="/chat", tags=["智能客服"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["知识库"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["数据洞察"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理后台"])
api_router.include_router(auth.router, prefix="/auth", tags=["鉴权"])
