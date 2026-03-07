"""文档加载与切片：支持 PDF、DOCX、DOC"""
from pathlib import Path
import platform
import subprocess
import tempfile
from typing import List

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings


def _load_doc_legacy(file_path: str) -> List[Document]:
    """加载旧版 .doc（Mac 用 textutil，其他系统请另存为 .docx）"""
    path = Path(file_path)
    if platform.system() == "Darwin":
        try:
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
                out_path = f.name
            subprocess.run(
                ["textutil", "-convert", "txt", "-output", out_path, str(path)],
                check=True,
                capture_output=True,
                timeout=30,
            )
            text = Path(out_path).read_text(encoding="utf-8", errors="replace")
            Path(out_path).unlink(missing_ok=True)
        except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            raise ValueError(f".doc 转换失败: {e}") from e
    else:
        raise ValueError(".doc 仅在 macOS 下支持，请将 .doc 另存为 .docx 后上传。")
    if not text.strip():
        return []
    return [Document(page_content=text.strip(), metadata={"source": path.name})]


def _load_docx(file_path: str) -> List[Document]:
    """使用 python-docx 加载 DOCX"""
    try:
        from docx import Document as DocxDocument
    except ImportError:
        raise ImportError("请安装 python-docx: pip install python-docx")
    doc = DocxDocument(file_path)
    parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            row_text = " ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                parts.append(row_text)
    text = "\n\n".join(parts)
    if not text.strip():
        return []
    return [Document(page_content=text, metadata={"source": Path(file_path).name})]


def load_document(file_path: str) -> List[Document]:
    """根据后缀加载单个文件为 Document 列表（未切片）"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        loader = PyPDFLoader(str(path))
        pages = loader.load()
        return pages
    if suffix == ".docx":
        return _load_docx(str(path))
    if suffix == ".doc":
        return _load_doc_legacy(str(path))
    raise ValueError(f"不支持的文件格式: {suffix}，仅支持 .pdf / .docx / .doc")


def chunk_documents(documents: List[Document]) -> List[Document]:
    """对文档列表做递归切片"""
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "。", "；", " ", ""],
        length_function=len,
    )
    return splitter.split_documents(documents)


def load_and_chunk_file(file_path: str) -> List[Document]:
    """加载并切片单个文件，返回 Document 列表"""
    docs = load_document(file_path)
    return chunk_documents(docs)


def load_and_chunk_directory(dir_path: str) -> List[Document]:
    """加载目录下所有 PDF/DOCX 并切片"""
    allowed = {".pdf", ".docx", ".doc"}
    all_docs: List[Document] = []
    for p in Path(dir_path).rglob("*"):
        if p.is_file() and p.suffix.lower() in allowed:
            try:
                docs = load_and_chunk_file(str(p))
                for d in docs:
                    d.metadata["source"] = str(p.name)
                all_docs.extend(docs)
            except Exception as e:
                print(f"跳过文件 {p}: {e}")
    return all_docs
