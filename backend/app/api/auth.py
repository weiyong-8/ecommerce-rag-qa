"""认证接口: 注册 / 登录 / 当前用户 / 修改密码"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.username == body.username).first()
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名已存在")
    user = User(username=body.username, password_hash=get_password_hash(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse, summary="用户登录")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    return TokenResponse(
        access_token=create_access_token(user), user=UserOut.model_validate(user)
    )


@router.get("/me", response_model=UserOut, summary="当前登录用户信息")
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password", summary="修改密码")
def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "原密码错误")
    if body.old_password == body.new_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "新密码不能与原密码相同")
    user.password_hash = get_password_hash(body.new_password)
    db.commit()
    return {"message": "密码修改成功"}
