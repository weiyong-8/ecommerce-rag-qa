"""重排序: bge-reranker-v2-m3 对召回片段精排(懒加载单例)"""
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_core.documents import Document

from app.config import settings

_reranker = None


def get_reranker() -> CrossEncoderReranker:
    global _reranker
    if _reranker is None:
        model = HuggingFaceCrossEncoder(
            model_name=settings.rerank_model,
            model_kwargs={"device": settings.embedding_device},
        )
        _reranker = CrossEncoderReranker(model=model, top_n=5)
    return _reranker


def rerank(query: str, hits: list[dict]) -> list[dict]:
    """对检索结果精排,返回 top-5 片段(保留原元数据)"""
    if len(hits) <= 5:
        return hits
    docs = [Document(page_content=h["text"], metadata=h) for h in hits]
    ranked = get_reranker().compress_documents(docs, query)
    return [dict(d.metadata) for d in ranked]
