"""论文降重服务：基于项目 LLM 的段落级改写。

规则移植自 paper-rewrite skill（/Users/Stars/Projects/skills/paper-rewrite）：
- 三档力度（轻度保留~80% / 中度~50% / 重度~30%）
- 保护内容：数据、引用标记、公式、专有名词、标题、参考文献条目
- 改写后做数字一致性校验，不一致的段落回退原文，确保数据不被改错
"""
import logging
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)

REWRITE_SYSTEM = """你是中文学术论文改写专家，任务是降低论文与已发表内容的表述相似度（降重），
同时严格保留原文的核心论点、数据、引用与逻辑结构。你的改写只在表达层面进行，
绝不引入新信息、新数据、新引用。"""

INTENSITY_RULES = {
    "light": (
        "改写力度：轻度（保留原文约 80% 表达，仅微调以打散相似句式）。\n"
        "可用手段：保守的同义替换（提出→设计、显著→明显、方法→方案）；"
        "主动句与被动句互换；拆分长句或合并短句；连接词替换（因此→故而、然而→不过）。"
    ),
    "medium": (
        "改写力度：中度（保留原文约 50% 表达，实质性改写）。\n"
        "可用手段（含轻度全部）：句式重构（合并/拆分/调整分句顺序）；"
        "概念抽象化或具体化（方法→技术路线、性能→综合表现）；主语变换（研究对象↔研究者）；"
        "因果重述（A导致B→B的产生源于A）；限定语调整（在…基础上→借助…）。"
    ),
    "heavy": (
        "改写力度：重度（保留原文约 30% 表达，彻底重组）。\n"
        "可用手段（含轻中度全部）：调整论点顺序重组段落结构；论证逻辑改写（归纳↔演绎）；"
        "重新切分论述单元；视角转换（方法视角↔问题视角）；表达范式变换（陈述↔设问、定义式↔描述式）。"
    ),
}

INTENSITY_LABELS = {"light": "轻度", "medium": "中度", "heavy": "重度"}

REWRITE_PROMPT = """改写下面的论文段落，用于降低与已发表内容的相似度。

{intensity_rules}

以下内容必须原样保留，违反即为严重错误：
- 所有数字、百分数、统计值、实验数据（如 95%、15 和 12）
- 引用标记（如 [1]、[2]、（Smith, 2020））
- 专有名词、人名、机构名、量表/模型名（如 CLASS、瑞吉欧、安吉游戏）
- 图表标号（如 图3-1、表2）

要求：保持核心论点与逻辑不变；保持学术语言风格，无口语化；不增加任何新信息；中文表达自然流畅。

直接输出改写后的段落正文，不要任何解释、前后缀或标记。

原文段落：
{paragraph}"""

# 段落级保护：命中即跳过不改写
_PROTECT_PATTERNS = [
    re.compile(r"^\s*(第?[一二三四五六七八九十\d]+[章节部分、.．]\s*\S{0,30})$"),  # 章节标题
    re.compile(r"^\s*(参考文献|致\s*谢|附\s*录|Abstract|Keywords|References)\s*:?\s*$", re.I),  # 独立标题行
    re.compile(r"^\s*(摘\s*要|关键词)\s*[:：]\s*\S{0,80}$"),  # 摘要/关键词短行（长摘要正文仍会改写）
    re.compile(r"^\s*[\d\s.,;，；、\[\]()（）-]+$"),  # 纯数据/编号行
    re.compile(r"(\$[^$]*\$|\\\\begin\{(?:equation|align|algorithm)\}|\\\\cite\{)"),  # 公式/LaTeX
    re.compile(r"^\s*(图|表|Figure|Table)\s*[\d一二三四五]"),  # 图表题注
    re.compile(r"^\s*\[\d+\]"),  # 参考文献条目
]
_MIN_CJK = re.compile(r"[\u4e00-\u9fff]")
_NUMBERS = re.compile(r"\d+(?:\.\d+)?%?")


def _is_protected(text: str) -> bool:
    """判断段落是否受保护（标题/公式/数据行/参考文献等，不改写）"""
    t = text.strip()
    if len(t) < 30:  # 短行多为标题、题注、列表项
        return True
    if len(_MIN_CJK.findall(t)) < 10:  # 中文太少的段落（英文摘要、符号行）不动
        return True
    return any(p.search(t) for p in _PROTECT_PATTERNS)


def _numbers_match(orig: str, rewritten: str) -> bool:
    """改写后原文中的每个数字都必须仍在（数据完整性校验）"""
    from collections import Counter

    return Counter(_NUMBERS.findall(orig)) == Counter(_NUMBERS.findall(rewritten))


def _rewrite_batch(paragraphs: List[str], intensity: str) -> List[Optional[str]]:
    """并行改写一组段落，返回与输入等长的结果列表（None 表示该段失败/回退）"""
    llm = get_llm(temperature=0.5)
    messages = [
        [
            SystemMessage(content=REWRITE_SYSTEM),
            HumanMessage(
                content=REWRITE_PROMPT.format(
                    intensity_rules=INTENSITY_RULES[intensity], paragraph=p
                )
            ),
        ]
        for p in paragraphs
    ]
    results = llm.batch(messages, config={"max_concurrency": 5})
    out: List[Optional[str]] = []
    for p, r in zip(paragraphs, results):
        text = (r.content or "").strip()
        text = re.sub(r"^(改写后[:：]|输出[:：])\s*", "", text)
        if not text or not _numbers_match(p, text):
            out.append(None)  # 失败或数据不一致 → 回退原文
        else:
            out.append(text)
    return out


