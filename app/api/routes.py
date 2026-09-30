"""API 路由：论文生成、润色、扩写、知识库问答"""
import os
import shutil
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from app.models import (
    AskKnowledgeRequest,
    AskKnowledgeResponse,
    KnowledgeStatsRequest,
    KnowledgeStatsResponse,
    SearchKnowledgeRequest,
    SearchKnowledgeResponse,
    SearchResultItem,
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
    SearchPapersRequest,
    SearchPapersResponse,
    CollectPapersRequest,
    CollectPapersResponse,
    DownloadAndIngestRequest,
    DownloadAndIngestResponse,
    TopicQueryRequest,
    TopicQueryResponse,
    TopicFacetsResponse,
    TopicSuggestRequest,
    TopicSuggestResponse,
    GenerateOutlineRequest,
    GenerateOutlineResponse,
    ReviewPaperRequest,
    ReviewPaperResponse,
    ExtractTextResponse,
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
    generate_outline,
    review_paper,
)
from app.services.document_loader import load_and_chunk_file
from app.services.vector_store import add_documents_to_store
from app.services.paper_collector import search_papers, collect_papers
from app.services.topic_library import get_topics, get_facets, suggest_topics

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
    """论文生成（支持携带流程中选定的素材与补充素材）"""
    try:
        content = generate_paper(
            title=req.title,
            outline=req.outline,
            direction=req.direction,
            words=req.words,
            use_rag=req.use_rag,
            extra_context=req.extra_context,
            notes=req.notes,
        )
        return GeneratePaperResponse(success=True, content=content)
    except Exception as e:
        return GeneratePaperResponse(success=False, content=f"生成失败: {str(e)}")


@router.post("/generate_outline", response_model=GenerateOutlineResponse)
async def api_generate_outline(req: GenerateOutlineRequest):
    """生成论文提纲（写论文流程第③步）"""
    try:
        outline = generate_outline(
            title=req.title,
            direction=req.direction,
            use_rag=req.use_rag,
            extra_context=req.extra_context,
        )
        return GenerateOutlineResponse(success=True, outline=outline)
    except Exception as e:
        return GenerateOutlineResponse(success=False, error=f"生成失败: {str(e)}")


@router.post("/review_paper", response_model=ReviewPaperResponse)
async def api_review_paper(req: ReviewPaperRequest):
    """论文评审报告（改论文流程的评审操作）"""
    try:
        report = review_paper(req.content)
        return ReviewPaperResponse(success=True, report=report)
    except Exception as e:
        return ReviewPaperResponse(success=False, error=f"评审失败: {str(e)}")


@router.post("/extract_text", response_model=ExtractTextResponse)
async def api_extract_text(file: UploadFile = File(...)):
    """提取上传文件的文本（改论文流程的文件输入）"""
    suffix = Path(file.filename or "").suffix.lower()
    try:
        if suffix in {".txt", ".md", ".tex"}:
            text = (await file.read()).decode("utf-8", errors="replace")
        elif suffix in {".pdf", ".docx", ".doc"}:
            temp = Path(get_settings().upload_dir) / "temp" / (uuid.uuid4().hex + suffix)
            temp.parent.mkdir(parents=True, exist_ok=True)
            try:
                temp.write_bytes(await file.read())
                from app.services.document_loader import load_document
                docs = load_document(str(temp))
                text = "\n\n".join(d.page_content for d in docs if d.page_content.strip())
            finally:
                temp.unlink(missing_ok=True)
        else:
            return ExtractTextResponse(success=False, error=f"不支持的格式: {suffix}")
        text = text.replace("\x00", "").strip()
        if not text:
            return ExtractTextResponse(success=False, error="未能提取到文本（扫描版 PDF 或空文件）")
        return ExtractTextResponse(success=True, text=text[:100000], filename=file.filename or "", chars=len(text))
    except Exception as e:
        return ExtractTextResponse(success=False, error=f"提取失败: {str(e)}")


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


@router.get("/knowledge/stats", response_model=KnowledgeStatsResponse)
async def api_knowledge_stats():
    """获取知识库统计信息：文档数量、数据库大小、向量片段数"""
    try:
        from app.services.vector_store import get_vector_store_stats, create_vector_store
        from app.config import get_settings
        import os

        settings = get_settings()

        # 获取向量库统计信息
        stats = {
            "document_count": 0,
            "db_size_bytes": 0,
            "vector_count": 0
        }

        try:
            # 尝试获取向量库统计
            vector_stats = get_vector_store_stats()
            stats.update(vector_stats)
        except Exception as e:
            print(f"获取向量库统计失败: {e}")

        # 计算数据库文件大小
        try:
            db_path = getattr(settings, 'database_url', '').split('//')[-1].split('?')[0]
            if os.path.exists(db_path):
                stats["db_size_bytes"] = os.path.getsize(db_path)
        except Exception as e:
            print(f"获取数据库大小失败: {e}")

        return KnowledgeStatsResponse(success=True, stats=stats)
    except Exception as e:
        return KnowledgeStatsResponse(success=True, stats={
            "document_count": 0,
            "db_size_bytes": 0,
            "vector_count": 0
        })


