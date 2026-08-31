"""鉴权 API：注册、登录、当前用户。"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.core import security
from app.db.models import User
from app.db.session import get_db
from app.models.schemas import AuthLogin, AuthRegister

router = APIRouter()
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> dict:
    """解析当前用户。

    携带有效 Bearer 令牌时，始终按令牌身份解析（演示/生产一致）；
    AUTH_REQUIRED=False 且无令牌时，返回系统默认主体（演示免登录）；
    AUTH_REQUIRED=True 且无令牌时，返回 401。
    """
    if creds and creds.credentials:
        payload = security.decode_access_token(creds.credentials)
        if payload:
            user = db.query(User).filter(User.username == payload["sub"]).first()
            if user:
                return {"sub": user.username, "role": user.role, "tenant_id": user.tenant_id}

    if not settings.AUTH_REQUIRED:
        return {"sub": "system", "role": "admin", "tenant_id": "default"}

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未提供认证令牌")


def require_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> dict:
    """受保护路由依赖（语义化）。等价于 get_current_user。"""
    return get_current_user(creds, db)


@router.post("/register", summary="注册用户")
def register(req: AuthRegister, db: Session = Depends(get_db)):
    # 安全：角色与租户由服务端固定，客户端不可指定（防止自助提权为 admin）。
    # admin 角色只能由已有管理员通过 POST /auth/grant-role 授予。
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    db.add(
        User(
            username=req.username,
            hashed_password=security.pwd_hash(req.password),
            role="operator",
            tenant_id="default",
        )
    )
    db.commit()
    return {"ok": True, "username": req.username, "role": "operator"}


@router.post("/grant-role", summary="授予用户角色（仅管理员）")
def grant_role(
    username: str,
    role: str,
    current: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")
    if role not in ("admin", "operator", "viewer"):
        raise HTTPException(status_code=400, detail="无效角色，可选：admin | operator | viewer")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.role = role
    db.commit()
    return {"ok": True, "username": username, "role": role}


@router.post("/login", summary="登录获取令牌")
def login(req: AuthLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not security.pwd_verify(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    token = security.create_access_token(user.username)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_min": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    }


@router.get("/me", summary="当前用户信息")
def me(user: dict = Depends(get_current_user)):
    return user
