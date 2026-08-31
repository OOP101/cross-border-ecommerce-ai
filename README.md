# 国际贸易上市公司一站式智能服务平台

基于 **MoPaaS 大模型应用引擎 + RAG + Agent** 打造的一站式外贸智能服务平台，帮助外贸企业「单人驾驭多语言交流」，显著降低对外贸业务员岗位的依赖。

> 当前仓库为**可运行脚手架**：LLM 默认接入 **DeepSeek**（`deepseek-v4-pro`），Embedding / 向量库默认 Mock / 内存（无需额外 Key 即可启动）；未配置 Key 时 LLM 自动降级 Mock，保证全流程可跑通。

---

## ✨ 核心能力

| 模块 | 说明 | 状态 |
|------|------|------|
| 智能文案生成 | 商品描述 / 广告语 / 活动文案 / SEO 标签，多语言 | ✅ |
| 多语言翻译引擎 | 30+ 语种实时翻译 + **持久化术语库** + 翻译记忆 | ✅ |
| RAG 智能客服 | 混合检索 + 重排序 + 知识溯源 + 多轮对话 | ✅ |
| 知识库管理 | 多格式上传、清洗、分块、向量化、增量更新 | ✅ |
| 数据洞察 | 客服满意度、意图分布、Token 消耗看板 | ✅ |
| 管理后台 | 模型配置、知识库、监控告警、审计日志 | ✅ |

---

## 🏗️ 架构

四层分层架构：

```
用户交互层   Web端 | 移动端 | REST API | 微信/WhatsApp 等渠道
服务编排层   对话管理 | 意图识别 | 上下文管理 | Agent 工作流编排(LangGraph)
RAG检索层    问题解析 | 混合检索(BM25+向量) | 重排序 | 上下文拼接
数据模型层   向量库 | 知识库 | LLM推理引擎 | 翻译模型 | 缓存
```

详细设计见 [docs/项目大纲.md](docs/项目大纲.md)。

---

## 🚀 快速开始

### 环境要求
- Python ≥ 3.11（推荐 3.13）
- Node.js ≥ 18（前端开发）

### 1. 启动后端

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt

# 导入示例知识库（可选，用于体验 RAG 效果）
python scripts/ingest.py

# 启动服务
uvicorn app.main:app --reload --port 8009
```

接口文档（Swagger）：http://localhost:8009/docs

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

### 3. 配置真实大模型（可选）

项目默认已切换为 **DeepSeek**（真实 Key 已写入 `backend/.env`，被 git 忽略）。如需更换模型或 Key，修改：

```ini
LLM_PROVIDER=openai_compatible
LLM_API_KEY=sk-你的DeepSeekKey
LLM_BASE_URL=https://api.deepseek.com/v1
# deepseek-v4-pro（旗舰首选）/ deepseek-v4-flash（均衡性价比首选）
LLM_MODEL=deepseek-v4-pro
```

---

## 📁 目录结构

```
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py          # 应用入口
│   │   ├── config.py        # 配置（pydantic-settings）
│   │   ├── api/v1/          # 六大模块 REST API
│   │   ├── core/            # LLM / Embedding / 向量库 抽象
│   │   ├── services/        # RAG / 客服 / 文案 / 翻译 / Agent / 洞察
│   │   ├── models/          # Pydantic schemas
│   │   ├── db/              # SQLAlchemy 数据模型
│   │   └── utils/           # 分块 / 清洗 / PII / 分词
│   ├── data/knowledge/      # 示例知识库文档
│   └── scripts/ingest.py    # 知识导入脚本
├── frontend/                # Vue 3 + Element Plus
│   └── src/views/           # 六大功能页面
├── docs/                    # 架构与设计文档
└── docker-compose.yml       # 本地编排
```

---

## 🔌 可插拔设计

所有外部能力均通过抽象接口隔离，配置切换即可替换：

- **LLM**：`core/llm` —— `mock` / `openai_compatible`（通义千问、DeepSeek、OpenAI 等）
- **Embedding**：`core/embeddings` —— `mock` / `openai_compatible` / `sentence-transformers`
- **向量库**：`core/vector_store` —— `memory` / `chroma`（可扩展 Milvus）
- **Agent**：`services/agent` —— 内置规则路由，安装 `langgraph` 后自动升级为图编排

---

## 🔐 鉴权与术语库

### 鉴权（JWT，零第三方依赖）
- 基于标准库实现 PBKDF2 密码哈希 + HS256 JWT（`app/core/security.py`），无需安装 `pyjwt` / `passlib`。
- 演示模式 `AUTH_REQUIRED=false` 时管理后台等接口免登录；生产在 `.env` 设 `AUTH_REQUIRED=true` 后，接口需携带 `Authorization: Bearer <token>`。
- 默认播种管理员：`admin / admin123`（**生产务必修改**）。

```bash
# 登录获取令牌
curl -X POST http://localhost:8009/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}'

# 携带令牌访问受保护接口
curl http://localhost:8009/api/v1/admin/status \
  -H 'Authorization: Bearer <token>'
```

### 术语库（P0 专业术语库，已持久化）
- 术语存于数据库表 `terminology`，随知识库一起增量更新，保证多语言译法一致。
- 管理接口：`GET/POST /api/v1/translation/terminology`。

### 配置自检
无需 API Key 即可确认当前生效的实现：

```bash
cd backend
.venv/Scripts/python.exe scripts/check_config.py
```

---

## 📄 许可

内部项目脚手架，遵循公司数据安全与合规要求。
