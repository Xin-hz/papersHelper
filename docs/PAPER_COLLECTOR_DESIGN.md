# 论文自动采集与录入模块设计

## 🎯 功能概述

新增一个论文自动采集模块，支持从多个学术网站根据特定主题搜索、下载论文，并自动向量化录入到 RAG 知识库中。

## 🏗️ 模块架构

```
paper_collector/
├── paper_collector.py       # 主服务：论文采集协调器
├── sources/
│   ├── arxiv_collector.py   # arXiv 论文采集
│   ├── cnki_collector.py    # 中国知网采集
│   ├── wanfang_collector.py # 万方数据库采集
│   └── pubmed_collector.py  # PubMed 采集
├── processors/
│   ├── pdf_processor.py     # PDF 处理和提取
│   └── metadata_extractor.py # 元数据提取
└── utils/
    ├── rate_limiter.py      # 请求频率限制
    └── academic_search.py   # 学术搜索工具
```

## 🔍 支持的数据源

### 1. arXiv.org
- **优势**: 免费、API 友好、PDF 直接下载
- **范围**: 计算机、物理、数学、生物等
- **API**: arXiv API (无需认证)

### 2. 中国知网 (CNKI) 
- **优势**: 中文学术资源丰富
- **范围**: 教育学、学前教育相关论文
- **挑战**: 需要模拟登录或使用机构访问

### 3. 万方数据
- **优势**: 中文学术资源
- **范围**: 各学科期刊论文
- **挑战**: 需要处理验证码或机构访问

### 4. PubMed
- **优势**: 医学、生物学免费资源
- **范围**: 医学、心理学、特殊教育
- **API**: NCBI E-utilities (免费)

## 📊 核心功能

### 1. 论文搜索
```python
class PaperSearcher:
    def search(self, query: str, max_results: int = 10) -> List[PaperMetadata]:
        """多源搜索论文"""
        pass
```

### 2. 论文下载
```python
class PaperDownloader:
    def download(self, metadata: PaperMetadata) -> Optional[Path]:
        """下载论文PDF到本地"""
        pass
```

### 3. 自动入库
```python
class PaperIngester:
    def ingest(self, pdf_path: Path, metadata: PaperMetadata) -> bool:
        """向量化并录入知识库"""
        pass
```

## 🔄 工作流程

```
用户输入主题关键词
    ↓
并行搜索多个数据源
    ↓
去重和相关性排序
    ↓
批量下载PDF
    ↓
处理和文本提取
    ↓
向量化录入RAG
    ↓
返回采集结果统计
```

## 🛡️ 限制和策略

### 速率限制
- arXiv: 每秒最多1个请求
- CNKI: 每秒最多0.5个请求  
- PubMed: 每秒最多3个请求

### 质量控制
- 只下载完整PDF
- 过滤掉页数过少的论文(< 3页)
- 提取标题、作者、摘要等元数据

### 存储管理
- 按主题分类存储
- 自动去重(基于DOI或标题+作者)
- 定期清理临时文件

## 📡 API 接口设计

### 1. 搜索论文
```http
POST /api/papers/search
Content-Type: application/json

{
  "query": "幼儿园游戏化教学",
  "sources": ["arxiv", "cnki"],
  "max_results": 20,
  "year_range": "2020-2024"
}

Response:
{
  "success": true,
  "papers": [
    {
      "title": "游戏化教学在幼儿园的应用研究",
      "authors": ["张三", "李四"],
      "year": 2023,
      "abstract": "...",
      "source": "cnki",
      "doi": "10.xxxx/xxxx",
      "download_url": "https://...",
      "pdf_available": true
    }
  ],
  "total": 15
}
```

