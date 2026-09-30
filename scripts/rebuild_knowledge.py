"""重建知识库索引：清空向量库后，按当前切片配置重新入库上传目录下的全部文档。

用法：
    python scripts/rebuild_knowledge.py

修改 CHUNK_SIZE / CHUNK_OVERLAP 后必须执行一次，否则旧片段仍按旧参数切分。
"""
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.services.document_loader import load_document, chunk_documents
from app.services.vector_store import (
    add_documents_to_store,
    clear_collection,
    get_collection_name,
    get_vector_store_stats,
)

UUID_PREFIX = re.compile(r"^[0-9a-f]{32}_")  # 上传文件名带的 uuid 前缀，展示时去掉


def _ingested_sources() -> set:
    """查询已入库的文档来源名，用于断点续跑时跳过"""
    import psycopg2

    conn = psycopg2.connect(get_settings().database_url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT cmetadata->>'source'
                FROM langchain_pg_embedding
                WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = %s)
                """,
                (get_collection_name(),),
            )
            return {r[0] for r in cur.fetchall() if r[0]}
    finally:
        conn.close()


def main():
    resume = "--resume" in sys.argv
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    files = [
        p
        for p in sorted(upload_dir.rglob("*"))
        if p.suffix.lower() in {".pdf", ".docx", ".doc"} and "temp" not in p.parts
    ]
    if not files:
        print(f"{upload_dir} 下没有可入库的文档")
        return

    # 按文件内容 md5 去重（同一文件多次上传只入库一次，避免重复片段刷屏检索结果）
    unique_files = []
    seen_hashes = set()
    for p in files:
        h = hashlib.md5(p.read_bytes()).hexdigest()
        if h in seen_hashes:
            print(f"  跳过重复文件: {UUID_PREFIX.sub('', p.name)}")
            continue
        seen_hashes.add(h)
        unique_files.append(p)

    if resume:
        done = _ingested_sources()
        unique_files = [p for p in unique_files if UUID_PREFIX.sub("", p.name) not in done]
        print(f"断点续跑：跳过已入库 {len(done)} 个来源，剩余 {len(unique_files)} 个文件待入库\n")
    else:
        deleted = clear_collection()
        print(f"已清空旧索引：{deleted} 条片段")
        print(f"待入库文件：{len(unique_files)} 个（另跳过 {len(files) - len(unique_files)} 个重复文件）\n")

    total_chunks = ok = 0
    failed = []
    for p in unique_files:
        try:
            docs = chunk_documents(load_document(str(p)))
            display = UUID_PREFIX.sub("", p.name)
            for d in docs:
                d.metadata["source"] = display
            add_documents_to_store(docs)
            total_chunks += len(docs)
            ok += 1
            print(f"  [{ok}/{len(files)}] {display}: {len(docs)} 片段")
        except Exception as e:
            failed.append(f"{p.name}: {e}")
            print(f"  失败 {p.name}: {e}")

    print(f"\n完成：成功 {ok} 个文件，共 {total_chunks} 片段；失败 {len(failed)} 个")
    for f in failed:
        print(f"  失败详情 {f}")
    print("向量库统计:", get_vector_store_stats())


if __name__ == "__main__":
    main()
