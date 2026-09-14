"""知识库文档表: 元数据与解析状态"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Document(Base):
    """知识库文档: status 流转 pending → parsing → indexed / failed"""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))            # 原始文件名
    file_type: Mapped[str] = mapped_column(String(16))        # md / txt / pdf / docx / xlsx
    category: Mapped[str] = mapped_column(String(64), default="通用")  # 商品类目(元数据过滤)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    error_msg: Mapped[str] = mapped_column(String(255), default="")
    uploader_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
