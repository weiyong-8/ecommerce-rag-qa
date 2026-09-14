"""安全工具: 密码哈希(bcrypt)与 JWT 令牌"""
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import settings
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def get_password_hash(password: str) -> str:
    """密码哈希(入库只存哈希,不存明文)"""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user: User, expires_minutes: int | None = None) -> str:
    """生成 JWT,payload 携带用户 id / 用户名 / 角色"""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """解码并校验 JWT(过期/伪造均抛出 jwt.PyJWTError)"""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
