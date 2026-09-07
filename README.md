# 国际贸易上市公司一站式智能服务平台

基于 **MoPaaS 大模型应用引擎 + RAG + Agent** 打造的一站式外贸智能服务平台，帮助外贸企业「单人驾驭多语言交流」，显著降低对外贸业务员岗位的依赖。

> 当前仓库为**可运行脚手架**：LLM 主接入 **小米 MiMo V2.5**（`mimo-v2.5-pro`，备用 DeepSeek 故障转移），Embedding / 向量库默认 Mock / 内存（无需额外 Key 即可启动）；未配置 Key 时 LLM 自动降级 Mock，保证全流程可跑通。

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

详细设计见 [docs_跨境电商一站式智能服务平台/02-需求进度/项目大纲.md](docs_跨境电商一站式智能服务平台/02-需求进度/项目大纲.md)。

---

## 🚀 快速开始

### 环境要求
- Python ≥ 3.11（推荐 3.13）
- Node.js ≥ 18（前端开发）

### 一键启动（推荐）

双击 `start.bat`，或命令行运行：

```bash
python launcher.py            # 交互菜单
python launcher.py start      # 启动（依赖未变化时秒级启动，自动打开浏览器）
python launcher.py stop       # 一键停止前后端服务
python launcher.py restart    # 重启
python launcher.py status     # 查看服务运行状态
```

v2 启动器特性：依赖缓存（requirements.txt / package.json 未变化则跳过安装）、一键停止（按端口反查 PID）、端口被占用时可交互式释放、彩色状态输出。Windows 下也可直接双击 `start.bat` / `stop.bat` / `status.bat`。

### 1. 启动后端（手动方式）

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

---

## ⚙️ 环境配置指南

### 哪些文件不随仓库分发？（不是隐藏，是真实不存在）

以下内容被 `.gitignore` 排除，**克隆仓库后本地不会有**，需要按下面步骤自行生成：

| 未上传内容 | 原因 | 克隆后如何获得 |
|---|---|---|
| `.env` / `backend/.env` | 含 API Key 等敏感信息，**严禁入库** | 复制 `.env.example` 为 `.env` 并填写 |
| `backend/.venv/` | Python 虚拟环境体积大、平台相关 | `python -m venv .venv` + `pip install` |
| `frontend/node_modules/` | npm 依赖体积大 | `npm install` |
| `backend/data/*.db` | 运行时数据库 | 首次启动自动创建 |
| `backend/data/chroma/`、`index/` | 向量库持久化数据 | 重新执行 `python scripts/ingest.py` |
| `*.log` | 运行日志 | 自动生成 |

### 配置步骤（克隆后必读）

```bash
# 1) 生成环境配置（根目录 .env 供 docker-compose 使用；backend/.env 供源码开发使用）
cp .env.example .env
cp .env.example backend/.env

# 2) 编辑 .env，至少填写 LLM_API_KEY（不填则自动降级为 Mock 模式，流程可跑通但无真实 AI 输出）

# 3) 验证配置是否生效
cd backend && .venv/Scripts/python.exe scripts/check_config.py
```

### 关键配置项说明（`.env`）

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `LLM_PROVIDER` | `openai_compatible` | `mock`（离线演示）/ `openai_compatible`（任意 OpenAI 兼容接口） |
| `LLM_API_KEY` | 空 | 大模型 API Key，**必填**才能获得真实 AI 能力 |
| `LLM_BASE_URL` | 小米 MiMo | OpenAI 兼容 Base URL |
| `LLM_MODEL` | `mimo-v2.5-pro` | 模型 ID，见下方模型清单 |
| `LLM_TIMEOUT` | `60` | 单次请求超时（秒）；推理型模型建议 ≥ 60 |
| `LLM_FAILOVER` | DeepSeek 备用 | 格式 `base_url\|api_key\|model`，主端点异常/429/5xx 时自动切换 |
| `EMBEDDING_PROVIDER` | `mock` | `mock` 离线向量 / `openai_compatible` 真实嵌入 |
| `VECTOR_STORE` | `memory` | `memory`（开发）/ `chroma`（生产持久化） |
| `DATABASE_URL` | SQLite | 默认 `sqlite:///./data/app.db`，可换 PostgreSQL/MySQL |
| `AUTH_REQUIRED` | `false` | 演示免登录；生产改 `true` 启用 JWT 鉴权 |
| `JWT_SECRET_KEY` | 开发默认值 | **生产必须替换**：`python -c "import secrets; print(secrets.token_urlsafe(48))"` |

### 大模型供应商切换（改 3 行即可）

```ini
# 小米 MiMo（项目默认）——模型清单（2026-09 实测可用）：
#   mimo-v2.5 / mimo-v2.5-pro / mimo-v2.5-asr /
#   mimo-v2.5-tts / mimo-v2.5-tts-voiceclone / mimo-v2.5-tts-voicedesign
# 注：MiMo-V2 系列已于 2026-06-30 下线
LLM_BASE_URL=https://api.xiaomimimo.com/v1
LLM_MODEL=mimo-v2.5-pro
LLM_API_KEY=sk-你的小米Key

# DeepSeek
# LLM_BASE_URL=https://api.deepseek.com/v1
# LLM_MODEL=deepseek-v4-pro
# LLM_API_KEY=sk-你的DeepSeekKey

# 通义千问（DashScope 兼容模式）
# LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# LLM_MODEL=qwen-plus
# LLM_API_KEY=sk-你的DashScopeKey

# 故障转移示例（主端点异常时自动切 DeepSeek）
LLM_FAILOVER=https://api.deepseek.com/v1|sk-你的DeepSeekKey|deepseek-v4-flash
```

> 模型选择建议：智能客服等交互场景用 `mimo-v2.5`（非推理，1~3 秒响应）；深度分析用 `mimo-v2.5-pro`（推理型，思考期约 10~20 秒，前端会实时展示思考进度）。

### 安全提醒

- `.env` 已被 `.gitignore` 排除，**永远不会**被 `git add -A` 提交；若曾误提交，请立即吊销对应 Key。
- 生产环境：`AUTH_REQUIRED=true` + 强随机 `JWT_SECRET_KEY` + 关闭 `CORS_ORIGINS=["*"]`（改为具体域名）。

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
├── docs_跨境电商一站式智能服务平台/  # 需求、汇报与设计文档
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
