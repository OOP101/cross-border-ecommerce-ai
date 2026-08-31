"""知识库管理 API。"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.v1.auth import require_user
from app.db.session import get_db
from app.models.schemas import KnowledgeSearchRequest
from app.services import knowledge as kb_service

router = APIRouter()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(require_user),
):
    """上传并向量化知识文档（PDF/Word/Excel/Markdown/TXT），归属当前用户租户。"""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件内容为空")
    try:
        result = kb_service.add_document(db, file.filename or "untitled", content, user["tenant_id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.get("")
def list_documents(db: Session = Depends(get_db), user: dict = Depends(require_user)):
    """知识文档列表（仅当前租户）。"""
    return {"documents": kb_service.list_documents(db, user["tenant_id"])}


@router.delete("/{doc_id}")
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user),
):
    """删除知识文档及其向量（仅限本租户文档）。"""
    kb_service.delete_document(db, doc_id, user["tenant_id"])
    return {"ok": True}


@router.post("/search")
def search_knowledge(req: KnowledgeSearchRequest):
    """知识库检索（调试）。"""
    return {"results": kb_service.search_knowledge(req.query, req.top_k)}
