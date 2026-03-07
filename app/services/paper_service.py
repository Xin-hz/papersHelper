"""论文生成、润色、扩写业务逻辑"""
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage

from app.prompts import SYSTEM_PROMPT
from app.services.llm_service import get_chat_llm
from app.services.rag_service import get_context_for_writing


def _invoke_with_system(llm, user_prompt: str) -> str:
    """使用统一人格系统 Prompt 调用 LLM"""
    return llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_prompt)]).content


GENERATE_PROMPT = """写一篇幼儿园教育研究论文。

论文主题：
{topic}

研究方向：
{direction}

字数要求：
{words}

可选大纲（若有）：
{outline}

写作要求：
1. 内容符合中国幼儿园教育实践
2. 语言具有教育研究论文风格
3. 提供具体教学案例
4. 内容具有一定理论依据

参考知识库内容（仅供参考，可选择性引用）：
{context}

输出结构：
标题

摘要（200字）

关键词（3-5个）

一、研究背景
二、理论基础
三、教学实践案例
四、教学策略分析
五、实践效果

结论

参考文献（3-5条）

请直接输出完整论文正文，按上述结构组织。"""


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


def generate_paper(
    title: str,
    outline: Optional[str] = None,
    direction: Optional[str] = None,
    words: Optional[str] = None,
    use_rag: bool = True,
) -> str:
    """生成论文正文"""
    context = ""
    if use_rag:
        context = get_context_for_writing(title, top_k=8)
    llm = get_chat_llm(temperature=0.6)
    prompt = GENERATE_PROMPT.format(
        topic=title,
        direction=direction or "不限定",
        words=words or "按常规篇幅",
        outline=outline or "无",
        context=context or "（暂无知识库内容）",
    )
    return _invoke_with_system(llm, prompt)


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
