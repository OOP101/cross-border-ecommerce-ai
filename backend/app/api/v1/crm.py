"""CRM 客户管理 API：客户信息、跟进记录。"""
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.models import Customer, FollowUp
from app.db.session import get_db

router = APIRouter()


# ============ Pydantic Schemas ============

class CustomerCreate(BaseModel):
    company_name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    industry: Optional[str] = None
    grade: str = "C"
    source: Optional[str] = None
    tags: list[str] = []
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    industry: Optional[str] = None
    grade: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[list[str]] = None
    notes: Optional[str] = None


class FollowUpCreate(BaseModel):
    customer_id: int
    contact_type: str  # phone/email/meeting/other
    content: str
    next_follow_date: Optional[datetime] = None


# ============ 客户管理 ============

@router.get("/stats/overview", summary="客户统计概览")
def customer_stats_overview(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """获取客户统计概览。"""
    from datetime import datetime, timedelta

    tenant_id = user["tenant_id"]

    # 总客户数
    total = db.query(Customer).filter(Customer.tenant_id == tenant_id).count()

    # A 级客户数
    grade_a = db.query(Customer).filter(
        Customer.tenant_id == tenant_id,
        Customer.grade == "A",
    ).count()

    # 待跟进（有跟进记录且下次跟进日期在未来 7 天内）
    now = datetime.now()
    future = now + timedelta(days=7)
    pending_follow_up = db.query(FollowUp).filter(
        FollowUp.tenant_id == tenant_id,
        FollowUp.next_follow_date >= now,
        FollowUp.next_follow_date <= future,
    ).count()

    # 本月新增
    month_start = datetime(now.year, now.month, 1)
    month_new = db.query(Customer).filter(
        Customer.tenant_id == tenant_id,
        Customer.created_at >= month_start,
    ).count()

    return {
        "total": total,
        "grade_a": grade_a,
        "pending_follow_up": pending_follow_up,
        "month_new": month_new,
    }


@router.get("/customers", summary="客户列表")
def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    grade: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """获取客户列表，支持分页和筛选。"""
    query = db.query(Customer).filter(Customer.tenant_id == user["tenant_id"])

    if grade:
        query = query.filter(Customer.grade == grade)
    if keyword:
        query = query.filter(
            (Customer.company_name.contains(keyword)) |
            (Customer.contact_person.contains(keyword)) |
            (Customer.email.contains(keyword))
        )

    total = query.count()
    customers = query.order_by(Customer.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": c.id,
                "company_name": c.company_name,
                "contact_person": c.contact_person,
                "email": c.email,
                "phone": c.phone,
                "grade": c.grade,
                "source": c.source,
                "tags": json.loads(c.tags) if c.tags else [],
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in customers
        ],
    }


@router.post("/customers", summary="创建客户")
def create_customer(
    req: CustomerCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """创建新客户。"""
    customer = Customer(
        tenant_id=user["tenant_id"],
        company_name=req.company_name,
        contact_person=req.contact_person,
        email=req.email,
        phone=req.phone,
        address=req.address,
        industry=req.industry,
        grade=req.grade,
        source=req.source,
        tags=json.dumps(req.tags, ensure_ascii=False),
        notes=req.notes,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return {"id": customer.id, "company_name": customer.company_name}


@router.get("/customers/{customer_id}", summary="客户详情")
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """获取客户详情。"""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.tenant_id == user["tenant_id"],
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    return {
        "id": customer.id,
        "company_name": customer.company_name,
        "contact_person": customer.contact_person,
        "email": customer.email,
        "phone": customer.phone,
        "address": customer.address,
        "industry": customer.industry,
        "grade": customer.grade,
        "source": customer.source,
        "tags": json.loads(customer.tags) if customer.tags else [],
        "notes": customer.notes,
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
        "updated_at": customer.updated_at.isoformat() if customer.updated_at else None,
    }


@router.put("/customers/{customer_id}", summary="更新客户")
def update_customer(
    customer_id: int,
    req: CustomerUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """更新客户信息。"""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.tenant_id == user["tenant_id"],
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    update_data = req.model_dump(exclude_unset=True)
    if "tags" in update_data:
        update_data["tags"] = json.dumps(update_data["tags"], ensure_ascii=False)

    for key, value in update_data.items():
        setattr(customer, key, value)

    db.commit()
    return {"ok": True, "id": customer.id}


@router.delete("/customers/{customer_id}", summary="删除客户")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """删除客户。"""
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.tenant_id == user["tenant_id"],
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    db.delete(customer)
    db.commit()
    return {"ok": True}


# ============ 跟进记录 ============

@router.get("/customers/{customer_id}/follow-ups", summary="客户跟进记录列表")
def list_follow_ups(
    customer_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """获取某客户的所有跟进记录。"""
    # 验证客户存在
    customer = db.query(Customer).filter(
        Customer.id == customer_id,
        Customer.tenant_id == user["tenant_id"],
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    follow_ups = db.query(FollowUp).filter(
        FollowUp.customer_id == customer_id,
        FollowUp.tenant_id == user["tenant_id"],
    ).order_by(FollowUp.created_at.desc()).all()

    return [
        {
            "id": f.id,
            "customer_id": f.customer_id,
            "contact_type": f.contact_type,
            "content": f.content,
            "next_follow_date": f.next_follow_date.isoformat() if f.next_follow_date else None,
            "created_by": f.created_by,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in follow_ups
    ]


@router.post("/follow-ups", summary="创建跟进记录")
def create_follow_up(
    req: FollowUpCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """创建跟进记录。"""
    # 验证客户存在
    customer = db.query(Customer).filter(
        Customer.id == req.customer_id,
        Customer.tenant_id == user["tenant_id"],
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    follow_up = FollowUp(
        tenant_id=user["tenant_id"],
        customer_id=req.customer_id,
        contact_type=req.contact_type,
        content=req.content,
        next_follow_date=req.next_follow_date,
        created_by=user["sub"],
    )
    db.add(follow_up)
    db.commit()
    db.refresh(follow_up)
    return {"id": follow_up.id, "customer_id": follow_up.customer_id}


@router.get("/follow-ups/upcoming", summary="即将跟进的客户")
def upcoming_follow_ups(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """获取未来 N 天内需要跟进的客户。"""
    from datetime import timedelta
    now = datetime.now()
    future = now + timedelta(days=days)

    follow_ups = db.query(FollowUp).filter(
        FollowUp.tenant_id == user["tenant_id"],
        FollowUp.next_follow_date >= now,
        FollowUp.next_follow_date <= future,
    ).order_by(FollowUp.next_follow_date.asc()).all()

    result = []
    for f in follow_ups:
        customer = db.query(Customer).filter(Customer.id == f.customer_id).first()
        if customer:
            result.append({
                "follow_up_id": f.id,
                "customer_id": customer.id,
                "company_name": customer.company_name,
                "contact_person": customer.contact_person,
                "next_follow_date": f.next_follow_date.isoformat() if f.next_follow_date else None,
                "content": f.content,
            })

    return result
