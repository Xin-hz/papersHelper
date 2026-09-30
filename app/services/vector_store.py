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
    # 显式超时与重试：避免个别请求挂死导致整个入库流程卡住
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=30.0, max_retries=3)

    class BailianEmbeddings(Embeddings):
        def _embed(self, texts: List[str]) -> List[List[float]]:
            # 批量请求（兼容接口支持数组输入），比逐条调用快一个数量级
            out: List[List[float]] = []
            batch = 10
            for i in range(0, len(texts), batch):
                part = [t if isinstance(t, str) else str(t or "") for t in texts[i:i + batch]]
                r = client.embeddings.create(model=model, input=part)
                out.extend(d.embedding for d in r.data)
            return out

        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            return self._embed(texts)

        def embed_query(self, text: str) -> List[float]:
            text = text if isinstance(text, str) else (str(text) if text is not None else "")
            return self._embed([text])[0]

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


def clear_collection(collection_name: Optional[str] = None) -> int:
    """清空指定集合的全部向量片段，返回删除的条数（用于重建索引）"""
    import psycopg2

    name = collection_name or get_collection_name()
    conn = psycopg2.connect(get_settings().database_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM langchain_pg_embedding
                WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = %s)
                """,
                (name,),
            )
            deleted = cur.rowcount
        conn.commit()
        return deleted
    finally:
        conn.close()


def get_vector_store_stats() -> dict:
    """获取向量库统计信息"""
    try:
        import psycopg2
        from app.config import get_settings

        settings = get_settings()
        db_url = settings.database_url

        # 解析数据库连接信息
        if db_url.startswith("postgresql://") or db_url.startswith("postgresql+psycopg2://"):
            # 移除协议前缀
            clean_url = db_url.replace("postgresql+psycopg2://", "postgresql://")
            clean_url = clean_url.replace("postgresql://", "")

            # 解析连接信息
            parts = clean_url.split("@")
            if len(parts) == 2:
                user_pass = parts[0].split(":")
                host_db = parts[1].split("/")

                user = user_pass[0] if len(user_pass) > 0 else "postgres"
                password = user_pass[1] if len(user_pass) > 1 else ""
                host_port = host_db[0].split(":")
                host = host_port[0]
                port = host_port[1] if len(host_port) > 1 else "5432"
                database = host_db[1] if len(host_db) > 1 else "postgres"

                # 连接数据库
                conn = psycopg2.connect(
                    host=host,
                    port=int(port),
                    database=database,
                    user=user,
                    password=password
                )

                cursor = conn.cursor()

                # 获取集合名称
                collection_name = get_collection_name()

                # 统计文档数量（去重title或source的组合）
                cursor.execute(f"""
                    SELECT COUNT(DISTINCT CASE
                        WHEN cmetadata->>'title' IS NOT NULL AND cmetadata->>'title' != ''
                        THEN cmetadata->>'title'
                        ELSE cmetadata->>'source'
                    END)
                    FROM langchain_pg_embedding
                    WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = '{collection_name}')
                """)
                document_count = cursor.fetchone()[0] or 0

                # 统计向量片段总数
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM langchain_pg_embedding
                    WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = '{collection_name}')
                """)
                vector_count = cursor.fetchone()[0] or 0

                cursor.close()
                conn.close()

                return {
                    "document_count": document_count,
                    "vector_count": vector_count
                }
    except Exception as e:
        print(f"获取向量库统计出错: {e}")
        return {
            "document_count": 0,
            "vector_count": 0
        }
