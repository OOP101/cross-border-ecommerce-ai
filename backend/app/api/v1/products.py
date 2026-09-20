"""商品管理 API：商品信息、库存管理。"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.db.models import Product
from app.db.session import get_db

router = APIRouter()


# ============ Pydantic Schemas ============

class ProductCreate(BaseModel):
    sku: str
    name: str
    category: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    cost_price: float = 0.0
    selling_price: float = 0.0
    currency: str = "USD"
    stock_quantity: int = 0
    amazon_asin: Optional[str] = None
    amazon_marketplace: Optional[str] = None
    status: str = "active"
    images: list[str] = []


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    currency: Optional[str] = None
    stock_quantity: Optional[int] = None
    amazon_asin: Optional[str] = None
    amazon_marketplace: Optional[str] = None
    status: Optional[str] = None
    images: Optional[list[str]] = None


# ============ 商品管理 ============

@router.get("", summary="商品列表")
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """获取商品列表，支持分页和筛选。"""
    query = db.query(Product).filter(Product.tenant_id == user["tenant_id"])

    if category:
        query = query.filter(Product.category == category)
    if status:
        query = query.filter(Product.status == status)
    if keyword:
        query = query.filter(
            (Product.name.contains(keyword)) |
            (Product.sku.contains(keyword)) |
            (Product.amazon_asin.contains(keyword))
        )

    total = query.count()
    products = query.order_by(Product.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "category": p.category,
                "brand": p.brand,
                "cost_price": p.cost_price,
                "selling_price": p.selling_price,
                "currency": p.currency,
                "stock_quantity": p.stock_quantity,
                "amazon_asin": p.amazon_asin,
                "amazon_marketplace": p.amazon_marketplace,
                "status": p.status,
                "images": json.loads(p.images) if p.images else [],
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in products
        ],
    }


@router.post("", summary="创建商品")
def create_product(
    req: ProductCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """创建新商品。"""
    # 检查 SKU 是否已存在
    existing = db.query(Product).filter(
        Product.sku == req.sku,
        Product.tenant_id == user["tenant_id"],
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"SKU {req.sku} 已存在")

    product = Product(
        tenant_id=user["tenant_id"],
        sku=req.sku,
        name=req.name,
        category=req.category,
        brand=req.brand,
        description=req.description,
        cost_price=req.cost_price,
        selling_price=req.selling_price,
        currency=req.currency,
        stock_quantity=req.stock_quantity,
        amazon_asin=req.amazon_asin,
        amazon_marketplace=req.amazon_marketplace,
        status=req.status,
        images=json.dumps(req.images, ensure_ascii=False),
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"id": product.id, "sku": product.sku, "name": product.name}


# 注意：固定路径路由必须在 {product_id} 动态路由之前定义
@router.get("/categories/list", summary="商品分类列表")
def list_categories(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """获取所有商品分类。"""
    products = db.query(Product).filter(
        Product.tenant_id == user["tenant_id"],
        Product.category.isnot(None),
    ).all()

    categories = list(set(p.category for p in products if p.category))
    return {"categories": categories}


@router.get("/stats/overview", summary="商品统计概览")
def product_stats_overview(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """获取商品统计概览。"""
    tenant_id = user["tenant_id"]

    total = db.query(Product).filter(Product.tenant_id == tenant_id).count()
    active = db.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.status == "active",
    ).count()
    low_stock = db.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.stock_quantity < 10,
        Product.status == "active",
    ).count()

    # 计算总库存价值
    products = db.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.status == "active",
    ).all()
    total_value = sum(p.cost_price * p.stock_quantity for p in products)

    return {
        "total": total,
        "active": active,
        "low_stock": low_stock,
        "total_value": round(total_value, 2),
    }


@router.get("/products/{product_id}", summary="商品详情")
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """获取商品详情。"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.tenant_id == user["tenant_id"],
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    return {
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "brand": product.brand,
        "description": product.description,
        "cost_price": product.cost_price,
        "selling_price": product.selling_price,
        "currency": product.currency,
        "stock_quantity": product.stock_quantity,
        "amazon_asin": product.amazon_asin,
        "amazon_marketplace": product.amazon_marketplace,
        "status": product.status,
        "images": json.loads(product.images) if product.images else [],
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


@router.put("/products/{product_id}", summary="更新商品")
def update_product(
    product_id: int,
    req: ProductUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """更新商品信息。"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.tenant_id == user["tenant_id"],
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    # 如果更新 SKU，检查是否与其他商品冲突
    if req.sku and req.sku != product.sku:
        existing = db.query(Product).filter(
            Product.sku == req.sku,
            Product.tenant_id == user["tenant_id"],
            Product.id != product_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"SKU {req.sku} 已被其他商品使用")

    update_data = req.model_dump(exclude_unset=True)
    if "images" in update_data:
        update_data["images"] = json.dumps(update_data["images"], ensure_ascii=False)

    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    return {"ok": True, "id": product.id}


@router.delete("/products/{product_id}", summary="删除商品")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """删除商品。"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.tenant_id == user["tenant_id"],
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    db.delete(product)
    db.commit()
    return {"ok": True}
