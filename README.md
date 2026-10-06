# 幼儿园教师 AI 论文助手

基于 Python + FastAPI + LangChain + pgvector 的幼儿园教师 AI 助手后端，支持知识库 RAG、论文生成/润色/降重、教案与教学案例生成。

## 功能

1. **论文生成**：按主题与大纲生成学术论文  
2. **教案生成**：按主题、年龄段、领域生成完整教案  
3. **教学案例生成**：按主题与场景生成教学案例  
4. **论文润色**：提升学术性与语言流畅度  
5. **论文降重**：同义替换与句式改写降低重复率  
6. **知识库问答**：上传 PDF/DOCX 后基于 RAG 回答问题  

支持上传 PDF/DOCX 知识库、自动分块向量化、使用 RAG 回答。

## 技术栈

- **后端**: Python 3.10+ / FastAPI
- **LLM**: Kimi（月之暗面）/ 通义千问（Qwen，OpenAI 兼容）
- **向量库**: PostgreSQL + pgvector
- **Embedding**: BGE-large-zh（sentence-transformers）
- **RAG**: LangChain（检索 + 生成）

## 项目结构

```
PapersHelper/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置（环境变量）
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # 接口路由
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # 请求/响应模型
│   └── services/
│       ├── __init__.py
│       ├── document_loader.py   # PDF/DOCX 加载与切片
│       ├── vector_store.py     # pgvector + BGE Embedding
│       ├── llm_service.py      # Kimi/Qwen 调用
│       ├── rag_service.py      # RAG 问答
│       └── paper_service.py    # 论文/教案/教学案例/润色/降重/扩写
├── knowledge_uploads/      # 上传的知识库文件（可配置）
├── requirements.txt
├── .env.example
└── README.md
```

## 环境准备

### 1. PostgreSQL + pgvector

**方式 A：Docker（推荐，不依赖 Homebrew）**  
已安装 Docker 时，在项目根目录执行：

```bash
docker compose up -d
```

等待几秒后执行：`python scripts/init_db.py`

**方式 B：本机 PostgreSQL**  
`createdb papers_helper` 后执行 `python scripts/init_db.py`

**方式 C：Postgres.app（Mac）**  
从 https://postgresapp.com 下载，启动后执行 `createdb papers_helper`，再执行 `python scripts/init_db.py`

### 2. Python 依赖

```bash
cd PapersHelper
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 环境变量

复制示例配置并填写 API Key：

```bash
cp .env.example .env
# 编辑 .env，至少设置：
# - DATABASE_URL
# - LLM_PROVIDER（kimi 或 qwen）
# - KIMI_API_KEY 或 QWEN_API_KEY（按所选提供商）
```

## 运行

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API 文档: http://localhost:8000/docs  
- 健康检查: http://localhost:8000/health  
- **接口请求示例（curl）**：见 [docs/API_EXAMPLES.md](docs/API_EXAMPLES.md)，便于复制调试。

## 前端

前端为 Vue 3 + Vite 单页应用。开发：`cd frontend && npm install && npm run dev`（http://localhost:5173）。构建：`npm run build`，完成后访问 http://localhost:8000/app/ 使用（后端会自动挂载 frontend/dist）。详见 [docs/FRONTEND_FLOW.md](docs/FRONTEND_FLOW.md) 与 [frontend/README.md](frontend/README.md)。

## 独立技能版（paper-helper，推荐给同事）

本仓库另含一个**零依赖、可单独分发**的论文助手技能 [skills/paper-helper](skills/paper-helper/)：
写论文四步流程 + 改论文四操作、浙江获奖选题库 1459 条、本地知识库检索、成稿自检与评选规范 Word 排版。
同事无需部署本后端，粘贴一段安装提示词即可装好——见 [skills/paper-helper/INSTALL.md](skills/paper-helper/INSTALL.md)。

## 接口说明

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ask_knowledge` | 知识库 RAG 问答 |
| POST | `/api/generate_paper` | 论文生成 |
| POST | `/api/generate_lesson_plan` | 教案生成 |
| POST | `/api/generate_teaching_case` | 教学案例生成 |
| POST | `/api/improve_paper` | 论文润色 |
| POST | `/api/reduce_weight` | 论文降重 |
| POST | `/api/expand_paper` | 论文扩写 |
| POST | `/api/upload_knowledge` | 上传 PDF/DOCX 到知识库（自动切片向量化） |

### 请求示例

**知识库问答**  
`POST /api/ask_knowledge`  
```json
{ "question": "幼儿园游戏化教学有哪些常见策略？", "top_k": 5 }
```

**论文生成**  
`POST /api/generate_paper`  
```json
{ "title": "幼儿园区域活动中教师指导策略研究", "outline": "一、引言 二、文献综述 三、研究方法 四、结果与讨论 五、结论", "use_rag": true }
```

**论文润色**  
`POST /api/improve_paper`  
```json
{ "content": "这是待润色的一段论文正文...", "focus": "学术性与语言流畅" }
```

**论文扩写**  
`POST /api/expand_paper`  
```json
{ "content": "待扩写的段落...", "target_section": "文献综述", "use_rag": true }
```

**教案生成**  
`POST /api/generate_lesson_plan`  
```json
{ "topic": "认识四季", "grade": "大班", "subject": "科学", "duration": "一课时", "use_rag": true }
```

**教学案例生成**  
`POST /api/generate_teaching_case`  
```json
{ "topic": "区域活动中幼儿争抢材料", "scenario": "区域活动", "use_rag": true }
```

**论文降重**  
`POST /api/reduce_weight`  
```json
{ "content": "待降重的论文段落...", "focus": "同义替换与句式改写" }
```

**上传知识库**  
`POST /api/upload_knowledge`  
- `Content-Type: multipart/form-data`
- 字段: `file`，支持 `.pdf` / `.docx`

上传后会自动按配置的 `chunk_size` / `chunk_overlap` 切片并写入 pgvector，供 RAG 使用。

## 配置说明

- `CHUNK_SIZE` / `CHUNK_OVERLAP`: 文档切片大小与重叠，影响检索粒度。
- `TOP_K_RETRIEVE`: RAG 检索返回的文档数。
- `EMBEDDING_DEVICE`: `cpu` 或 `cuda`（有 GPU 时可设为 `cuda` 加速）。

首次使用 BGE 模型时会从 HuggingFace 下载，请保证网络畅通或配置镜像。

## License

MIT
