"""智能文案生成 API。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.schemas import BatchCopywritingRequest, CopywritingRequest
from app.services import copywriting as copy_service

router = APIRouter()


@router.post("/generate")
async def generate_copy(req: CopywritingRequest, db: Session = Depends(get_db)):
    """生成营销文案（多段文案并发调用 LLM）。"""
    return await copy_service.generate_copywriting_async(
        db,
        copy_type=req.copy_type,
        product_name=req.product_name,
        category=req.category,
        selling_points=req.selling_points,
        target_market=req.target_market,
        target_language=req.target_language,
        style=req.style,
        tone=req.tone,
    )


@router.post("/batch")
def generate_batch(req: BatchCopywritingRequest, db: Session = Depends(get_db)):
    """批量生成多商品文案。"""
    return {"results": copy_service.generate_batch(db, req.products, req.target_language)}
