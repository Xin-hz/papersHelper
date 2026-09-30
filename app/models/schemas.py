"""API 请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Optional


# ---------- 通用 ----------
class MessageResponse(BaseModel):
    success: bool = True
    message: str = ""


# ---------- 知识库问答 ----------
class AskKnowledgeRequest(BaseModel):
    question: str = Field(..., description="用户问题")
    top_k: Optional[int] = Field(None, description="检索条数，默认使用配置")


class SourceItem(BaseModel):
    title: str = Field("", description="文档标题或文件名")
    source: str = Field("", description="来源标识")
    authors: list[str] = Field(default_factory=list, description="作者")
    year: Optional[int] = Field(None, description="发表年份")
    snippet: str = Field("", description="命中的原文摘录")


class AskKnowledgeResponse(BaseModel):
    success: bool = True
    answer: str = Field(..., description="基于知识库的回答")
    sources: Optional[list[SourceItem]] = Field(default_factory=list, description="引用来源（含文档信息）")


# ---------- 知识库统计 ----------
class KnowledgeStatsRequest(BaseModel):
    pass  # 空请求，只需GET


class KnowledgeStatsResponse(BaseModel):
    success: bool = True
    stats: dict = Field(default_factory=dict, description="统计信息，包含document_count, db_size_bytes, vector_count")


# ---------- 知识库检索验证 ----------
class SearchKnowledgeRequest(BaseModel):
    query: str = Field(..., description="检索关键词")
    top_k: int = Field(5, description="返回结果数")


class SearchResultItem(BaseModel):
    content: str = Field(..., description="检索到的内容片段")
    score: float = Field(..., description="相似度得分")
    metadata: Optional[dict] = Field(default_factory=dict, description="元数据信息")


class SearchKnowledgeResponse(BaseModel):
    success: bool = True
    results: list[SearchResultItem] = Field(default_factory=list, description="检索结果列表")
    message: Optional[str] = Field(None, description="附加信息")


# ---------- 论文生成 ----------
class GeneratePaperRequest(BaseModel):
    title: str = Field(..., description="论文标题或主题")
    outline: Optional[str] = Field(None, description="可选大纲")
    direction: Optional[str] = Field(None, description="研究方向，如：游戏化教学、家园共育")
    words: Optional[str] = Field(None, description="字数要求，如：3000字、5000字")
    use_rag: bool = Field(True, description="是否结合知识库")
    extra_context: Optional[str] = Field(None, description="流程第②步选定的知识库素材（优先于自动检索）")
    notes: Optional[str] = Field(None, description="作者补充的真实事实/素材（班级情况、真实数据等）")


class GeneratePaperResponse(BaseModel):
    success: bool = True
    content: str = Field(..., description="生成的论文内容")


# ---------- 提纲 / 评审 / 文本提取 ----------
class GenerateOutlineRequest(BaseModel):
    title: str = Field(..., description="论文标题或主题")
    direction: Optional[str] = Field(None, description="研究方向")
    use_rag: bool = Field(True, description="是否结合知识库")
    extra_context: Optional[str] = Field(None, description="选定的知识库素材")


class GenerateOutlineResponse(BaseModel):
    success: bool = True
    outline: str = ""
    error: Optional[str] = None


class ReviewPaperRequest(BaseModel):
    content: str = Field(..., description="待评审的论文全文")


class ReviewPaperResponse(BaseModel):
    success: bool = True
    report: str = ""
    error: Optional[str] = None


class ExtractTextResponse(BaseModel):
    success: bool = True
    text: str = ""
    filename: str = ""
    chars: int = 0
    error: Optional[str] = None


# ---------- 论文润色 ----------
class ImprovePaperRequest(BaseModel):
    content: str = Field(..., description="待润色的论文内容")
    focus: Optional[str] = Field(None, description="润色侧重点，如：学术性、语言流畅")


class ImprovePaperResponse(BaseModel):
    success: bool = True
    content: str = Field(..., description="润色后的内容")


# ---------- 论文扩写 ----------
class ExpandPaperRequest(BaseModel):
    content: str = Field(..., description="待扩写的段落或全文")
    target_words: Optional[str] = Field(None, description="目标字数，如：3000字、5000字")
    target_section: Optional[str] = Field(None, description="指定扩写部分（可选），用于检索知识库")
    use_rag: bool = Field(True, description="是否结合知识库")


class ExpandPaperResponse(BaseModel):
    success: bool = True
    content: str = Field(..., description="扩写后的内容")


# ---------- 教案生成 ----------
class GenerateLessonPlanRequest(BaseModel):
    topic: str = Field(..., description="课程名称 / 教学主题")
    grade: Optional[str] = Field(None, description="适合年龄，如：大班、中班、小班")
    goal: Optional[str] = Field(None, description="课程目标")
    subject: Optional[str] = Field(None, description="领域（可选），如：语言、艺术、科学")
    duration: Optional[str] = Field(None, description="课时（可选），如：一课时、20分钟")
    use_rag: bool = Field(True, description="是否结合知识库")


class GenerateLessonPlanResponse(BaseModel):
    success: bool = True
    content: str = Field(..., description="生成的教案内容")


# ---------- 教学案例生成 ----------
class GenerateTeachingCaseRequest(BaseModel):
    topic: str = Field(..., description="活动名称 / 案例主题")
    age: Optional[str] = Field(None, description="年龄段，如：大班、中班、小班")
    goal: Optional[str] = Field(None, description="活动目标")
    scenario: Optional[str] = Field(None, description="场景说明（可选），如：区域活动、集体教学")
    use_rag: bool = Field(True, description="是否结合知识库")


class GenerateTeachingCaseResponse(BaseModel):
    success: bool = True
    content: str = Field(..., description="生成的教学案例内容")


# ---------- 论文降重 ----------
class ReduceWeightRequest(BaseModel):
    content: str = Field(..., description="待降重的论文内容")
    focus: Optional[str] = Field(None, description="降重侧重点，如：同义替换、句式改写")


class ReduceWeightResponse(BaseModel):
    success: bool = True
    content: str = Field(..., description="降重后的内容")


# ---------- 课题申报（评职称用） ----------
class TopicApplicationRequest(BaseModel):
    topic: str = Field(..., description="课题名称")
    direction: Optional[str] = Field(None, description="研究方向，如：游戏化教学、家园共育")
    use_rag: bool = Field(True, description="是否结合知识库")


class TopicApplicationResponse(BaseModel):
    success: bool = True
    content: str = Field(..., description="生成的课题申报书内容")


# ---------- 选题库 ----------
class TopicQueryRequest(BaseModel):
    keyword: Optional[str] = Field(None, description="关键词，匹配标题/单位/作者")
    year: Optional[str] = Field(None, description="年份，如 2024")
    award: Optional[str] = Field(None, description="奖级：一等奖/二等奖/三等奖")
    city: Optional[str] = Field(None, description="地市，如 杭州/宁波")
    limit: int = Field(50, ge=1, le=200, description="每页条数")
    offset: int = Field(0, ge=0, description="偏移量")


class TopicItem(BaseModel):
    year: str = ""
    award: str = ""
    city: str = ""
    unit: str = ""
    authors: str = ""
    title: str = ""


class TopicQueryResponse(BaseModel):
    success: bool = True
    total: int = 0
    items: list[TopicItem] = Field(default_factory=list)


class TopicFacetsResponse(BaseModel):
    success: bool = True
    years: list[str] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    total: int = 0


class TopicSuggestRequest(BaseModel):
    direction: str = Field(..., description="研究方向或兴趣，如：户外自主游戏、师幼互动")
    background: Optional[str] = Field(None, description="园所/学段情况，可选")
    age_group: Optional[str] = Field(None, description="关注的年龄段，如大班")


class TopicRefItem(BaseModel):
    title: str = ""
    city: str = ""
    award: str = ""
    year: str = ""


class TopicSuggestResponse(BaseModel):
    success: bool = True
    suggestion: str = ""
    referenced: list[TopicRefItem] = Field(default_factory=list)
    error: Optional[str] = None


# ---------- 论文采集 ----------
class SearchPapersRequest(BaseModel):
    query: str = Field(..., description="搜索关键词")
    sources: list[str] = Field(default=["arxiv"], description="数据源，如：arxiv, cnki, wanfang")
    max_results: int = Field(20, description="最大结果数")
    year_range: Optional[str] = Field(None, description="年份范围，如：2020-2024")


class PaperInfo(BaseModel):
    title: str
    authors: list[str]
    year: Optional[int] = None
    abstract: str = ""
    doi: str = ""
    download_url: str = ""
    source: str = ""
    pdf_available: bool = False


class SearchPapersResponse(BaseModel):
    success: bool = True
    papers: dict[str, list[PaperInfo]] = Field(default_factory=dict, description="按数据源分组的论文列表")
    total: int = Field(0, description="总论文数")


class CollectPapersRequest(BaseModel):
    query: str = Field(..., description="搜索关键词")
    sources: list[str] = Field(default=["arxiv"], description="数据源")
    max_papers: int = Field(10, description="最大采集论文数")
    year_range: Optional[str] = Field(None, description="年份范围")
    auto_ingest: bool = Field(True, description="是否自动入库RAG")


class CollectionStats(BaseModel):
    ingested: int = 0
    failed: int = 0
    total_chunks: int = 0


class CollectPapersResponse(BaseModel):
    success: bool = True
    message: str = ""
    collected: int = 0
    ingested: int = 0
    failed: int = 0
    stats: CollectionStats = Field(default_factory=CollectionStats)


# ---------- 下载并入库 ----------
class DownloadAndIngestRequest(BaseModel):
    title: str = Field(..., description="论文标题")
    authors: list[str] = Field(default_factory=list, description="作者列表")
    year: Optional[int] = Field(None, description="发表年份")
    abstract: str = ""
    doi: str = ""
    download_url: str = Field(..., description="PDF下载链接")
    source: str = "openalex"
    pdf_available: bool = True


class DownloadAndIngestResponse(BaseModel):
    success: bool = True
    message: str = ""
    ingested_chunks: int = 0
