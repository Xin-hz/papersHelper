"""RAG 服务：LangChain 检索增强生成"""
from typing import List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.prompts import SYSTEM_PROMPT
from app.services.llm_service import get_chat_llm
from app.services.vector_store import get_retriever


RAG_SYSTEM_APPEND = """请根据提供的知识库资料回答用户问题。若资料中未包含答案，请如实说明。"""

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT + "\n\n" + RAG_SYSTEM_APPEND),
    ("human", """以下是知识库资料：

{context}

请根据以上资料回答问题：

{question}

要求：
1. 优先引用资料内容
2. 进行总结归纳
3. 语言保持学术性
4. 结构清晰"""),
])


def _format_docs(docs) -> str:
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


def _source_item(doc) -> dict:
    """把检索片段整理成可展示的来源信息（文档标题/作者/年份/摘录）"""
    md = doc.metadata or {}
    title = md.get("title") or md.get("source") or "未知文档"
    snippet = doc.page_content.strip()
    if len(snippet) > 200:
        snippet = snippet[:200] + "..."
    return {
        "title": str(title),
        "source": md.get("source", ""),
        "authors": md.get("authors") or [],
        "year": md.get("year"),
        "snippet": snippet,
    }


def ask_knowledge(question: str, top_k: Optional[int] = None) -> tuple[str, list[dict]]:
    """
    基于知识库 RAG 回答问题。
    返回 (answer, sources)，sources 为结构化来源列表。
    """
    retriever = get_retriever(top_k=top_k)
    docs = retriever.invoke(question)
    context = _format_docs(docs)

    llm = get_chat_llm(temperature=0.3)
    answer = (RAG_PROMPT | llm | StrOutputParser()).invoke(
        {"context": context or "（知识库中未检索到相关内容）", "question": question}
    )

    return answer, [_source_item(d) for d in docs]


def retrieve_for_writing(query: str, top_k: Optional[int] = None) -> list:
    """为写作检索知识库片段，返回 Document 列表（含元数据）"""
    retriever = get_retriever(top_k=top_k or 4)
    return retriever.invoke(query)


def get_context_for_writing(query: str, top_k: Optional[int] = None) -> str:
    """为论文生成/扩写提供检索到的上下文"""
    docs = retrieve_for_writing(query, top_k=top_k or 8)
    return _format_docs(docs)
