"""知识库业务逻辑: 文档生命周期管理 + 后台解析入库"""
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import SessionLocal
from app.models import Document
from app.rag.embeddings import get_embedding_model
from app.rag.milvus_store import delete_by_doc, insert_chunks
from app.rag.splitter import load_and_split

logger = logging.getLogger(__name__)

# 上传扩展名 → 内部类型(统一 markdown 为 md)
ALLOWED_TYPES = {
    "md": "md",
    "markdown": "md",
    "txt": "txt",
    "pdf": "pdf",
    "docx": "docx",
    "xlsx": "xlsx",
}


def upload_path(doc_id: int, file_type: str) -> Path:
    return settings.upload_dir_path / f"{doc_id}.{file_type}"


def delete_document(db: Session, doc: Document) -> None:
    """删除文档: 向量片段 → 磁盘文件 → 数据库记录(Milvus 暂不可用时允许降级)"""
    try:
        delete_by_doc(doc.id)
    except Exception as e:
        logger.warning("删除 Milvus 片段失败(doc_id=%s): %s", doc.id, e)
    try:
        upload_path(doc.id, doc.file_type).unlink(missing_ok=True)
    except Exception as e:
        logger.warning("删除磁盘文件失败(doc_id=%s): %s", doc.id, e)
    db.delete(doc)
    db.commit()


def process_document(doc_id: int) -> None:
    """后台解析入库: 解析→切分→向量化→写入 Milvus,全程更新状态(pending→parsing→indexed/failed)"""
    db = SessionLocal()
    doc = None
    try:
        doc = db.get(Document, doc_id)
        if doc is None:
            return
        doc.status = "parsing"
        db.commit()

        path = upload_path(doc.id, doc.file_type)
        chunks = load_and_split(str(path), doc.file_type)
        if not chunks:
            raise ValueError("文档未解析出有效内容")

        embedding_model = get_embedding_model()
        vectors = embedding_model.embed_documents([c.text for c in chunks])

        rows = [
            {
                "text": chunk.text,
                "vector": vectors[i],
                "doc_id": doc.id,
                "chunk_index": i,
                "doc_name": doc.name,
                "category": doc.category,
                "headers": chunk.headers,
            }
            for i, chunk in enumerate(chunks)
        ]
        insert_chunks(rows)

        doc.chunk_count = len(chunks)
        doc.status = "indexed"
        doc.error_msg = ""
        db.commit()
        logger.info("文档入库完成 doc_id=%s chunks=%s", doc.id, len(chunks))
    except Exception as e:
        logger.exception("文档解析失败 doc_id=%s", doc_id)
        if doc is not None:
            doc.status = "failed"
            doc.error_msg = str(e)[:250]
            db.commit()
    finally:
        db.close()