@router.post("/knowledge/search", response_model=SearchKnowledgeResponse)
async def api_search_knowledge(req: SearchKnowledgeRequest):
    """知识库检索验证：返回最相关的片段和相似度"""
    try:
        from app.services.vector_store import create_vector_store

        # 创建向量存储实例
        vector_store = create_vector_store(use_existing=True)

        # 执行相似度搜索
        from langchain_community.vectorstores import PGVector
        results = vector_store.similarity_search_with_score(
            query=req.query,
            k=req.top_k
        )

        # 格式化结果
        search_results = []
        for doc, score in results:
            search_results.append(SearchResultItem(
                content=doc.page_content,
                score=float(1.0 - score),  # 转换距离为相似度
                metadata=doc.metadata
            ))

        return SearchKnowledgeResponse(
            success=True,
            results=search_results,
            message=f"找到 {len(search_results)} 个相关片段"
        )
    except Exception as e:
        return SearchKnowledgeResponse(
            success=False,
            results=[],
            message=f"检索失败: {str(e)}"
        )


@router.post("/papers/download_and_ingest", response_model=DownloadAndIngestResponse)
async def api_download_and_ingest(req: DownloadAndIngestRequest):
    """下载单篇论文并入库"""
    try:
        from app.services.paper_collector.paper_collector import PaperDownloader, PaperMetadata
        from app.services.document_loader import load_and_chunk_file
        from app.services.vector_store import add_documents_to_store
        from pathlib import Path
        import uuid

        # 创建PaperMetadata对象
        metadata = PaperMetadata(
            title=req.title,
            authors=req.authors,
            year=req.year,
            abstract=req.abstract,
            doi=req.doi,
            download_url=req.download_url,
            source=req.source,
            pdf_available=req.pdf_available,
        )

        # 下载PDF
        downloader = PaperDownloader()
        pdf_path = downloader.download_pdf(metadata)

        if not pdf_path:
            return DownloadAndIngestResponse(
                success=False,
                message=f"PDF下载失败: {metadata.title}"
            )

        # 向量化入库
        docs = load_and_chunk_file(str(pdf_path))
        for doc in docs:
            doc.metadata.update({
                "source": metadata.source,
                "title": metadata.title,
                "authors": metadata.authors,
                "year": metadata.year,
                "doi": metadata.doi,
                "collected_at": f"{datetime.utcnow().isoformat()}Z",
            })

        add_documents_to_store(docs)

        return DownloadAndIngestResponse(
            success=True,
            message=f"成功下载并入库: {metadata.title}",
            ingested_chunks=len(docs)
        )

    except Exception as e:
        return DownloadAndIngestResponse(
            success=False,
            message=f"处理失败: {str(e)}"
        )


@router.post("/upload_knowledge", response_model=MessageResponse)
async def api_upload_knowledge(files: list[UploadFile] = File(..., alias="files")):
    """上传多个 PDF/DOCX/DOC 到知识库并自动切片向量化（按内容去重）"""
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

    # 已有文件的内容指纹，避免同一文件重复入库污染检索结果
    import hashlib
    existing_hashes = {
        hashlib.md5(p.read_bytes()).hexdigest()
        for p in upload_dir.glob("*")
        if p.is_file() and p.suffix.lower() in allowed
    }

    total_chunks = 0
    processed = 0
    errors = []
    skipped = []

    for file in files:
        content = await file.read()
        digest = hashlib.md5(content).hexdigest()
        if digest in existing_hashes:
            skipped.append(file.filename)
            continue
        safe_name = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = upload_dir / safe_name
        try:
            file_path.write_bytes(content)
            existing_hashes.add(digest)
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

    if errors and processed == 0 and not skipped:
        raise HTTPException(status_code=500, detail="; ".join(errors))
    msg = f"已上传 {processed} 个文件，共 {total_chunks} 个片段"
    if skipped:
        msg += f"；跳过重复文件: {'、'.join(skipped[:3])}"
    if errors:
        msg += "；失败: " + "; ".join(errors[:3])
    return MessageResponse(success=True, message=msg)


@router.post("/papers/search", response_model=SearchPapersResponse)
async def api_search_papers(req: SearchPapersRequest):
    """搜索学术论文（仅搜索，不下载数据库）"""
    try:
        results = search_papers(
            query=req.query,
            sources=req.sources,
            max_results=req.max_results,
            year_range=req.year_range,
        )

        # 计算总论文数
        total = sum(len(papers) for papers in results.values())

        return SearchPapersResponse(
            success=True,
            papers=results,
            total=total,
        )
    except Exception as e:
        return SearchPapersResponse(
            success=False,
            papers={},
            total=0,
        )


