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


class AskKnowledgeResponse(BaseModel):
    success: bool = True
    answer: str = Field(..., description="基于知识库的回答")
    sources: Optional[list[str]] = Field(default_factory=list, description="引用来源片段")


# ---------- 论文生成 ----------
class GeneratePaperRequest(BaseModel):
    title: str = Field(..., description="论文标题或主题")
    outline: Optional[str] = Field(None, description="可选大纲")
    direction: Optional[str] = Field(None, description="研究方向，如：游戏化教学、家园共育")
    words: Optional[str] = Field(None, description="字数要求，如：3000字、5000字")
    use_rag: bool = Field(True, description="是否结合知识库")


class GeneratePaperResponse(BaseModel):
    success: bool = True
    content: str = Field(..., description="生成的论文内容")


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
