#!/usr/bin/env python3
"""paper-helper 成稿自检（零依赖）。

检查项：
  1 结构完整：标题行 / 摘要： / 关键词： / ≥3 个一级章节 / 参考文献节
  2 字数：正文（不含参考文献、图表定义行、表格数据行）是否超上限（默认 4000 为评选口径，可用 --limit 调整）
  3 引文对应：正文 [n] 与参考文献条目编号一一对应（缺引/缺条/多余都报）
  4 图表配对：正文"（见图1）（见表1）"引用 ↔「图:…图1…」「表:…表1…」定义行，双向核对
  5 样本量一致：全文"共N名"只允许一个值（出现多个不同值报警）
  6 百分比清单：列出全部 N% 供人工核对前后测是否闭合

用法：
  python3 check_paper.py 论文.txt [--limit 4000]
输入格式与 make_docx.py 相同（首行标题；「表:表题|表头…」「图:路径|图题」标记行）。
"""
import argparse
import re
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="论文文本文件（make_docx 输入格式）")
    ap.add_argument("--limit", type=int, default=4000, help="正文字数上限（默认 4000，评选口径；其他用途用 --limit 调整）")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"文件不存在: {path}", file=sys.stderr)
        sys.exit(2)
    lines = [l.rstrip() for l in path.read_text(encoding="utf-8").splitlines()]

    results = []  # (ok: bool|None, name, detail)
    def item(ok, name, detail=""):
        results.append((ok, name, detail))

    # ---------- 分段 ----------
    nonempty = [l for l in lines if l.strip()]
    title = nonempty[0] if nonempty else ""
    ref_idx = next((i for i, l in enumerate(lines) if l.strip() == "参考文献"), None)
    body_lines = lines[:ref_idx] if ref_idx is not None else lines
    ref_lines = lines[ref_idx + 1:] if ref_idx is not None else []
    # 排除图表定义行与表格数据行后的"纯正文"
    prose = [l for l in body_lines[1:]
             if not l.strip().startswith(("表:", "图:"))
             and l.count("|") < 2]

    # ---------- 1 结构 ----------
    item(bool(title), "标题行", title[:30])
    item(any(l.strip().startswith("摘要") for l in body_lines), "摘要")
    item(any(l.strip().startswith("关键词") for l in body_lines), "关键词")
    chapters = re.findall(r"^([一二三四五六七八九十]+、)", "\n".join(body_lines), re.M)
    item(len(chapters) >= 3, f"一级章节 ≥3（实际 {len(chapters)}）")
    item(ref_idx is not None, "参考文献节")

    # ---------- 2 字数 ----------
    body_text = "\n".join(prose)
    n_chars = len(re.sub(r"\s", "", body_text))
    item(n_chars <= args.limit, f"正文字数 ≤{args.limit}（实际 {n_chars}）")

    # ---------- 3 引文对应 ----------
    cited = set(re.findall(r"\[(\d+)\]", "\n".join(body_lines)))
    listed = set(re.findall(r"^\[(\d+)\]", "\n".join(ref_lines), re.M)
                 or re.findall(r"^(\d+)\. ", "\n".join(ref_lines), re.M))
    if cited or listed:
        missing_refs = sorted(cited - listed, key=int)
        unused_refs = sorted(listed - cited, key=int)
        item(not missing_refs and not unused_refs, "引文与文献一一对应",
             f"文中{sorted(cited, key=int)} vs 文末{sorted(listed, key=int)}"
             + (f"；缺条目{missing_refs}" if missing_refs else "")
             + (f"；未被引用{unused_refs}" if unused_refs else ""))
    else:
        item(None, "引文对应（全文无引注，建议补充）")

    # ---------- 4 图表配对 ----------
    defined = set()
    for l in lines:
        if l.strip().startswith(("表:", "图:")):
            # 图题在竖线之后（图:路径|图题），表题在竖线之前；整行扫描编号即可（路径不含"图N"字样）
            defined |= set(re.findall(r"([图表]\d+)", l.strip()[2:]))
    referenced = set(re.findall(r"([图表]\d+)", "\n".join(prose)))
    if defined or referenced:
        no_def = referenced - defined
        no_ref = defined - referenced
        item(not no_def and not no_ref, "图表定义与引用配对",
             f"定义{sorted(defined)} vs 引用{sorted(referenced)}"
             + (f"；缺定义{no_def}" if no_def else "")
             + (f"；未被引用{no_ref}" if no_ref else ""))
    else:
        item(None, "图表配对（纯文字稿，无图表）")

    # ---------- 5 样本量 ----------
    samples = set(re.findall(r"共\s*(\d+)\s*名", path.read_text(encoding="utf-8")))
    if samples:
        item(len(samples) == 1, f"样本量唯一（出现值：{sorted(samples)}）")
    else:
        item(None, "样本量（未检出'共N名'表述）")

    # ---------- 6 百分比清单 ----------
    pcts = re.findall(r"(\d+(?:\.\d+)?)\s*%", body_text)
    item(None, f"百分比清单（共{len(pcts)}处，人工核对前后测闭合）", " ".join(sorted(set(pcts), key=float)) or "无")

    # ---------- 输出 ----------
    icons = {True: "✅", False: "❌", None: "ℹ️"}
    fails = 0
    for ok, name, detail in results:
        if ok is False:
            fails += 1
        line = f"{icons[ok]} {name}" + (f"  —— {detail}" if detail else "")
        print(line)
    print(f"\n结论：{'全部通过' if fails == 0 else f'{fails} 项未通过，请修改后重检'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
