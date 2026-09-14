"""全局配置: 从环境变量 / .env 读取(env_file 锚定在 backend 目录,不依赖启动 cwd)"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ===== 服务 =====
    app_name: str = "电商商品知识库问答系统"
    debug: bool = True
    # JWT 签名密钥(生产环境务必修改)
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60 * 24

    # ===== MySQL =====
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "rag123456"
    mysql_db: str = "rag_db"
    # 可选: 直接指定完整连接串(测试/CI 用 SQLite 覆盖,不填则按上方 MySQL 配置拼接)
    database_url: str = ""

    # ===== Redis =====
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0

    # ===== Milvus 向量库 =====
    milvus_host: str = "127.0.0.1"
    milvus_port: int = 19530

    # ===== 大模型(DeepSeek,OpenAI 兼容接口)=====
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"

    # ===== 本地向量模型(M2 使用)=====
    embedding_model: str = "BAAI/bge-m3"
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    # 模型下载镜像(国内用 hf-mirror 加速)
    hf_endpoint: str = "https://hf-mirror.com"
    embedding_device: str = "cpu"

    # ===== 知识库(M2)=====
    milvus_collection: str = "product_kb"
    chunk_size: int = 500
    chunk_overlap: int = 50
    upload_dir: str = "data/uploads"
    max_upload_size_mb: int = 20

    @property
    def sqlalchemy_url(self) -> str:
        """SQLAlchemy 连接串(database_url 优先,便于测试覆盖)"""
        if self.database_url:
            return self.database_url
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"
        )

    @property
    def upload_dir_path(self) -> Path:
        """上传文件目录(锚定 backend 目录,不依赖启动 cwd)"""
        return BASE_DIR / self.upload_dir


settings = Settings()
