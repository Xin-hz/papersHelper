"""论文生成、润色、扩写业务逻辑"""
import re
from typing import List, Optional

from langchain_core.messages import SystemMessage, HumanMessage

from app.prompts import SYSTEM_PROMPT
from app.services.llm_service import get_chat_llm
from app.services.rag_service import get_context_for_writing, retrieve_for_writing


def _invoke_with_system(llm, user_prompt: str) -> str:
    """使用统一人格系统 Prompt 调用 LLM"""
    return llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)]).content


# ---------- 论文多阶段生成：大纲 → 逐章生成 → 摘要/关键词 → 参考文献 ----------

OUTLINE_PROMPT = """为论文《{title}》拟定章节大纲。

研究方向：{direction}
总字数：约 {words} 字

要求：
1. 输出 4-6 个正文章节（不含摘要、关键词、参考文献）
2. 每行一个章节标题，格式如「一、研究背景」
3. 章节顺序符合幼儿园教育研究论文的逻辑

只输出章节列表，不要其他内容。"""


SECTION_PROMPT = """撰写论文《{title}》中的「{section}」章节（第 {index}/{total} 章）。

本章节字数要求：约 {budget} 字。
研究方向：{direction}

论文完整大纲（你只写「{section}」这一章，其他章节由并行任务撰写）：
{outline_all}

参考知识库片段（真实文献资料，观点与案例优先从这里取材）：
{context}

写作要求：
1. 观点具体、论证充分，不写空话套话
2. 涉及教学实践时给出具体案例：幼儿年龄段、活动名称、投放材料、师幼互动过程
3. 引用知识库观点时自然融入行文，不要原文罗列片段
4. 若非首章，开头自然承接上一章「{prev_section}」的话题，但不要重复其内容
5. 若非末章，结尾可为下一章「{next_section}」留出引子，但不要提前展开
6. 章节标题行用中文编号，如「一、{section}」，不要使用 Markdown 的 # 号标题

直接输出本章节正文（以章节标题开头），不要任何额外解释。"""


ABSTRACT_PROMPT = """基于以下论文正文，撰写摘要与关键词。

要求：
1. 摘要 200 字左右，概括研究问题、实践方法、核心观点与结论
2. 关键词 3-5 个，用分号分隔

输出格式：
摘要：……
关键词：……

论文正文：
{body}"""


def _parse_total_words(words: Optional[str]) -> int:
    """从「3000字」这类描述中解析总字数，默认 3000"""
    m = re.search(r"\d{3,6}", words or "")
    return int(m.group()) if m else 3000


def _strip_numbering(line: str) -> str:
    """去掉章节标题前的「一、」「1.」「（一）」等编号"""
    return re.sub(r"^\s*[（(]?[0-9一二三四五六七八九十]+[）)、.．]\s*", "", line).strip()


def _parse_outline_sections(outline: str) -> List[str]:
    """把用户大纲解析为章节列表（兼容换行/分号/单行编号分隔）"""
    parts = re.split(r"[\n；;]+", outline)
    if len(parts) == 1:
        # 单行大纲：按「二、」这类下一个编号出现的位置切分
        parts = re.split(r"\s*(?=[（(]?[一二三四五六七八九十\d]+[、.．)])", outline)
    sections = []
    for p in parts:
        name = _strip_numbering(p)
        if not name:
            continue
        if any(k in name for k in ("摘要", "关键词", "参考文献", "致谢")):
            continue
        sections.append(name)
    return sections


def _doc_ref_name(doc) -> str:
    """从检索片段元数据取文献显示名"""
    md = doc.metadata or {}
    name = md.get("title") or md.get("source") or ""
    if not name or str(name).lower() == "none":
        return ""
    year = md.get("year")
    return f"{name}（{year}）" if year else str(name)


def _generate_outline(llm, title: str, direction: Optional[str], total_words: int) -> List[str]:
    prompt = OUTLINE_PROMPT.format(
        title=title,
        direction=direction or "不限定",
        words=total_words,
    )
    raw = _invoke_with_system(llm, prompt)
    return _parse_outline_sections(raw)


