"""Milvus 向量库封装: 集合 Schema 设计 / 批量写入 / 按文档删除 / 检索

集合 Schema(pk 自增主键 + 文本 + bge-m3 向量 + 标量元数据):
- doc_id / chunk_index: 引用回源与片段定位
- doc_name / category / headers: 引用展示与类目过滤检索
索引: HNSW + COSINE(bge-m3 向量已归一化); M6 将做参数调优
"""
import logging

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from app.config import settings

logger = logging.getLogger(__name__)

VECTOR_DIM = 1024  # bge-m3 输出维度

_COLLECTION: Collection | None = None


def _connect() -> None:
    """连接 Milvus(幂等,重复连接直接忽略)"""
    try:
        connections.connect(
            alias="default", host=settings.milvus_host, port=settings.milvus_port
        )
    except Exception:
        pass


def _ensure_collection() -> Collection:
    """首次使用时创建集合与 HNSW 索引,已存在则直接复用"""
    _connect()
    if not utility.has_collection(settings.milvus_collection):
        fields = [
            FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM),
            FieldSchema(name="doc_id", dtype=DataType.INT64),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            FieldSchema(name="doc_name", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="headers", dtype=DataType.VARCHAR, max_length=512),
        ]
        schema = CollectionSchema(fields, description="电商商品知识库文档片段(bge-m3 向量)")
        col = Collection(name=settings.milvus_collection, schema=schema)
        col.create_index(
            field_name="vector",
            index_params={
                "index_type": "HNSW",
                "metric_type": "COSINE",
                "params": {"M": 16, "efConstruction": 200},
            },
        )
        logger.info("Milvus 集合已创建: %s", settings.milvus_collection)
    else:
        col = Collection(name=settings.milvus_collection)
    return col


def get_collection() -> Collection:
    global _COLLECTION
    if _COLLECTION is None:
        _COLLECTION = _ensure_collection()
    return _COLLECTION


def insert_chunks(rows: list[dict]) -> int:
    """批量写入片段(分批插入,插入后 flush 保证可见),返回写入条数"""
    if not rows:
        return 0
    col = get_collection()
    batch_size = 256
    for i in range(0, len(rows), batch_size):
        col.insert(rows[i : i + batch_size])
    col.flush()
    return len(rows)


def delete_by_doc(doc_id: int) -> None:
    """删除某文档的全部片段(标量过滤删除)"""
    col = get_collection()
    col.delete(expr=f"doc_id == {doc_id}")
    col.flush()


def search_similar(query_vector: list[float], top_k: int = 20, category: str = "") -> list[dict]:
    """向量相似检索,返回 [{text, doc_id, chunk_index, doc_name, category, headers, score}]"""
    col = get_collection()
    col.load()
    expr = f'category == "{category}"' if category else None
    res = col.search(
        data=[query_vector],
        anns_field="vector",
        param={"metric_type": "COSINE", "params": {"ef": 128}},
        limit=top_k,
        expr=expr,
        output_fields=[
            "text",
            "doc_id",
            "chunk_index",
            "doc_name",
            "category",
            "headers",
        ],
    )
    hits = []
    for hit in res[0]:
        entity = hit.entity
        hits.append(
            {
                "text": entity.get("text"),
                "doc_id": entity.get("doc_id"),
                "chunk_index": entity.get("chunk_index"),
                "doc_name": entity.get("doc_name"),
                "category": entity.get("category"),
                "headers": entity.get("headers"),
                "score": round(hit.distance, 4),
            }
        )
    return hits
