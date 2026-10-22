#!/usr/bin/env python3
"""把 Word 成稿渲染成逐页 PNG，供排版视觉验收（条件功能，仅标准库）。

依赖（缺任一则提示并退出，不影响核心流程）：
  LibreOffice（soffice；macOS 也认 /Applications/LibreOffice.app 路径）→ docx 转 PDF
  poppler 的 pdftoppm → PDF 逐页转 PNG

用法：
  python3 render_docx.py 成稿.docx [输出目录]    # 目录默认 成稿_pages/（与 docx 同级）
输出：目录内 成稿.pdf 与 成稿-1.png、成稿-2.png…（110 DPI），路径逐行打印
"""
import shutil
import subprocess
import sys
from pathlib import Path


def find_soffice():
    for c in (shutil.which("soffice"), shutil.which("libreoffice"),
              "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if c and Path(c).is_file():
            return c
    return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    src = Path(sys.argv[1]).expanduser().resolve()
    if not src.is_file():
        print(f"找不到文件：{src}", file=sys.stderr)
        sys.exit(1)
    outdir = (Path(sys.argv[2]).expanduser().resolve() if len(sys.argv) > 2
              else src.parent / f"{src.stem}_pages")
    outdir.mkdir(parents=True, exist_ok=True)

    soffice = find_soffice()
    pdftoppm = shutil.which("pdftoppm")
    missing = [n for n, v in (("LibreOffice(soffice)", soffice), ("pdftoppm(poppler)", pdftoppm)) if not v]
    if missing:
        print("排版视觉验收不可用，缺依赖：" + "、".join(missing) + "\n"
              "  安装：brew install --cask libreoffice && brew install poppler\n"
              "  不装不影响核心流程——跳过视觉验收，交付前人工打开 Word 检查即可。",
              file=sys.stderr)
        sys.exit(2)

    r = subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(outdir), str(src)],
                       capture_output=True, text=True, timeout=180)
    pdf = outdir / f"{src.stem}.pdf"
    if r.returncode != 0 or not pdf.is_file():
        print("docx 转 PDF 失败：\n" + (r.stderr or r.stdout)[:300], file=sys.stderr)
        sys.exit(1)

    r = subprocess.run([pdftoppm, "-png", "-r", "110", str(pdf), str(outdir / src.stem)],
                       capture_output=True, text=True, timeout=180)
    pages = sorted(outdir.glob(f"{src.stem}-*.png"))
    if r.returncode != 0 or not pages:
        print("PDF 转 PNG 失败：\n" + (r.stderr or r.stdout)[:300], file=sys.stderr)
        sys.exit(1)

    print(f"渲染完成，共 {len(pages)} 页：")
    for p in pages:
        print(f"  {p}")
    print(f"PDF：{pdf}")


if __name__ == "__main__":
    main()
