"""数据库会话管理（SQLAlchemy 2.0）。"""
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# 默认行业术语（国际贸易高频缩写），首次启动播种
_DEFAULT_TERMS = [
    ("FOB", {"zh": "离岸价", "en": "Free On Board"}, "trade"),
    ("CIF", {"zh": "到岸价", "en": "Cost, Insurance and Freight"}, "trade"),
    ("LC", {"zh": "信用证", "en": "Letter of Credit"}, "trade"),
    ("MOQ", {"zh": "最小起订量", "en": "Minimum Order Quantity"}, "trade"),
    ("ETD", {"zh": "预计发运日期", "en": "Estimated Time of Departure"}, "trade"),
    ("ETA", {"zh": "预计到达日期", "en": "Estimated Time of Arrival"}, "trade"),
    ("B/L", {"zh": "提单", "en": "Bill of Lading"}, "trade"),
]


def init_db() -> None:
    """初始化所有表，并播种默认用户与术语。"""
    from app.core import security
    from app.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite()
    _seed_defaults(security)


def _migrate_sqlite() -> None:
    """轻量迁移：create_all 不会给已存在的表加列，这里按需 ALTER TABLE。

    仅覆盖脚手架阶段的字段演进；引入 Alembic 后可移除。
    """
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "knowledge_docs" in inspector.get_table_names():
        columns = {c["name"] for c in inspector.get_columns("knowledge_docs")}
        if "doc_id" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE knowledge_docs ADD COLUMN doc_id VARCHAR(32)"))
                conn.execute(text("CREATE INDEX ix_knowledge_docs_doc_id ON knowledge_docs (doc_id)"))


def _seed_defaults(security) -> None:
    from app.db import models

    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            db.add(
                models.User(
                    username="admin",
                    hashed_password=security.pwd_hash("admin123"),
                    role="admin",
                    tenant_id="default",
                )
            )
        if db.query(models.Term).count() == 0:
            for term, trans, cat in _DEFAULT_TERMS:
                db.add(
                    models.Term(
                        term=term,
                        translations=json.dumps(trans, ensure_ascii=False),
                        category=cat,
                    )
                )
        db.commit()
    finally:
        db.close()


def get_db():
    """FastAPI 依赖：提供数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