@router.post("/papers/collect", response_model=CollectPapersResponse)
async def api_collect_papers(req: CollectPapersRequest):
    """采集论文：搜索、下载PDF、自动入库RAG"""
    try:
        result = collect_papers(
            query=req.query,
            sources=req.sources,
            max_papers=req.max_papers,
            year_range=req.year_range,
            auto_ingest=req.auto_ingest,
        )

        return CollectPapersResponse(**result)
    except Exception as e:
        return CollectPapersResponse(
            success=False,
            message=f"采集失败: {str(e)}",
            collected=0,
            ingested=0,
            failed=0,
        )


@router.post("/paper/generate_docx")
async def api_generate_paper_docx(req: GeneratePaperRequest):
    """生成图文排版论文 Word（事实底座→分节撰写→图表→评选规范排版），约需 3-5 分钟"""
    try:
        from app.services.paper_docx import generate_paper_docx

        result = generate_paper_docx(
            title=req.title,
            direction=req.direction,
            use_rag=req.use_rag,
        )
        return {
            "success": True,
            "filename": result["filename"],
            "words": result["words"],
            "stats": result["stats"],
            "download_url": f"/api/download/{result['filename']}",
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("图文论文生成失败")
        return {"success": False, "error": f"生成失败: {str(e)}"}


@router.post("/paper/rewrite")
async def api_rewrite_paper(
    file: UploadFile = File(...),
    intensity: str = Form("medium"),
    generate_diff: bool = Form(False)
):
    """论文降重（段落级改写，保留原文件，输出 {原名}_降重_{力度} 文件）"""
    try:
        from app.services.paper_rewrite import rewrite_paper, INTENSITY_RULES

        if intensity not in INTENSITY_RULES:
            return {"success": False, "error": f"不支持的力度: {intensity}，可选 light/medium/heavy"}

        settings = get_settings()
        temp_dir = Path(settings.upload_dir) / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / (uuid.uuid4().hex + "_" + (file.filename or "paper"))
        try:
            temp_file.write_bytes(await file.read())
            result = rewrite_paper(str(temp_file), intensity=intensity, generate_diff=generate_diff)
        finally:
            temp_file.unlink(missing_ok=True)

        if result["status"] != "success":
            return {"success": False, "error": result.get("error", "降重失败")}

        # 把输出文件挪到 temp 目录统一管理，供 /api/download 下载
        output_path = Path(result["output_file"])
        final_path = temp_dir / output_path.name
        if output_path != final_path:
            shutil.copy(output_path, final_path)
        diff_final = None
        if result.get("diff_file"):
            diff_path = Path(result["diff_file"])
            diff_final = temp_dir / diff_path.name
            if diff_path != diff_final:
                shutil.copy(diff_path, diff_final)

        return {
            "success": True,
            "output_file": str(final_path),
            "output_filename": final_path.name,
            "original_filename": file.filename,
            "intensity": result["intensity"],
            "stats": result.get("stats"),
            "diff_file": diff_final.name if diff_final else None,
        }

    except Exception as e:
        return {"success": False, "error": f"降重处理失败: {str(e)}"}


@router.post("/topics/search", response_model=TopicQueryResponse)
async def api_topics_search(req: TopicQueryRequest):
    """选题库检索：按关键词/年份/奖级/城市筛选获奖论文选题"""
    result = get_topics(
        keyword=req.keyword,
        year=req.year,
        award=req.award,
        city=req.city,
        limit=req.limit,
        offset=req.offset,
    )
    return TopicQueryResponse(success=True, total=result["total"], items=result["items"])


@router.get("/topics/facets", response_model=TopicFacetsResponse)
async def api_topics_facets():
    """选题库筛选项（年份/奖级/城市）与总量"""
    facets = get_facets()
    return TopicFacetsResponse(success=True, **facets)


@router.post("/topics/suggest", response_model=TopicSuggestResponse)
async def api_topics_suggest(req: TopicSuggestRequest):
    """AI 选题建议：基于浙江获奖趋势与用户方向生成选题推荐"""
    try:
        result = suggest_topics(
            direction=req.direction,
            background=req.background,
            age_group=req.age_group,
        )
        return TopicSuggestResponse(**result)
    except Exception as e:
        return TopicSuggestResponse(success=False, error=f"生成建议失败: {str(e)}")


@router.get("/download/{filename}")
async def api_download_file(filename: str):
    """文件下载接口"""
    try:
        from fastapi.responses import Response

        # 安全检查：防止路径遍历攻击
        import urllib.parse
        safe_filename = urllib.parse.unquote(filename).replace("..", "").replace("/", "").replace("\\", "")

        # 先尝试temp目录
        file_path = Path("knowledge_uploads/temp") / safe_filename
        if not file_path.exists():
            # 尝试其他目录
            file_path = Path("knowledge_uploads/collected_papers") / safe_filename
        if not file_path.exists():
            # 尝试项目根目录
            file_path = Path(safe_filename)

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {safe_filename}")

        # 读取文件内容
        with open(file_path, 'rb') as f:
            content = f.read()

        # 使用UTF-8编码的文件名
        encoded_filename = urllib.parse.quote(safe_filename)

        # 返回文件内容
        return Response(
            content=content,
            media_type='application/octet-stream',
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")
