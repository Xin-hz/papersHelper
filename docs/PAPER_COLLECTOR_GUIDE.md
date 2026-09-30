# 论文自动采集模块使用指南

## 🎯 功能简介

论文自动采集模块可以帮助你从学术网站搜索、下载论文，并自动向量化录入到 RAG 知识库中。这样就能让 AI 助手基于最新的学术研究来生成论文、教案等内容。

## 🚀 快速开始

### 1. 安装依赖

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装新增的依赖包
pip install arxiv requests tqdm
```

或者重新安装所有依赖：
```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端（另一个终端）
cd frontend
npm run dev
```

### 3. 访问论文采集页面

打开浏览器访问：http://localhost:5173/collector

## 📖 使用步骤

### 界面操作

1. **输入搜索关键词**
   - 在搜索框中输入你想要的主题，如"幼儿园游戏化教学"
   - 支持中英文关键词

2. **选择数据源**
   - 目前支持 arXiv（计算机、物理、数学等）
   - 未来将支持中国知网、万方数据等

3. **设置参数**
   - 最大结果数：建议 10-20 篇
   - 年份范围：如 "2020-2024"（可选）

4. **搜索论文**
   - 点击"🔍 搜索论文"按钮
   - 等待搜索结果展示

5. **选择论文**
   - 勾选你想要的论文（默认选中所有有 PDF 的论文）
   - 可以查看标题、作者、摘要等信息

6. **采集入库**
   - 点击"📥 采集并入库"按钮
   - 系统会自动下载 PDF、提取文本、向量化、录入知识库

### API 调用

#### 搜索论文

```bash
curl -X POST http://localhost:8000/api/papers/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "幼儿园游戏化教学",
    "sources": ["arxiv"],
    "max_results": 20,
    "year_range": "2020-2024"
  }'
```

响应示例：
```json
{
  "success": true,
  "papers": {
    "arxiv": [
      {
        "title": "Gamification in Early Childhood Education",
        "authors": ["John Doe", "Jane Smith"],
        "year": 2023,
        "abstract": "This paper explores...",
        "doi": "arxiv.1234.5678",
        "download_url": "https://arxiv.org/pdf/2301.00001.pdf",
        "source": "arxiv",
        "pdf_available": true
      }
    ]
  },
  "total": 15
}
```

#### 采集并入库

```bash
curl -X POST http://localhost:8000/api/papers/collect \
  -H "Content-Type: application/json" \
  -d '{
    "query": "early childhood education",
    "sources": ["arxiv"],
    "max_papers": 5,
    "auto_ingest": true
  }'
```

响应示例：
```json
{
  "success": true,
  "message": "采集完成: 搜索 8 篇，下载 7 篇，入库 6 篇",
  "collected": 7,
  "ingested": 6,
  "failed": 1,
  "stats": {
    "ingested": 6,
    "failed": 1,
    "total_chunks": 234
  }
}
```

## 🔧 Python 代码调用

### 搜索论文

```python
from app.services.paper_collector import search_papers

# 搜索论文（只搜索，不下载数据库）
results = search_papers(
    query="machine learning in education",
    sources=["arxiv"],
    max_results=15,
    year_range="2020-2024"
)

# 查看结果
for source, papers in results.items():
    print(f"来源: {source}")
    for paper in papers:
        print(f"- {paper.title}")
        print(f"  作者: {', '.join(paper.authors)}")
        print(f"  年份: {paper.year}")
        print(f"  PDF可用: {paper.pdf_available}")
```

### 采集论文

```python
from app.services.paper_collector import collect_papers

# 采集论文（搜索、下载、入库一条龙）
result = collect_papers(
    query="educational technology",
    sources=["arxiv"],
    max_papers=10,
    year_range="2022-2024",
    auto_ingest=True  # 自动入库RAG
)

print(f"采集完成: {result['message']}")
print(f"成功入库: {result['ingested']} 篇")
print(f"文档片段: {result['stats']['total_chunks']} 个")
```

### 高级用法

```python
from app.services.paper_collector import PaperCollector

# 创建采集器实例
collector = PaperCollector()

# 只搜索论文
search_results = collector.search_papers(
    query="early childhood development",
    sources=["arxiv"],
    max_results=20
)

# 查看搜索结果
arxiv_papers = search_results.get("arxiv", [])
for paper in arxiv_papers:
    print(f"{paper.title} - {paper.authors}")

# 选择性采集
if arxiv_papers:
    # 采集前5篇
    result = collector.collect_and_ingest(
        query="early childhood development",
        sources=["arxiv"],
        max_papers=5,
        auto_ingest=True
    )
    print(f"采集结果: {result}")
```

## 📊 采集结果查询

采集完成后，论文的文本内容会被自动切片并向量化存储在 PostgreSQL + pgvector 中。你可以通过以下方式查询：

### 通过知识库问答

```bash
curl -X POST http://localhost:8000/api/ask_knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "question": "游戏化教学在幼儿园中的应用有哪些策略？",
    "top_k": 5
  }'
```

### 通过生成论文

采集的论文会自动用于论文生成：

```bash
curl -X POST http://localhost:8000/api/generate_paper \
  -H "Content-Type: application/json" \
  -d '{
    "title": "幼儿园区域活动中教师指导策略研究",
    "outline": "一、引言 二、文献综述 三、研究方法 四、结果与讨论 五、结论",
    "use_rag": true
  }'
