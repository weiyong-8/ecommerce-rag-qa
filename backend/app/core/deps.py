"""FastAPI 依赖: 登录态解析与管理员角色校验"""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User

# tokenUrl 指向登录接口,Swagger 文档右上角可用 Authorize 按钮调试
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """从 Authorization: Bearer <token> 解析当前用户,无效/过期返回 401"""
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "登录已失效,请重新登录"
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """管理员校验(需求: 仅 admin 可管理知识库),非 admin 返回 403"""
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要管理员权限")
    return user
