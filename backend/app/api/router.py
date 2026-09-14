"""API 总路由: 所有业务接口统一挂在 /api 前缀下"""
from fastapi import APIRouter

from app.api import auth, conversations, kb

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(kb.router)
api_router.include_router(conversations.router)
