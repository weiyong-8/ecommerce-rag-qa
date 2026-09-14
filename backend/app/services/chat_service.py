"""问答业务逻辑: 检索 → 重排 → 引用式提示词 → LLM 流式生成 → 落库

SSE 事件流:
- {"type": "sources", "sources": [...]}  引用片段(生成前先行下发,前端可提前展示)
- {"type": "token", "content": "..."}    流式文本增量
- {"type": "done"}                       完成(消息已落库)
- {"type": "error", "message": "..."}    任何环节失败(检索/模型/权限)
"""
import json
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.database import SessionLocal
from app.models import Conversation, Message
from app.rag.embeddings import get_embedding_model
from app.rag.llm import get_chat_model
from app.rag.milvus_store import search_similar
from app.rag.reranker import rerank

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是电商平台的智能商品客服助手,请仅根据【参考片段】回答用户关于商品的问题。

要求:
1. 优先使用参考片段中的信息回答,引用内容时在句末标注来源编号,如 [1]、[2]
2. 如果参考片段中没有相关信息,明确回答"知识库中暂未收录相关信息,建议联系人工客服",不要编造内容
3. 使用简体中文,回答简洁清晰,可适当使用列表
"""

# 检索召回数 / 精排保留数 / 携带的历史轮数
TOP_K_RECALL = 20
TOP_K_RERANK = 5
HISTORY_TURNS = 6


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


def _build_messages(history: list[Message], question: str, chunks: list[dict]) -> list:
    """拼装带引用编号的提示词 + 多轮历史上下文"""
    context = "\n\n".join(
        f"[{i + 1}] (来源: {c['doc_name']} | {c.get('headers') or '正文'})\n{c['text']}"
        for i, c in enumerate(chunks)
    )
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for m in history:
        if m.role == "user":
            messages.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            messages.append(AIMessage(content=m.content))
    messages.append(
        HumanMessage(content=f"【参考片段】\n{context}\n\n【用户问题】\n{question}")
    )
    return messages


async def ask_stream(conversation_id: int, user_id: int, question: str):
    """SSE 流式问答(异步生成器)"""
    db = SessionLocal()
    try:
        conv = db.get(Conversation, conversation_id)
        if conv is None or conv.user_id != user_id:
            yield _sse({"type": "error", "message": "会话不存在"})
            return

        # 多轮历史(取当前提问之前的最近几轮)
        history = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.id.desc())
            .limit(HISTORY_TURNS)
            .all()
        )[::-1]

        # 首次提问自动生成会话标题
        if conv.title == "新对话":
            conv.title = question[:20]

        # 保存用户消息
        db.add(Message(conversation_id=conv.id, role="user", content=question))
        db.commit()

        # 1) 向量检索
        try:
            q_vec = get_embedding_model().embed_query(question)
            hits = search_similar(q_vec, top_k=TOP_K_RECALL)
        except Exception as e:
            logger.exception("向量检索失败")
            yield _sse({"type": "error", "message": f"知识库检索失败(请确认 Milvus 已启动): {str(e)[:100]}"})
            return
        if not hits:
            yield _sse({"type": "error", "message": "知识库为空,请先由管理员上传商品文档"})
            return

        # 2) 重排序 + 引用片段
        chunks = rerank(question, hits)[:TOP_K_RERANK]
        sources = [
            {
                "index": i + 1,
                "doc_id": c["doc_id"],
                "doc_name": c["doc_name"],
                "chunk_index": c.get("chunk_index"),
                "headers": c.get("headers", ""),
                "text": c["text"][:300],
                "score": c.get("score"),
            }
            for i, c in enumerate(chunks)
        ]
        yield _sse({"type": "sources", "sources": sources})

        # 3) LLM 流式生成
        try:
            llm = get_chat_model()
            answer_parts: list[str] = []
            async for chunk in llm.astream(_build_messages(history, question, chunks)):
                piece = chunk.content or ""
                if piece:
                    answer_parts.append(piece)
                    yield _sse({"type": "token", "content": piece})
        except Exception as e:
            logger.exception("大模型调用失败")
            yield _sse({"type": "error", "message": f"大模型调用失败: {str(e)[:100]}"})
            return

        # 4) 保存回答(含引用片段,历史会话可完整恢复)
        answer = "".join(answer_parts)
        db.add(
            Message(
                conversation_id=conv.id,
                role="assistant",
                content=answer,
                sources=sources,
            )
        )
        db.commit()
        yield _sse({"type": "done"})
    finally:
        db.close()
