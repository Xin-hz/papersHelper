#!/usr/bin/env python3
"""paper-helper 知识库检索脚本（仅标准库）。

用法：
  python3 kb_query.py "低结构材料 投放策略"        # 默认返回 5 条
  python3 kb_query.py "观察记录" -k 10 -c 园本课程  # 指定条数与分类
多词按 OR 召回（任一命中），按命中词数与词频排序；子串匹配，任意长度中文词都可用。
"""
import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path

KB_ROOT = Path(os.environ.get("PAPER_KB", str(Path.home() / "paper-kb")))
DB_PATH = KB_ROOT / ".index.db"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="检索词（可含多个词，空格分隔）")
    ap.add_argument("-k", "--top", type=int, default=5, help="返回条数（默认 5）")
    ap.add_argument("-c", "--category", help="限定分类（即知识库子文件夹名）")
    args = ap.parse_args()

    if not DB_PATH.exists():
        print(f"索引不存在：{DB_PATH}\n请先运行 kb_build.py 构建索引。", file=sys.stderr)
        sys.exit(1)

    terms = [t for t in re.split(r"\s+", args.query.strip()) if len(t) >= 2]
    if not terms:
        print("检索词太短（每词至少 2 个字符）", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    # 用 instr 而非 LIKE：部分 SQLite 构建（如 macOS 系统 Python）的 LIKE 对中文匹配异常
    where = " OR ".join("instr(text, ?) > 0" for _ in terms)
    params = list(terms)
    if args.category:
        where = f"({where}) AND category = ?"
        params.append(args.category)
    rows = conn.execute(f"SELECT text, category, source FROM chunks WHERE {where}", params).fetchall()
    conn.close()

    def rank(row):
        text = row[0]
        hit_terms = sum(1 for t in terms if t in text)
        freq = sum(text.count(t) for t in terms)
        return (hit_terms, freq)

    rows.sort(key=rank, reverse=True)
    if not rows:
        print("未检索到相关内容。可换关键词，或运行 kb_build.py 更新索引。")
        return
    for i, (text, category, source) in enumerate(rows[: args.top], 1):
        snippet = re.sub(r"\s+", " ", text)[:200]
        print(f"[{i}]【{category}】{source}")
        print(f"    {snippet}")
        print()


if __name__ == "__main__":
    main()
