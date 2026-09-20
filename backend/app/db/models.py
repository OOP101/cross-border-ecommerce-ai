"""ORM 数据模型。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class KnowledgeDoc(Base):
    """知识文档元数据。"""
    __tablename__ = "knowledge_docs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), default="default", server_default="default", index=True)
    filename: Mapped[str] = mapped_column(String(255), index=True)
    content_type: Mapped[str] = mapped_column(String(50), default="text/plain")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | indexed | failed
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Conversation(Base):
    """客服对话记录。"""
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), default="default", server_default="default", index=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    user_msg: Mapped[str] = mapped_column(Text)
    bot_msg: Mapped[str] = mapped_column(Text)
    intent: Mapped[str] = mapped_column(String(32), default="product")
    sources: Mapped[str] = mapped_column(Text, default="[]")  # JSON 字符串
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Feedback(Base):
    """客服满意度反馈。"""
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(Integer, index=True)
    rating: Mapped[int] = mapped_column(Integer, default=5)  # 1-5
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ApiUsage(Base):
    """模型调用与性能统计。"""
    __tablename__ = "api_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    endpoint: Mapped[str] = mapped_column(String(100), index=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AuditLog(Base):
    """审计日志。"""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(64), default="system")
    action: Mapped[str] = mapped_column(String(100))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class User(Base):
    """系统用户（多租户、多角色）。"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="operator")  # admin | operator | viewer
    tenant_id: Mapped[str] = mapped_column(String(64), default="default")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Term(Base):
    """翻译术语库条目（行业专属译法，保证多语言一致性）。"""
    __tablename__ = "terminology"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term: Mapped[str] = mapped_column(String(120), index=True)
    translations: Mapped[str] = mapped_column(Text, default="{}")  # JSON: {"en": "...", "zh": "..."}
    category: Mapped[str] = mapped_column(String(50), default="trade")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TranslationMemory(Base):
    """翻译记忆：源文本哈希 -> 译文，跨重启持久化。"""
    __tablename__ = "translation_memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hash: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # md5(src:tgt:text)
    translated: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Customer(Base):
    """客户信息表。"""
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), default="default", server_default="default", index=True)
    company_name: Mapped[str] = mapped_column(String(255), index=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    grade: Mapped[str] = mapped_column(String(10), default="C")  # A/B/C/D
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # amazon/exhibition/website/referral
    tags: Mapped[str] = mapped_column(Text, default="[]")  # JSON 数组
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class FollowUp(Base):
    """客户跟进记录。"""
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), default="default", server_default="default", index=True)
    customer_id: Mapped[int] = mapped_column(Integer, index=True)
    contact_type: Mapped[str] = mapped_column(String(20))  # phone/email/meeting/other
    content: Mapped[str] = mapped_column(Text)
    next_follow_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[str] = mapped_column(String(64), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Product(Base):
    """商品信息表。"""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), default="default", server_default="default", index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cost_price: Mapped[float] = mapped_column(Float, default=0.0)  # 成本价
    selling_price: Mapped[float] = mapped_column(Float, default=0.0)  # 售价
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    amazon_asin: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    amazon_marketplace: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/inactive
    images: Mapped[str] = mapped_column(Text, default="[]")  # JSON 数组
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
