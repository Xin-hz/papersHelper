#!/usr/bin/env python3
"""成稿归档速查（仅标准库）。列出 ~/paper-kb/.drafts/ 里的近期成稿，供写作前比对结构与化名。

用法：
  python3 drafts.py            # 最近 10 篇（标题/时间/字数）
  python3 drafts.py 20         # 最近 20 篇
"""
import os
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path

KB_ROOT = Path(os.environ.get("PAPER_KB", str(Path.home() / "paper-kb")))
DRAFTS = KB_ROOT / ".drafts"


def docx_first_line(p: Path) -> str:
    try:
        with zipfile.ZipFile(p) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
        texts = re.findall(r"<w:t[^>]*>([^<]*)</w:t>", xml)
        for t in texts:
            if t.strip():
                return t.strip()
    except Exception:
        pass
    return ""


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 10
    if not DRAFTS.is_dir():
        print(f"成稿目录不存在：{DRAFTS}\n首次交付成稿时会自动创建；或运行 init_kb.py 初始化。")
        return
    files = [p for p in DRAFTS.iterdir()
             if p.is_file() and p.suffix.lower() in {".txt", ".md", ".docx"}]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        print("成稿目录为空。写完第一篇后，把终稿（txt+docx）存进来，下一篇会自动比对防雷同。")
        return
    print(f"最近 {min(n, len(files))} 篇成稿（新→旧）：")
    for p in files[:n]:
        mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        if p.suffix.lower() == ".docx":
            title = docx_first_line(p) or "（无法读取标题）"
            size = "-"
        else:
            text = p.read_text(encoding="utf-8", errors="replace")
            title = next((l.strip() for l in text.splitlines() if l.strip()), "（无标题）")
            size = f"{len(text)}字"
        print(f"  [{mtime}] {title[:40]}  {size}  {p.name}")
    print("\n写作前自查：本篇结构组合/章节骨架/化名与上面近期成稿重复了吗？重复就换（见 写作参考卡.md）。")


if __name__ == "__main__":
    main()
