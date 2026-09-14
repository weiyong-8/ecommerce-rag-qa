"""向量化: bge-m3 本地模型(懒加载单例,首次使用自动下载)"""
import os

from app.config import settings

# 必须在导入 sentence-transformers 之前设置镜像地址
os.environ.setdefault("HF_ENDPOINT", settings.hf_endpoint)

_embedding_model = None


def get_embedding_model():
    """懒加载 bge-m3(1024 维,中文效果优,向量归一化后配合余弦相似度)"""
    global _embedding_model
    if _embedding_model is None:
        from langchain_huggingface import HuggingFaceEmbeddings

        _embedding_model = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"device": settings.embedding_device},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embedding_model
