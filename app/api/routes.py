"""API 路由：论文生成、润色、扩写、知识库问答"""
import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException

from app.models import (
    AskKnowledgeRequest,
    AskKnowledgeResponse,
    GeneratePaperRequest,
    GeneratePaperResponse,
    ImprovePaperRequest,
    ImprovePaperResponse,
    ExpandPaperRequest,
    ExpandPaperResponse,
    GenerateLessonPlanRequest,
    GenerateLessonPlanResponse,
    GenerateTeachingCaseRequest,
    GenerateTeachingCaseResponse,
    ReduceWeightRequest,
    ReduceWeightResponse,
    TopicApplicationRequest,
    TopicApplicationResponse,
    MessageResponse,
)
from app.config import get_settings
from app.services.rag_service import ask_knowledge
from app.services.paper_service import (
    generate_paper,
    improve_paper,
    expand_paper,
    generate_lesson_plan,
    generate_teaching_case,
    reduce_weight,
    generate_topic_application,
)
from app.services.document_loader import load_and_chunk_file
from app.services.vector_store import add_documents_to_store

router = APIRouter(prefix="/api", tags=["幼儿园教师 AI 论文助手"])


@router.post("/ask_knowledge", response_model=AskKnowledgeResponse)
async def api_ask_knowledge(req: AskKnowledgeRequest):
    """知识库 RAG 问答"""
    try:
        answer, sources = ask_knowledge(req.question, top_k=req.top_k)
        return AskKnowledgeResponse(success=True, answer=answer, sources=sources)
    except Exception as e:
        return AskKnowledgeResponse(success=False, answer=f"查询失败: {str(e)}", sources=[])


@router.post("/generate_paper", response_model=GeneratePaperResponse)
async def api_generate_paper(req: GeneratePaperRequest):
    """论文生成"""
    try:
        content = generate_paper(
            title=req.title,
            outline=req.outline,
            direction=req.direction,
            words=req.words,
            use_rag=req.use_rag,
        )
        return GeneratePaperResponse(success=True, content=content)
    except Exception as e:
        return GeneratePaperResponse(success=False, content=f"生成失败: {str(e)}")


@router.post("/improve_paper", response_model=ImprovePaperResponse)
async def api_improve_paper(req: ImprovePaperRequest):
    """论文润色"""
    try:
        content = improve_paper(req.content, focus=req.focus)
        return ImprovePaperResponse(success=True, content=content)
    except Exception as e:
        return ImprovePaperResponse(success=False, content=f"润色失败: {str(e)}")


@router.post("/expand_paper", response_model=ExpandPaperResponse)
async def api_expand_paper(req: ExpandPaperRequest):
    """论文扩写"""
    try:
        content = expand_paper(
            content=req.content,
            target_words=req.target_words,
            target_section=req.target_section,
            use_rag=req.use_rag,
        )
        return ExpandPaperResponse(success=True, content=content)
    except Exception as e:
        return ExpandPaperResponse(success=False, content=f"扩写失败: {str(e)}")


@router.post("/generate_lesson_plan", response_model=GenerateLessonPlanResponse)
async def api_generate_lesson_plan(req: GenerateLessonPlanRequest):
    """教案生成"""
    try:
        content = generate_lesson_plan(
            topic=req.topic,
            grade=req.grade,
            goal=req.goal,
            subject=req.subject,
            duration=req.duration,
            use_rag=req.use_rag,
        )
        return GenerateLessonPlanResponse(success=True, content=content)
    except Exception as e:
        return GenerateLessonPlanResponse(success=False, content=f"生成失败: {str(e)}")


@router.post("/generate_teaching_case", response_model=GenerateTeachingCaseResponse)
async def api_generate_teaching_case(req: GenerateTeachingCaseRequest):
    """教学案例生成"""
    try:
        content = generate_teaching_case(
            topic=req.topic,
            age=req.age,
            goal=req.goal,
            scenario=req.scenario,
            use_rag=req.use_rag,
        )
        return GenerateTeachingCaseResponse(success=True, content=content)
    except Exception as e:
        return GenerateTeachingCaseResponse(success=False, content=f"生成失败: {str(e)}")


@router.post("/reduce_weight", response_model=ReduceWeightResponse)
async def api_reduce_weight(req: ReduceWeightRequest):
    """论文降重"""
    try:
        content = reduce_weight(req.content, focus=req.focus)
        return ReduceWeightResponse(success=True, content=content)
    except Exception as e:
        return ReduceWeightResponse(success=False, content=f"降重失败: {str(e)}")


@router.post("/topic_application", response_model=TopicApplicationResponse)
async def api_topic_application(req: TopicApplicationRequest):
    """课题申报书生成（评职称用）"""
    try:
        content = generate_topic_application(
            topic=req.topic,
            direction=req.direction,
            use_rag=req.use_rag,
        )
        return TopicApplicationResponse(success=True, content=content)
    except Exception as e:
        return TopicApplicationResponse(success=False, content=f"生成失败: {str(e)}")


@router.post("/upload_knowledge", response_model=MessageResponse)
async def api_upload_knowledge(files: list[UploadFile] = File(..., alias="files")):
    """上传多个 PDF/DOCX/DOC 到知识库并自动切片向量化"""
    allowed = {".pdf", ".docx", ".doc"}
    for f in files:
        suffix = Path(f.filename or "").suffix.lower()
        if suffix not in allowed:
            raise HTTPException(status_code=400, detail=f"不支持 {suffix}，仅支持 .pdf / .docx / .doc")
    if not files:
        raise HTTPException(status_code=400, detail="请至少选择一个文件")
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="单次最多上传 5 个文件，请分批上传以免超时")
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    total_chunks = 0
    processed = 0
    errors = []

    for file in files:
        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = upload_dir / safe_name
        try:
            content = await file.read()
            file_path.write_bytes(content)
            docs = load_and_chunk_file(str(file_path))
            for d in docs:
                d.metadata["source"] = file.filename or safe_name
            add_documents_to_store(docs)
            total_chunks += len(docs)
            processed += 1
        except Exception as e:
            if file_path.exists():
                file_path.unlink(missing_ok=True)
            errors.append(f"{file.filename}: {e}")

    if errors and processed == 0:
        raise HTTPException(status_code=500, detail="; ".join(errors))
    msg = f"已上传 {processed} 个文件，共 {total_chunks} 个片段"
    if errors:
        msg += "；失败: " + "; ".join(errors[:3])
    return MessageResponse(success=True, message=msg)
