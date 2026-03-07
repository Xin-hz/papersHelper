"""RAG 服务：LangChain 检索增强生成"""
from typing import List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
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


def ask_knowledge(question: str, top_k: Optional[int] = None) -> tuple[str, List[str]]:
    """
    基于知识库 RAG 回答问题。
    返回 (answer, sources)。
    """
    retriever = get_retriever(top_k=top_k)
    llm = get_chat_llm(temperature=0.3)
    prompt = RAG_PROMPT

    chain = (
        {"context": retriever | _format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    answer = chain.invoke(question)

    # 检索到的文档片段作为来源
    docs = retriever.invoke(question)
    sources = [d.page_content[:200] + "..." if len(d.page_content) > 200 else d.page_content for d in docs]

    return answer, sources


def get_context_for_writing(query: str, top_k: Optional[int] = None) -> str:
    """为论文生成/扩写提供检索到的上下文"""
    retriever = get_retriever(top_k=top_k or 8)
    docs = retriever.invoke(query)
    return _format_docs(docs)
