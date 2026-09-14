"""FastAPI 入口: 基于 LangChain 的电商商品知识库问答系统"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动: 建表 + 种子管理员(admin/123456),依赖 Docker 基础设施已就绪
    init_db()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

# 开发环境允许前端 dev server 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", summary="服务信息")
def root():
    return {"service": settings.app_name, "docs": "/docs", "status": "running"}


@app.get("/health", summary="健康检查")
def health():
    return {"status": "ok"}
