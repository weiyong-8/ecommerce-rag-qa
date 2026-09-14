"""知识库文档请求/响应模型"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    file_type: str
    category: str
    status: str  # pending / parsing / indexed / failed
    chunk_count: int
    file_size: int
    uploader_id: int
    error_msg: str = ""
    created_at: datetime
