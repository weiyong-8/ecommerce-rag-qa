"""会话与消息请求/响应模型"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: str = Field(default="新对话", max_length=50)


class ConversationRename(BaseModel):
    title: str = Field(min_length=1, max_length=50)


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    sources: list[dict[str, Any]] = []
    created_at: datetime


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
