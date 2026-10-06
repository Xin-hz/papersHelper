#!/usr/bin/env python3
"""paper-helper 知识库索引构建脚本（仅依赖 Python 标准库）。

约定：
  知识库根目录默认 ~/paper-kb/，可用环境变量 PAPER_KB 覆盖
  根目录下的每个子文件夹 = 一个分类（如 获奖论文/ 园本课程/ 政策文件/）
  顶层散放文件归入"未分类"

支持格式：.txt .md .docx（直接解析）；.doc（macOS textutil）；.pdf（需系统装有 pdftotext）
索引写入 <根目录>/.index.db（SQLite FTS5，trigram 分词支持中文子串检索）

用法：
  python3 kb_build.py            # 全量重建索引
  python3 kb_build.py --quiet    # 只输出统计
"""
import hashlib
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

KB_ROOT = Path(os.environ.get("PAPER_KB", str(Path.home() / "paper-kb")))
DB_PATH = KB_ROOT / ".index.db"
CHUNK_SIZE = 700  # 字符

# 有效内容字符（中文/字母/数字/常用标点/空白），用于过滤乱码
_MEANINGFUL = re.compile(r"[\u4e00-\u9fffA-Za-z0-9，。；：、！？…—·（）()《》“”\"':;,.!?\s]")
_CJK = re.compile(r"[\u4e00-\u9fff]")
_CTRL = re.compile(r"[\x00-\x08\x0b\x0e-\x1f]")
_XML_JUNK = re.compile(r"xmlns|xpacket|<rdf:|mwg-rs|<\?xml|<x:xmpmeta")


def is_valid(text: str) -> bool:
    """过滤乱码：过短/控制字符/有效占比低/无中文且非英文散文/XML 残渣"""
    t = text.strip()
    if len(t) < 50 or _CTRL.search(t):
        return False
    if len(_MEANINGFUL.findall(t)) / len(t) < 0.6:
        return False
    if len(_CJK.findall(t)) >= 10:
        return True
    if _XML_JUNK.search(t):
        return False
    return len(re.findall(r"[A-Za-z]{2,}", t)) >= 15


def extract_text(path: Path):
    suffix = path.suffix.lower()
    try:
        if suffix in {".txt", ".md"}:
            return path.read_text(encoding="utf-8", errors="replace")
        if suffix == ".docx":
            with zipfile.ZipFile(path) as z:
                xml = z.read("word/document.xml").decode("utf-8", errors="replace")
            xml = re.sub(r"<w:tab[^>]*/>", "\t", xml)
            xml = re.sub(r"</w:p>", "\n", xml)
            text = re.sub(r"<[^>]+>", "", xml)
            return text
        if suffix == ".doc":
            if sys.platform != "darwin":
                return None
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
                out = f.name
            subprocess.run(["textutil", "-convert", "txt", "-output", out, str(path)],
                           check=True, capture_output=True, timeout=60)
            text = Path(out).read_text(encoding="utf-8", errors="replace").replace("\x00", "")
            Path(out).unlink(missing_ok=True)
            return text
        if suffix == ".pdf":
            r = subprocess.run(["pdftotext", str(path), "-"], capture_output=True, text=True, timeout=120)
            return r.stdout if r.returncode == 0 else None
    except Exception:
        return None
    return None


def chunk_text(text: str):
    """按空行分段后合并到约 CHUNK_SIZE 字符的块"""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    chunks, buf = [], ""
    for b in blocks:
        if buf and len(buf) + len(b) > CHUNK_SIZE:
            chunks.append(buf)
            buf = b
        else:
            buf = f"{buf}\n{b}" if buf else b
        while len(buf) > CHUNK_SIZE * 2:  # 超长段硬切
            chunks.append(buf[:CHUNK_SIZE * 2])
            buf = buf[CHUNK_SIZE * 2:]
    if buf.strip():
        chunks.append(buf)
    return chunks


def init_db(conn):
    # 普通表 + instr 检索（见 kb_query.py）：不用 FTS5——trigram 索引对中文文本体积膨胀近千倍，
    # 且需 SQLite ≥3.34；instr 逐块扫描在万级块规模下毫秒级完成，零版本依赖
    conn.execute("CREATE TABLE IF NOT EXISTS chunks ("
                 "id INTEGER PRIMARY KEY, text TEXT, category TEXT, source TEXT)")
    conn.execute("DELETE FROM chunks")


def main():
    quiet = "--quiet" in sys.argv
    if not KB_ROOT.is_dir():
        print(f"知识库目录不存在：{KB_ROOT}\n请创建后放入文档（子文件夹=分类），再运行本脚本。")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)  # 内部已清空旧数据
    conn.commit()

    stats = {"files": 0, "chunks": 0, "skipped": [], "junk_filtered": 0}
    entries = sorted(KB_ROOT.rglob("*"))
    for path in entries:
        rel = path.relative_to(KB_ROOT)
        # 跳过隐藏文件/目录（如 .drafts 成稿目录、.index.db 本身）
        if any(p.startswith(".") for p in rel.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in {
            ".txt", ".md", ".docx", ".doc", ".pdf"
        }:
            continue
        category = rel.parts[0] if len(rel.parts) > 1 else "未分类"
        text = extract_text(path)
        if not text or not text.strip():
            stats["skipped"].append(str(rel))
            continue
        chunks = [c for c in chunk_text(text) if is_valid(c)]
        stats["junk_filtered"] += sum(1 for c in chunk_text(text) if not is_valid(c))
        if not chunks:
            stats["skipped"].append(str(rel) + "（无有效内容）")
            continue
        conn.executemany(
            "INSERT INTO chunks(text, category, source) VALUES (?,?,?)",
            [(c, category, path.name) for c in chunks],
        )
        stats["files"] += 1
        stats["chunks"] += len(chunks)
        if not quiet:
            print(f"  [{category}] {path.name}: {len(chunks)} 块")
    conn.commit()
    conn.execute("VACUUM")  # 回收已删除页，避免历史重建残留导致库文件虚大
    conn.close()

    print(f"\n索引完成：{stats['files']} 个文件 / {stats['chunks']} 个文本块（过滤乱码块 {stats['junk_filtered']} 个）-> {DB_PATH}")
    if stats["skipped"]:
        print(f"跳过 {len(stats['skipped'])} 个无法提取的文件（扫描版 PDF 或加密文档）：")
        for s in stats["skipped"][:5]:
            print(f"  - {s}")


if __name__ == "__main__":
    main()