def generate_paper(
    title: str,
    outline: Optional[str] = None,
    direction: Optional[str] = None,
    words: Optional[str] = None,
    use_rag: bool = True,
    extra_context: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """生成论文正文（多阶段：大纲 → 逐章生成 → 摘要/关键词 → 参考文献）。

    extra_context：用户在流程第②步选定的知识库素材（提供时优先于自动检索）
    notes：用户补充的真实事实/素材（班级情况、真实数据等，注入各章生成）
    """
    llm = get_chat_llm(temperature=0.6)  # 配置 PAPER_MODEL 时自动使用更强模型

    total_words = _parse_total_words(words)

    # 阶段一：确定大纲
    sections = _parse_outline_sections(outline) if outline and outline.strip() else []
    if not sections:
        sections = _generate_outline(llm, title, direction, total_words)
    if not sections:
        sections = ["研究背景与问题提出", "理论基础", "实践案例与策略", "实践效果与反思"]
    if len(sections) > 6:
        sections = sections[:6]

    budget = max(400, total_words // len(sections))

    # 阶段二：各章并行生成（选定素材优先；否则每章单独检索知识库片段）
    outline_all = "\n".join(f"{i}. {s}" for i, s in enumerate(sections, 1))
    ref_names: List[str] = []
    section_prompts = []
    for idx, sec in enumerate(sections):
        if extra_context and extra_context.strip():
            context = extra_context
        else:
            docs = retrieve_for_writing(f"{title} {sec}", top_k=4) if use_rag else []
            context = "\n\n---\n\n".join(d.page_content for d in docs) if docs else "（未检索到相关资料）"
            for d in docs:
                name = _doc_ref_name(d)
                if name and name not in ref_names:
                    ref_names.append(name)
        if notes and notes.strip():
            context += f"\n\n作者补充的真实素材（优先采用，与上述资料冲突时以此为准）：\n{notes}"
        section_prompts.append(
            SECTION_PROMPT.format(
                title=title,
                section=sec,
                index=idx + 1,
                total=len(sections),
                budget=budget,
                direction=direction or "不限定",
                outline_all=outline_all,
                context=context,
                prev_section=sections[idx - 1] if idx > 0 else "（本章为开篇）",
                next_section=sections[idx + 1] if idx < len(sections) - 1 else "（本章为末章）",
            )
        )
    results = llm.batch(section_prompts, config={"max_concurrency": 5})
    cn_nums = "一二三四五六七八九十"
    written = []
    for idx, r in enumerate(results):
        text = str(r.content or "").strip()
        # 统一章节标题：去掉模型可能加的 Markdown # 前缀，规范为「一、章节名」
        lines = text.split("\n")
        first = lines[0].strip() if lines else ""
        first = re.sub(r"^#{1,6}\s*", "", first)
        body_lines = lines[1:] if len(lines) > 1 else []
        header = f"{cn_nums[idx]}、{_strip_numbering(first) or sections[idx]}"
        written.append("\n".join([header] + body_lines).strip())
    body = "\n\n".join(written)

    # 阶段三：基于全文生成摘要与关键词
    abstract = _invoke_with_system(
        llm, ABSTRACT_PROMPT.format(body=body[:6000])
    ).strip()

    # 阶段四：参考文献只列真实检索到的知识库文献，避免编造
    if ref_names:
        refs = "\n".join(f"[{i}] {name}" for i, name in enumerate(ref_names, 1))
    else:
        refs = "（本次生成未检索到知识库文献，请按实际引用补充）"

    return f"{title}\n\n{abstract}\n\n{body}\n\n参考文献\n{refs}"


OUTLINE_GEN_PROMPT = """为论文《{title}》拟定写作提纲。

研究方向：{direction}
预计篇幅：约 {words} 字

参考知识库片段（把握已有实践基础与提法）：
{context}

要求：
1. 输出 4-6 个正文章节，每行一章，格式为「一、章节标题」（中文编号，不写摘要/关键词/参考文献）
2. 章节顺序符合幼儿园实践研究论文逻辑（问题—策略—成效—反思类）
3. 章节标题具体、切口小，不写空泛的大标题

只输出提纲本身，不要其他解释。"""


def generate_outline(
    title: str,
    direction: Optional[str] = None,
    use_rag: bool = True,
    extra_context: Optional[str] = None,
) -> str:
    """生成论文提纲（流程第③步，供用户编辑确认后再进入正式撰写）"""
    if extra_context and extra_context.strip():
        context = extra_context
    elif use_rag:
        context = get_context_for_writing(title, top_k=6)
    else:
        context = "（无）"
    llm = get_chat_llm(temperature=0.6)
    raw = _invoke_with_system(llm, OUTLINE_GEN_PROMPT.format(
        title=title, direction=direction or "不限定", words="3000-4000", context=context or "（无）",
    ))
    sections = _parse_outline_sections(raw)
    cn = "一二三四五六"
    return "\n".join(f"{cn[i]}、{s}" for i, s in enumerate(sections[:6]))


REVIEW_PROMPT = """你是浙江省幼儿园教育教学论文评选的资深评委，熟悉其评选导向（观点明晰、逻辑严谨、文从字顺、正文一般不超过 4000 字）。
请对下述论文进行全面评审，输出评审报告。

按以下结构输出（用 Markdown 标题，不要改动其他格式）：

## 总体评价
2-3 句话概括稿件整体水平、最大亮点与最大短板。

## 分项评审
逐项打分（每项 10 分制，附 1-2 句给分理由）：
1. **选题价值**：切口是否小而具体、有无实践基础与新意
2. **结构逻辑**：章节安排是否合理、论证是否成环、前后是否呼应
3. **论据数据**：案例与数据是否具体充分、口径前后一致
4. **语言表达**：是否规范流畅、有无空话套话与口语化
5. **规范格式**：标题/摘要/关键词/参考文献是否规范，篇幅是否适中

## 主要问题
按重要性排序列 3-6 条，每条具体指出位置或表现。

## 修改建议
针对上述问题逐条给出可操作的修改建议。

## 综合结论
总分（50 分制）；一句话判断当前水平（如：需较大修改 / 接近区县级获奖水平 / 有冲击市级获奖水平的潜力）。

论文全文：
{content}"""


def review_paper(content: str) -> str:
    """生成论文评审报告（改论文流程的评审操作）"""
    llm = get_chat_llm(temperature=0.3)
    return _invoke_with_system(llm, REVIEW_PROMPT.format(content=content[:8000]))


IMPROVE_PROMPT = """请对以下论文内容进行学术化润色。

润色侧重点（若有）：{focus}

要求：
1. 提升论文表达质量
2. 保持原意
3. 优化逻辑结构
4. 避免重复表达

论文内容：
{text}

请直接输出润色后的完整内容，不要额外解释。"""


EXPAND_PROMPT = """请扩展以下论文内容。

目标字数：
{target_words}

要求：
1. 增加理论分析
2. 增加案例说明
3. 保持论文风格
4. 保持逻辑连贯

参考知识库（可引用）：
{context}

原文：
{text}

请直接输出扩写后的完整内容，不要额外解释。"""


LESSON_PLAN_PROMPT = """请设计一个幼儿园教学活动教案。

课程名称：
{course}

适合年龄：
{age}

课程目标：
{goal}

参考知识库（可选用）：
{context}

输出：
一、活动目标
二、活动准备
三、活动过程
四、师幼互动方式
五、延伸活动

要求：
1. 内容适合幼儿园课堂
2. 活动步骤清晰
3. 能激发幼儿兴趣"""


TEACHING_CASE_PROMPT = """请生成一个幼儿园教学案例。

活动名称：
{title}

年龄段：
{age}

活动目标：
{goal}

参考知识库（可选用）：
{context}

请输出以下内容：
1. 活动背景
2. 活动目标
3. 活动准备
4. 活动过程
5. 教师引导方式
6. 幼儿表现
7. 教学反思

要求：
案例真实可执行，符合幼儿园教学场景。"""


REDUCE_WEIGHT_PROMPT = """请对以下论文内容进行降重改写，在保持原意、学术规范的前提下，通过同义替换、句式调整、表述转换等方式降低与原文的重复度。

降重侧重点（若有）：{focus}

待降重内容：
{content}

要求：不改变核心观点与逻辑，不删减关键信息，仅做表述上的改写。直接输出降重后的完整内容，不要额外解释。"""


TOPIC_APPLICATION_PROMPT = """请撰写一份幼儿园教育课题申报书。

课题名称：
{topic}

研究方向：
{direction}

参考知识库（可选用）：
{context}

输出内容：
一、研究背景
二、研究意义
三、研究目标
四、研究内容
五、研究方法
六、实施计划
七、预期成果

要求：
1. 符合教育科研课题申报格式
2. 内容具有可实施性
3. 语言规范严谨"""


def improve_paper(content: str, focus: Optional[str] = None) -> str:
    """润色论文"""
    llm = get_chat_llm(temperature=0.4)
    prompt = IMPROVE_PROMPT.format(
        focus=focus or "整体",
        text=content,
    )
    return _invoke_with_system(llm, prompt)


def expand_paper(
    content: str,
    target_words: Optional[str] = None,
    target_section: Optional[str] = None,
    use_rag: bool = True,
) -> str:
    """扩写论文"""
    context = ""
    if use_rag:
        query = target_section or content[:300]
        context = get_context_for_writing(query, top_k=6)
    llm = get_chat_llm(temperature=0.5)
    prompt = EXPAND_PROMPT.format(
        target_words=target_words or "适当扩展，不限定字数",
        context=context or "（暂无知识库内容）",
        text=content,
    )
    return _invoke_with_system(llm, prompt)


def generate_lesson_plan(
    topic: str,
    grade: Optional[str] = None,
    goal: Optional[str] = None,
    subject: Optional[str] = None,
    duration: Optional[str] = None,
    use_rag: bool = True,
) -> str:
    """生成教案"""
    context = ""
    if use_rag:
        context = get_context_for_writing(topic, top_k=6)
    llm = get_chat_llm(temperature=0.5)
    prompt = LESSON_PLAN_PROMPT.format(
        course=topic,
        age=grade or "不限",
        goal=goal or "根据课程名称设定",
        context=context or "（暂无知识库内容）",
    )
    return _invoke_with_system(llm, prompt)


def generate_teaching_case(
    topic: str,
    age: Optional[str] = None,
    goal: Optional[str] = None,
    scenario: Optional[str] = None,
    use_rag: bool = True,
) -> str:
    """生成教学案例"""
    context = ""
    if use_rag:
        context = get_context_for_writing(topic, top_k=6)
    llm = get_chat_llm(temperature=0.5)
    prompt = TEACHING_CASE_PROMPT.format(
        title=topic,
        age=age or "不限",
        goal=goal or "根据活动名称与背景设定",
        context=context or "（暂无知识库内容）",
    )
    return _invoke_with_system(llm, prompt)


def reduce_weight(content: str, focus: Optional[str] = None) -> str:
    """论文降重"""
    llm = get_chat_llm(temperature=0.6)
    prompt = REDUCE_WEIGHT_PROMPT.format(
        focus=focus or "同义替换与句式改写",
        content=content,
    )
    return _invoke_with_system(llm, prompt)


def generate_topic_application(
    topic: str,
    direction: Optional[str] = None,
    use_rag: bool = True,
) -> str:
    """生成课题申报书（评职称用）"""
    context = ""
    if use_rag:
        context = get_context_for_writing(topic, top_k=6)
    llm = get_chat_llm(temperature=0.5)
    prompt = TOPIC_APPLICATION_PROMPT.format(
        topic=topic,
        direction=direction or "不限定",
        context=context or "（暂无知识库内容）",
    )
    return _invoke_with_system(llm, prompt)
