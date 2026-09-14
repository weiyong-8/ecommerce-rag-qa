"""知识库管理接口(仅管理员: 路由级 require_admin 统一校验)"""
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.core.database import get_db
from app.core.deps import require_admin
from app.models import Document, User
from app.schemas.kb import DocumentOut
from app.services import kb_service

router = APIRouter(
    prefix="/kb",
    tags=["知识库"],
    dependencies=[Depends(require_admin)],  # 全部接口仅管理员可访问
)

ALLOWED_EXTENSIONS = set(kb_service.ALLOWED_TYPES.keys())


def _get_doc(db: Session, doc_id: int) -> Document:
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "文档不存在")
    return doc


@router.post(
    "/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
    summary="上传知识库文档",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form("通用"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"不支持的文件类型: {ext}(支持: {', '.join(sorted(ALLOWED_EXTENSIONS))})",
        )

    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"文件过大(上限 {settings.max_upload_size_mb}MB)",
        )

    doc = Document(
        name=file.filename,
        file_type=kb_service.ALLOWED_TYPES[ext],
        category=category,
        file_size=len(content),
        uploader_id=admin.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    path = kb_service.upload_path(doc.id, doc.file_type)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)

    # 后台解析入库,不阻塞上传响应
    background_tasks.add_task(kb_service.process_document, doc.id)
    return doc


@router.get("/documents", response_model=list[DocumentOut], summary="文档列表")
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.id.desc()).all()


@router.get("/documents/{doc_id}", response_model=DocumentOut, summary="文档详情")
def get_document(doc_id: int, db: Session = Depends(get_db)):
    return _get_doc(db, doc_id)


@router.post(
    "/documents/{doc_id}/reprocess",
    response_model=DocumentOut,
    summary="重新解析入库",
)
def reprocess_document(
    doc_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    doc = _get_doc(db, doc_id)
    background_tasks.add_task(kb_service.process_document, doc.id)
    return doc


@router.delete("/documents/{doc_id}", summary="删除文档")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = _get_doc(db, doc_id)
    kb_service.delete_document(db, doc)
    return {"message": "删除成功"}


@router.get("/stats", summary="知识库统计")
def kb_stats(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Document.status,
            func.count(Document.id),
            func.coalesce(func.sum(Document.chunk_count), 0),
        )
        .group_by(Document.status)
        .all()
    )
    by_status = {
        s: {"documents": cnt, "chunks": chunks} for s, cnt, chunks in rows
    }
    return {
        "documents": db.query(func.count(Document.id)).scalar() or 0,
        "chunks": db.query(func.coalesce(func.sum(Document.chunk_count), 0)).scalar()
        or 0,
        "by_status": by_status,
    }
