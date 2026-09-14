"""数据库基础设施: 引擎 / 会话工厂 / 建表与管理员种子数据"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


# SQLite(仅测试用)需要关闭同线程检查
_connect_args = (
    {"check_same_thread": False} if settings.sqlalchemy_url.startswith("sqlite") else {}
)

engine = create_engine(
    settings.sqlalchemy_url,
    connect_args=_connect_args,
    pool_pre_ping=True,  # 取连接前探活,避免 MySQL 长时间闲置后拿到的失效连接
    pool_recycle=3600,   # 连接最长复用 1 小时(小于 MySQL wait_timeout)
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI 依赖: 请求级数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """启动时建表 + 种子管理员(admin/123456),幂等可重复执行"""
    # 局部导入避免循环依赖
    from app.core.security import get_password_hash
    from app.models import User

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(User).filter(User.username == "admin").first() is None:
            db.add(
                User(
                    username="admin",
                    password_hash=get_password_hash("123456"),
                    role="admin",
                )
            )
            db.commit()