def _extract_paragraphs(file_path: Path) -> List[str]:
    """按格式提取待处理文本段落（.txt/.md/.tex 直接读；.docx 并行提取段落+表格）"""
    suffix = file_path.suffix.lower()
    if suffix in {".txt", ".md", ".tex"}:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        return [b for b in re.split(r"\n\s*\n", text) if b.strip()]
    if suffix == ".docx":
        from docx import Document as DocxDocument

        doc = DocxDocument(str(file_path))
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        parts.append(cell.text)
        return parts
    if suffix == ".doc":
        import platform
        import subprocess
        import tempfile

        if platform.system() != "Darwin":
            raise ValueError(".doc 仅在 macOS 下支持，请另存为 .docx 后上传")
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            out_path = f.name
        subprocess.run(
            ["textutil", "-convert", "txt", "-output", out_path, str(file_path)],
            check=True, capture_output=True, timeout=60,
        )
        text = Path(out_path).read_text(encoding="utf-8", errors="replace").replace("\x00", "")
        Path(out_path).unlink(missing_ok=True)
        return [b for b in re.split(r"\n\s*\n", text) if b.strip()]
    if suffix == ".pdf":
        from app.services.document_loader import load_document

        pages = load_document(str(file_path))
        return [p.page_content for p in pages if p.page_content.strip()]
    raise ValueError(f"不支持的格式: {suffix}，支持 .txt / .md / .tex / .docx / .doc / .pdf")


def _set_docx_paragraph_text(para, new_text: str):
    """替换 docx 段落文本，保留段落样式（合并进首个 run）"""
    if para.runs:
        para.runs[0].text = new_text
        for r in para.runs[1:]:
            r.text = ""
    else:
        para.text = new_text


def _write_output(file_path: Path, rewrites: Dict[str, str], intensity: str) -> Path:
    """按原格式写出降重结果，文件名 {原名}_降重_{力度}.{扩展名}"""
    label = INTENSITY_LABELS[intensity]
    if file_path.suffix.lower() == ".docx":
        from docx import Document as DocxDocument

        out = file_path.parent / f"{file_path.stem}_降重_{label}.docx"
        shutil.copy(file_path, out)
        doc = DocxDocument(str(out))
        for p in doc.paragraphs:
            if p.text in rewrites:
                _set_docx_paragraph_text(p, rewrites[p.text])
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text in rewrites:
                        for p in cell.paragraphs:
                            if p.text in rewrites:
                                _set_docx_paragraph_text(p, rewrites[p.text])
        doc.save(str(out))
        return out

    # 文本类格式（.doc/.pdf 输入也落到 .txt/.md）
    paragraphs = _extract_paragraphs(file_path)
    out_suffix = file_path.suffix.lower() if file_path.suffix.lower() in {".txt", ".md", ".tex"} else ".txt"
    out = file_path.parent / f"{file_path.stem}_降重_{label}{out_suffix}"
    out.write_text(
        "\n\n".join(rewrites.get(p, p) for p in paragraphs), encoding="utf-8"
    )
    return out


def rewrite_paper(file_path: str, intensity: str = "medium", generate_diff: bool = False) -> Dict[str, object]:
    """论文降重主入口：按段落改写并输出新文件，保留原文件。"""
    path = Path(file_path)
    if intensity not in INTENSITY_RULES:
        return {"status": "error", "error": f"不支持的力度: {intensity}，可选 light/medium/heavy"}

    try:
        paragraphs = _extract_paragraphs(path)
    except Exception as e:
        logger.error("读取论文失败: %s", e)
        return {"status": "error", "error": f"读取论文失败: {e}"}

    # 去重后过滤出可改写段落（保护标题/公式/数据/文献等）
    unique = list(dict.fromkeys(paragraphs))
    targets = [p for p in unique if not _is_protected(p)]
    skipped = len(unique) - len(targets)
    if not targets:
        return {"status": "error", "error": "没有可改写的正文段落（内容过短或均为受保护内容）"}

    logger.info("降重开始: %s 段落（跳过受保护 %s 段），力度 %s", len(targets), skipped, intensity)
    results = _rewrite_batch(targets, intensity)

    rewrites: Dict[str, str] = {}
    reverted = 0
    diff_pairs = []
    for p, r in zip(targets, results):
        if r is None:
            reverted += 1
            continue
        rewrites[p] = r
        diff_pairs.append((p, r))

    if not rewrites:
        return {"status": "error", "error": "改写全部失败（LLM 返回异常或数据校验未通过），已保留原文件"}

    output_file = _write_output(path, rewrites, intensity)

    diff_file = None
    if generate_diff and diff_pairs:
        label = INTENSITY_LABELS[intensity]
        lines = [f"# 降重对照报告", "", f"力度：{label} ｜ 原文件：{path.name}", "",
                 f"改写 {len(diff_pairs)} 段；跳过受保护段落 {skipped} 段；校验回退 {reverted} 段", ""]
        for i, (orig, new) in enumerate(diff_pairs, 1):
            lines += [f"## 段落 {i}", "**原文**：", orig, "", "**改写**：", new, "", "---", ""]
        diff_file = str(path.parent / f"{path.stem}_降重_diff.md")
        Path(diff_file).write_text("\n".join(lines), encoding="utf-8")

    logger.info("降重完成: 改写 %s 段 / 回退 %s 段 / 跳过 %s 段", len(rewrites), reverted, skipped)
    return {
        "status": "success",
        "output_file": str(output_file),
        "original_file": str(path),
        "intensity": intensity,
        "diff_file": diff_file,
        "stats": {"total": len(unique), "rewritten": len(rewrites), "skipped": skipped, "reverted": reverted},
    }
