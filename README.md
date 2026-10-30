# 基于 LangChain 的电商商品知识库问答系统

面向电商商品场景的**企业级 RAG 知识库问答系统**:用户在浏览器中管理知识库、进行引用式问答,支持多用户多会话、会话历史持久化与管理员权限隔离。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11 + FastAPI + LangChain 0.3.x |
| 前端 | Vue 3 + Vite + Element Plus + Pinia |
| 向量库 | Milvus standalone(Docker) |
| 业务库 | MySQL 8(Docker) |
| 缓存 | Redis 7(Docker) |
| 对话模型 | DeepSeek API(OpenAI 兼容接口,可配置切换) |
| Embedding / 重排序 | BAAI/bge-m3 / bge-reranker-v2-m3(本地运行) |

## 目录结构

```
ecommerce-rag-qa/
├── docker-compose.yml      # MySQL + Redis + Milvus(+etcd/minio)
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # 入口(健康检查)
│   │   ├── config.py       # 全局配置(.env)
│   │   ├── api/            # 接口路由(M1 起)
│   │   ├── core/           # 安全: JWT/密码哈希(M1 起)
│   │   ├── models/         # SQLAlchemy 模型(M1 起)
│   │   ├── services/       # 业务逻辑
│   │   └── rag/            # RAG 模块(M2 起)
│   ├── requirements.txt    # 锁定版本
│   └── .env                # 本地配置(不入 git)
└── frontend/               # Vue3 前端
    └── src/
        ├── views/          # 登录 / 问答 / 知识库管理
        ├── router/         # 路由(含 admin 守卫 TODO)
        ├── stores/         # Pinia 登录态
        └── api/            # axios 封装
```

## 快速启动

### 0. 前置条件
- Docker Desktop(macOS 从官网安装)
- Python 3.11+ / Node 20+
- DeepSeek API Key(https://platform.deepseek.com)

### 1. 启动基础设施
```bash
docker compose up -d
# MySQL: 3306  Redis: 6379  Milvus: 19530(控制台 9091,MinIO 9001)
docker compose ps   # 查看健康状态
```

### 2. 启动后端
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# 编辑 .env,填入 DEEPSEEK_API_KEY
uvicorn app.main:app --reload --port 8000
```
接口文档: http://127.0.0.1:8000/docs

### 3. 启动前端
```bash
cd frontend
npm install
npm run dev
```
访问 http://localhost:5173(`/api` 自动代理到后端 8000)

## 里程碑进度

| 阶段 | 内容 | 状态 |
|---|---|---|
| M0 | 环境骨架: git/docker-compose/前后端脚手架 | ✅ 已完成 |
| M1 | 认证体系: 注册/登录/改密、JWT、角色校验、admin 种子 | ✅ 已完成 |
| M2 | 知识库管理: 上传→解析→切分→向量化→Milvus 入库 | ✅ 已完成(Milvus 入库待 Docker 验证) |
| M3 | RAG 问答: 检索→重排→LLM→引用,SSE 流式 | ✅ 已完成(端到端待 Docker+Key) |
| M4 | 会话与历史: 会话 CRUD、历史恢复、自动标题 | ✅ 已完成 |
| M5 | 前端界面: 登录页、聊天页(流式+引用卡片)、管理页 | ✅ 已完成 |
| M6 | 性能优化: 混合检索、语义缓存、限流、索引调优+压测 | ⬜ |
| M7 | 收尾: 测试数据、一键部署、性能压测 | ⬜ |

## 性能优化清单(后续计划)

混合检索(BM25+向量+RRF)→ bge-reranker 精排 → SSE 流式输出 → Redis 语义缓存 → 全链路异步 → Milvus HNSW 调优 → 连接池/限流 → 压测对比数据(Locust)