```

## 🎨 界面功能说明

### 搜索区域
- **搜索关键词**: 输入你要研究的主题
- **数据源选择**: 选择要搜索的学术数据库
- **结果数量**: 控制搜索返回的论文数量
- **年份范围**: 限定论文发表年份（可选）

### 结果展示
- **论文列表**: 显示搜索到的所有论文
- **复选框**: 选择要采集的论文
- **元数据**: 显示标题、作者、年份、摘要
- **PDF 状态**: 标识论文是否可下载

### 采集进度
- **实时统计**: 显示已搜索、已下载、已入库、失败的数量
- **状态消息**: 显示当前采集进度和结果
- **错误提示**: 失败时会显示具体错误信息

## 🛠️ 技术架构

### 数据流

```
用户输入关键词
    ↓
arXiv API 搜索
    ↓
返回论文元数据（标题、作者、摘要、PDF链接）
    ↓
用户选择论文
    ↓
下载 PDF 文件
    ↓
提取文本内容
    ↓
文档切片（chunk_size=500）
    ↓
BGE 模型向量化
    ↓
存储到 pgvector
    ↓
可用于 RAG 问答和生成
```

### 核心组件

1. **ArxivCollector**: arXiv 论文搜索器
2. **PaperDownloader**: PDF 下载器
3. **PaperIngester**: 向量化入库器
4. **PaperCollector**: 总协调器

## ⚙️ 配置说明

### 环境变量

在 `.env` 文件中可以配置：

```env
# 采集目录
COLLECTION_DIR=./knowledge_uploads/collected_papers

# 并发下载数
MAX_CONCURRENT_DOWNLOADS=3

# 下载超时时间（秒）
PDF_DOWNLOAD_TIMEOUT=30

# 请求速率限制（每秒请求数）
ARXIV_RATE_LIMIT=1
```

### Embedding 配置

采集的论文需要向量化才能存储到 pgvector 中。你可以选择：

1. **本地 BGE 模型**（默认）
   - 首次使用会下载约 1.3GB 的模型
   - 优点：免费、无限使用
   - 缺点：需要下载、CPU 较慢

2. **通义 API**（推荐）
   - 在 `.env` 中设置：
     ```env
     EMBEDDING_PROVIDER=dashscope
     DASHSCOPE_API_KEY=your_api_key
     ```
   - 优点：速度快、无需下载模型
   - 缺点：需要 API key、有费用

## 🔍 使用场景

### 场景 1：研究特定主题

你想研究"幼儿园游戏化教学"，需要收集相关论文：

1. 访问论文采集页面
2. 输入关键词："kindergarten gamification education"
3. 选择数据源：arXiv
4. 点击搜索，查看结果
5. 选择相关论文，点击采集入库
6. 之后就可以用这些论文来生成新论文或回答问题

### 场景 2：更新知识库

定期更新你的知识库，保持最新研究：

1. 输入你的研究领域关键词
2. 设置年份范围为当前年份
3. 采集最新论文
4. 知识库自动更新

### 场景 3：交叉学科研究

研究跨学科主题，如"AI + 教育"：

1. 搜索 "artificial intelligence education"
2. 采集相关论文
3. 搜索 "machine learning teaching"
4. 继续采集
5. 获得跨学科的知识库

## 📈 扩展计划

### Phase 2（计划中）
- 中国知网（CNKI）支持
- 万方数据库支持
- 更智能的去重算法
- 论文分类管理

### Phase 3（未来）
- PubMed 医学论文支持
- Google Scholar 支持
- 引文分析功能
- 自动生成文献综述

## ⚠️ 注意事项

1. **首次使用**：需要下载 Embedding 模型（约 1.3GB），请确保网络畅通
2. **速率限制**：arXiv 有请求频率限制，请勿过于频繁搜索
3. **存储空间**：采集的 PDF 会存储在 `knowledge_uploads/collected_papers/` 目录
4. **PDF 处理**：部分复杂的 PDF 可能无法完全提取文本
5. **API 费用**：如使用通义 API，需注意费用消耗

## 🐛 故障排除

### 问题 1：搜索失败

**可能原因**：
- 网络连接问题
- arXiv API 暂时不可用
- 请求过于频繁

**解决方法**：
- 检查网络连接
- 等待几分钟后重试
- 减少搜索频率

### 问题 2：PDF 下载失败

**可能原因**：
- PDF 链接失效
- 网络超时
- 存储空间不足

**解决方法**：
- 检查网络连接
- 清理磁盘空间
- 增加下载超时时间

### 问题 3：向量化失败

**可能原因**：
- 模型未正确下载
- PDF 内容无法提取
- 内存不足

**解决方法**：
- 检查模型是否正确加载
- 尝试使用通义 API Embedding
- 增加系统内存

## 📞 技术支持

如有问题，请查看：
- [DEBUG_GUIDE.md](../DEBUG_GUIDE.md) - 调试指南
- [README.md](../README.md) - 项目说明
- [docs/API_EXAMPLES.md](API_EXAMPLES.md) - API 示例

---

享受自动化的论文采集体验！🎉