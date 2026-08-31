"""Pydantic 请求/响应模型。"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---- 文案生成 ----
class CopywritingRequest(BaseModel):
    copy_type: str = Field("product", description="product | ad | campaign | keywords | all")
    product_name: str = Field(..., description="商品名称")
    category: Optional[str] = ""
    selling_points: Optional[str] = ""
    target_market: Optional[str] = ""
    target_language: str = "en"
    style: Optional[str] = ""
    tone: Optional[str] = ""


class BatchCopywritingRequest(BaseModel):
    products: List[Dict[str, Any]] = Field(..., description="商品列表")
    target_language: str = "en"


# ---- 翻译 ----
class TranslationRequest(BaseModel):
    text: str = Field(..., description="待翻译文本")
    source_language: str = "zh"
    target_language: str = "en"
    use_terminology: bool = True
    use_memory: bool = True


class TerminologyRequest(BaseModel):
    term: str
    translations: Dict[str, str]
    category: str = "trade"


# ---- 鉴权 ----
class AuthLogin(BaseModel):
    username: str
    password: str


class AuthRegister(BaseModel):
    username: str
    password: str
    # 角色与租户由服务端固定（operator/default），防止注册时自助提权为 admin。


# ---- 客服 ----
class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = "default"
    history: Optional[List[Dict[str, str]]] = []


class FeedbackRequest(BaseModel):
    conversation_id: int
    rating: int = Field(5, ge=1, le=5)
    comment: Optional[str] = ""


# ---- 知识库 ----
class KnowledgeSearchRequest(BaseModel):
    query: str
    top_k: int = 5


# ---- 管理后台 ----
class ModelConfigRequest(BaseModel):
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    temperature: Optional[float] = None
