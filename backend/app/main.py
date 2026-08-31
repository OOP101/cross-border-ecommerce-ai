"""FastAPI 应用入口。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1.router import api_router
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库表
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="国际贸易上市公司一站式智能服务平台 —— LLM + RAG + Agent",
    lifespan=lifespan,
)

# CORS：allow_credentials 与通配符 origins 组合会被浏览器拒绝，
# 仅在显式白名单时开启凭据，通配符（演示模式）自动降级。
_allow_credentials = "*" not in settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 v1 路由
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["system"])
def health() -> dict:
    """健康检查。"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "vector_store": settings.VECTOR_STORE,
    }


@app.get("/", tags=["system"])
def root() -> dict:
    return {"message": settings.APP_NAME, "docs": "/docs", "health": "/health"}
