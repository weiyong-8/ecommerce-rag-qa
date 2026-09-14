"""会话管理接口: 列表 / 新建 / 改名 / 删除 / 历史 / 知识库问答(SSE 流式)"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Conversation, Message, User
from app.schemas.chat import (
    AskRequest,
    ConversationCreate,
    ConversationOut,
    ConversationRename,
    MessageOut,
)
from app.services import chat_service

router = APIRouter(
    prefix="/conversations",
    tags=["会话"],
    dependencies=[Depends(get_current_user)],
)


def _get_owned(db: Session, conversation_id: int, user_id: int) -> Conversation:
    """校验会话归属,不属于当前用户一律 404(不泄露存在性)"""
    conv = db.get(Conversation, conversation_id)
    if conv is None or conv.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "会话不存在")
    return conv


@router.get("", response_model=list[ConversationOut], summary="会话列表")
def list_conversations(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


@router.post(
    "", response_model=ConversationOut, status_code=status.HTTP_201_CREATED, summary="新建会话"
)
def create_conversation(
    body: ConversationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = Conversation(user_id=user.id, title=body.title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.patch("/{conversation_id}", response_model=ConversationOut, summary="会话改名")
def rename_conversation(
    conversation_id: int,
    body: ConversationRename,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _get_owned(db, conversation_id, user.id)
    conv.title = body.title
    db.commit()
    return conv


@router.delete("/{conversation_id}", summary="删除会话")
def delete_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _get_owned(db, conversation_id, user.id)
    db.query(Message).filter(Message.conversation_id == conv.id).delete()
    db.delete(conv)
    db.commit()
    return {"message": "删除成功"}


@router.get(
    "/{conversation_id}/messages", response_model=list[MessageOut], summary="会话历史"
)
def get_messages(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _get_owned(db, conversation_id, user.id)
    return (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.id.asc())
        .all()
    )


@router.post("/{conversation_id}/ask", summary="知识库问答(SSE 流式)")
async def ask(
    conversation_id: int,
    body: AskRequest,
    user: User = Depends(get_current_user),
):
    return StreamingResponse(
        chat_service.ask_stream(conversation_id, user.id, body.question.strip()),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
