"""多语言翻译 API。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.schemas import TerminologyRequest, TranslationRequest
from app.services import translation as trans_service

router = APIRouter()


@router.post("/translate")
def translate(req: TranslationRequest, db: Session = Depends(get_db)):
    """实时翻译。"""
    return trans_service.translate(
        db,
        text=req.text,
        source_language=req.source_language,
        target_language=req.target_language,
        use_terminology=req.use_terminology,
        use_memory=req.use_memory,
    )


@router.get("/terminology")
def get_terminology(db: Session = Depends(get_db)):
    """查询术语库（数据库持久化）。"""
    return {"terminology": trans_service.list_terminology(db)}


@router.post("/terminology")
def add_terminology(req: TerminologyRequest, db: Session = Depends(get_db)):
    """新增/更新术语。"""
    trans_service.add_terminology(req.term, req.translations, req.category, db)
    return {"ok": True, "term": req.term}
