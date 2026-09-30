# 启动调试指南

## 项目概况
- **后端**: FastAPI + Python 3.10+
- **前端**: Vue 3 + Vite
- **数据库**: PostgreSQL + pgvector
- **LLM**: Kimi/通义千问
- **向量检索**: BGE-large-zh + LangChain

## 🚀 快速启动

### 1️⃣ 启动数据库（Docker 推荐）
```bash
# 在项目根目录执行
docker compose up -d
```

等待几秒后初始化数据库：
```bash
python scripts/init_db.py
```

### 2️⃣ 启动后端服务
```bash
# 激活虚拟环境
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 启动后端（热重载模式）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将运行在：http://localhost:8000

### 3️⃣ 启动前端开发服务器
```bash
# 新开一个终端
cd frontend
npm run dev
```

前端开发服务器将运行在：http://localhost:5173

## 🔍 调试模式

### 后端调试
```bash
# VS Code 调试配置
# 在 .vscode/launch.json 中添加：
{
  "name": "FastAPI Debug",
  "type": "python",
  "request": "launch",
  "module": "uvicorn",
  "args": [
    "app.main:app",
    "--reload",
    "--host", "0.0.0.0",
    "--port", "8000"
  ],
  "envFile": "${workspaceFolder}/.env",
  "console": "integratedTerminal",
  "justMyCode": false
}
```

### 前端调试
```bash
# 前端已经支持热重载，修改代码后自动刷新
# 浏览器打开 http://localhost:5173
# 使用浏览器开发者工具调试
```

## 📡 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 后端 API | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 健康检查 | http://localhost:8000/health | 服务状态 |
| 前端开发 | http://localhost:5173 | Vite 开发服务器 |
| 前端生产 | http://localhost:8000/app/ | 构建后的前端 |

## 🧪 测试接口

### 使用 curl 测试
```bash
# 健康检查
curl http://localhost:8000/health

# 知识库问答
curl -X POST http://localhost:8000/api/ask_knowledge \
  -H "Content-Type: application/json" \
  -d '{"question": "幼儿园游戏化教学有哪些常见策略？", "top_k": 5}'

# 论文生成
curl -X POST http://localhost:8000/api/generate_paper \
  -H "Content-Type: application/json" \
  -d '{"title": "幼儿园区域活动中教师指导策略研究", "outline": "一、引言 二、文献综述", "use_rag": true}'
```

### 使用 Swagger UI 测试
1. 访问 http://localhost:8000/docs
2. 点击接口展开详情
3. 点击 "Try it out"
4. 填写参数并执行

## 🐛 常见问题

### 1. PostgreSQL 连接失败
```bash
# 检查 Docker 容器状态
docker ps -a | grep postgres

# 查看 PostgreSQL 日志
docker logs papers-helper-postgres-1

# 重启容器
docker compose restart
```

### 2. Python 依赖问题
```bash
# 重新安装依赖
pip install -r requirements.txt

# 检查关键依赖
pip list | grep -E "fastapi|uvicorn|langchain|psycopg2"
```

### 3. 前端构建失败
```bash
cd frontend

# 清理并重新安装
rm -rf node_modules package-lock.json
npm install

# 重新构建
npm run build
```

### 4. API Key 相关错误
```bash
# 检查 .env 文件配置
cat .env | grep -E "LLM_PROVIDER|API_KEY"

# 确保 .env 中设置了：
# - LLM_PROVIDER=kimi 或 qwen
# - KIMI_API_KEY 或 QWEN_API_KEY
```

### 5. pgvector 扩展问题
```bash
# 重新初始化数据库
python scripts/init_db.py
```

## 🔧 开发工具推荐

### VS Code 扩展
- Python (Microsoft)
- Vue Language Features (Volar)
- Pylance
- REST Client (用于 API 测试)

### 浏览器插件
- Vue.js devtools (前端调试)

## 📝 环境变量检查清单

确保 `.env` 文件包含以下配置：

```env
# 数据库连接
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/papers_helper

# LLM 提供商（kimi 或 qwen）
LLM_PROVIDER=kimi

# API Keys（根据选择的提供商设置其一）
KIMI_API_KEY=your_kimi_api_key
# QWEN_API_KEY=your_qwen_api_key

# Embedding 配置
EMBEDDING_PROVIDER=local  # 或 dashscope
EMBEDDING_DEVICE=cpu      # 或 cuda（有 GPU 时）

# RAG 配置
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RETRIEVE=5
```

## 🎯 启动流程总结

1. **启动数据库**: `docker compose up -d`
2. **初始化数据库**: `python scripts/init_db.py`
3. **启动后端**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
4. **启动前端（开发模式）**: `cd frontend && npm run dev`
5. **访问应用**: http://localhost:5173 或 http://localhost:8000/app/

## 💡 调试技巧

1. **后端日志**: 终端会显示请求日志和错误信息
2. **前端日志**: 浏览器开发者工具 Console 面板
3. **API 测试**: 使用 Swagger UI (http://localhost:8000/docs)
4. **数据库查询**: 使用 Docker exec 进入容器
   ```bash
   docker exec -it papers-helper-postgres-1 psql -U postgres -d papers_helper
   ```

## 📚 更多文档

- [README.md](README.md) - 项目说明
- [docs/API_EXAMPLES.md](docs/API_EXAMPLES.md) - API 请求示例
- [docs/FRONTEND_FLOW.md](docs/FRONTEND_FLOW.md) - 前端流程说明
- [frontend/README.md](frontend/README.md) - 前端开发指南
