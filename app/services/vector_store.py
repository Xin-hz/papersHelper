"""向量存储：pgvector + 本地 BGE 或 通义 Embedding API"""
from typing import List, Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import PGVector

from app.config import get_settings

_vector_store: Optional[PGVector] = None


def get_embedding_model() -> Embeddings:
    """获取 Embedding：local=本地BGE(需下载)，dashscope=通义API(无需下载)"""
    settings = get_settings()
    if getattr(settings, "embedding_provider", "local") == "dashscope":
        return _get_dashscope_embeddings()
    return _get_local_embeddings()


def _get_local_embeddings() -> Embeddings:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    s = get_settings()
    return HuggingFaceEmbeddings(
        model_name=s.embedding_model,
        model_kwargs={"device": s.embedding_device},
        encode_kwargs={"normalize_embeddings": True},
    )


def _get_dashscope_embeddings() -> Embeddings:
    """百炼 Embedding：自定义类，保证每次请求 input 为纯 str，避免 contents 报错"""
    from openai import OpenAI
    s = get_settings()
    api_key = getattr(s, "dashscope_api_key", "") or getattr(s, "qwen_api_key", "")
    if not api_key:
        raise ValueError("使用 dashscope 时请在 .env 中设置 DASHSCOPE_API_KEY 或 QWEN_API_KEY")
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model = getattr(s, "dashscope_embedding_model", "text-embedding-v3")
    client = OpenAI(api_key=api_key, base_url=base_url)

    class BailianEmbeddings(Embeddings):
        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            out = []
            for t in texts:
                t = t if isinstance(t, str) else (str(t) if t is not None else "")
                r = client.embeddings.create(model=model, input=t)
                out.append(r.data[0].embedding)
            return out

        def embed_query(self, text: str) -> List[float]:
            text = text if isinstance(text, str) else (str(text) if text is not None else "")
            r = client.embeddings.create(model=model, input=text)
            return r.data[0].embedding

    return BailianEmbeddings()


def get_connection_string() -> str:
    url = get_settings().database_url
    if url.startswith("postgresql://") and "postgresql+" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def get_collection_name() -> str:
    return "papers_knowledge"


def create_vector_store(
    embedding: Optional[Embeddings] = None,
    collection_name: Optional[str] = None,
    use_existing: bool = True,
) -> PGVector:
    """创建或复用 pgvector（进程内单例，避免重复创建触发 __del__ 报错）"""
    global _vector_store
    if _vector_store is not None and use_existing:
        return _vector_store
    emb = embedding or get_embedding_model()
    conn = get_connection_string()
    name = collection_name or get_collection_name()
    kwargs = {
        "connection_string": conn,
        "collection_name": name,
        "pre_delete_collection": not use_existing,
    }
    try:
        store = PGVector(embedding_function=emb, **kwargs)
    except TypeError:
        store = PGVector(embedding=emb, **kwargs)
    if use_existing:
        _vector_store = store
    return store


def add_documents_to_store(
    documents: List[Document], collection_name: Optional[str] = None
) -> None:
    """将切片后的文档加入向量库"""
    vs = create_vector_store(collection_name=collection_name, use_existing=True)
    vs.add_documents(documents)


def get_retriever(top_k: Optional[int] = None):
    """获取 RAG 检索器"""
    settings = get_settings()
    k = top_k or settings.top_k_retrieve
    vs = create_vector_store(use_existing=True)
    return vs.as_retriever(search_kwargs={"k": k})