### 2. 采集和入库
```http
POST /api/papers/collect
Content-Type: application/json

{
  "query": "幼儿园教师专业发展",
  "sources": ["cnki", "wanfang"],
  "max_papers": 10,
  "auto_ingest": true,
  "year_range": "2022-2024"
}

Response:
{
  "success": true,
  "collected": 8,
  "ingested": 7,
  "failed": 1,
  "errors": ["某论文PDF下载失败"],
  "stats": {
    "total_chunks": 234,
    "total_sources": ["cnki", "wanfang"]
  }
}
```

### 3. 采集状态查询
```http
GET /api/papers/status

Response:
{
  "total_papers": 156,
  "total_chunks": 4567,
  "recent_collections": [
    {
      "query": "幼儿园区域活动",
      "collected_at": "2024-03-15T10:30:00",
      "paper_count": 12
    }
  ]
}
```

## 💾 数据存储结构

### 采集元数据表
```sql
CREATE TABLE paper_collections (
    id SERIAL PRIMARY KEY,
    query VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    authors TEXT[],
    year INTEGER,
    doi VARCHAR(100),
    abstract TEXT,
    download_url TEXT,
    local_path TEXT,
    ingested BOOLEAN DEFAULT FALSE,
    ingested_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(doi),
    CONSTRAINT unique_paper UNIQUE(source, title, authors)
);
```

### 采集历史表
```sql
CREATE TABLE collection_history (
    id SERIAL PRIMARY KEY,
    query VARCHAR(255) NOT NULL,
    sources TEXT[] NOT NULL,
    total_collected INTEGER DEFAULT 0,
    total_ingested INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'running',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

## 🎨 前端界面设计

### 1. 采集页面
- 搜索框：输入主题关键词
- 数据源选择：多选框选择要搜索的数据库
- 筛选条件：年份范围、论文类型等
- 结果展示：显示搜索到的论文列表
- 批量操作：选择论文进行采集入库

### 2. 管理页面  
- 采集历史：显示所有采集任务
- 知识库统计：显示论文数量、文档片段数量
- 去重管理：识别和删除重复论文
- 导出功能：导出论文列表为Excel

## ⚙️ 配置参数

### 环境变量
```env
# 论文采集配置
COLLECTION_DIR=./knowledge_uploads/collected_papers
MAX_CONCURRENT_DOWNLOADS=3
PDF_DOWNLOAD_TIMEOUT=30
ENABLE_CNKI_SCRAPER=true
CNKI_INSTITUTION_TOKEN=...

# 速率限制
ARXIV_RATE_LIMIT=1
CNKI_RATE_LIMIT=0.5
PUBMED_RATE_LIMIT=3
```

## 🔧 实现优先级

### Phase 1 (MVP)
- arXiv 论文采集
- 基础 PDF 下载和入库
- 简单的搜索界面

### Phase 2  
- CNKI 采集支持
- 更完善的元数据提取
- 采集历史管理

### Phase 3
- 万方、PubMed 支持
- 智能去重和推荐
- 高级筛选和导出功能

## 🚨 风险和挑战

### 技术风险
1. **反爬虫机制**: 知网等可能有严格的反爬措施
2. **PDF 解析**: 复杂格式的PDF可能解析困难
3. **性能问题**: 大规模论文采集可能耗时较长

### 解决方案
1. 使用合理的请求间隔和User-Agent轮换
2. 使用多个PDF解析库作为后备方案
3. 实现异步处理和进度反馈

## 📚 相关依赖

```python
# requirements.txt 新增
arxiv==1.4.2                 # arXiv API
scholarly==1.7.11            # Google Scholar (可选)
pdfminer.six==20231228       # PDF 解析
PyPDF2==3.0.1                # PDF 操作
requests==2.31.0             # HTTP 请求
beautifulsoup4==4.12.2        # HTML 解析
selenium==4.16.0             # 网页自动化 (知网)
fake-useragent==1.4.0        # User-Agent 伪装
python-dotenv==1.0.0         # 环境变量管理
```

这个设计提供了完整的论文自动采集解决方案，可以根据实际需求分阶段实现。