"""认证相关请求/响应模型"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _check_bcrypt_limit(v: str) -> str:
    """bcrypt 只处理前 72 字节,超长密码(如中文)需提前拦截"""
    if len(v.encode("utf-8")) > 72:
        raise ValueError("密码过长(不能超过 72 字节)")
    return v


class RegisterRequest(BaseModel):
    username: str = Field(
        min_length=3, max_length=32, pattern=r"^\w+$",
        description="用户名(3-32 位字母/数字/下划线/中文)",
    )
    password: str = Field(min_length=6, max_length=64, description="密码(6-64 位)")

    _check_password = field_validator("password")(_check_bcrypt_limit)


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=64, description="新密码(6-64 位)")

    _check_new_password = field_validator("new_password")(_check_bcrypt_limit)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
