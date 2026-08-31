"""鉴权工具：基于标准库实现 PBKDF2 密码哈希与 HS256 JWT（无第三方依赖）。

生产环境可替换为 passlib[bcrypt] + PyJWT，但脚手架默认零依赖即可运行。
"""
import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

from app.config import settings

_PBKDF2_ROUNDS = 100_000


# ---------------- 密码哈希 ----------------
def pwd_hash(password: str) -> str:
    """返回 'pbkdf2_sha256$<salt_b64>$<dk_b64>'。"""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS)
    return "pbkdf2_sha256$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()


def pwd_verify(password: str, stored: str) -> bool:
    try:
        _, salt_b64, dk_b64 = stored.split("$", 2)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(dk_b64)
        test = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS)
        return hmac.compare_digest(test, expected)
    except Exception:
        return False


# ---------------- JWT (HS256) ----------------
def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def create_access_token(sub: str, expires_min: Optional[int] = None) -> str:
    exp = int(time.time()) + (expires_min or settings.ACCESS_TOKEN_EXPIRE_MINUTES) * 60
    header = {"alg": settings.JWT_ALGORITHM, "typ": "JWT"}
    payload = {"sub": sub, "exp": exp, "iat": int(time.time())}
    signing_input = (
        _b64url(json.dumps(header, separators=(",", ":")).encode())
        + "."
        + _b64url(json.dumps(payload, separators=(",", ":")).encode())
    )
    sig = hmac.new(settings.JWT_SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
    return signing_input + "." + _b64url(sig)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        signing_input = header_b64 + "." + payload_b64
        expected = hmac.new(settings.JWT_SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64url_decode(sig_b64)):
            return None
        payload = json.loads(_b64url_decode(payload_b64))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None
