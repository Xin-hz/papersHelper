"""图文排版论文生成：事实底座 → 分节撰写 → matplotlib 图表 → 按评选规范排版 docx。

产出与手动流水线（papers_output 范文）同规格：
标题黑体小二居中、署名填写线、摘要/关键词楷体、正文宋体小四 1.5 倍行距、
一级标题黑体四号、二级黑体小四、三线表（表题在上）、图题在下、
参考文献 GB/T 7714（指南 + 知识库真实文献，不虚构）。
"""
import json
import logging
import re
import tempfile
from pathlib import Path
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.prompts import SYSTEM_PROMPT
from app.services.llm_service import get_llm
from app.services.rag_service import retrieve_for_writing

logger = logging.getLogger(__name__)

DOC_SYSTEM = SYSTEM_PROMPT + """

你同时熟悉浙江省教育教学论文评选的写作规范：观点明晰、逻辑严谨、文从字顺，
正文不超过 4000 字，案例具体（幼儿化名、材料、动作、语言），数据表述克制。"""

FACTS_PROMPT = """为一篇幼儿园实践研究论文设计"研究事实底座"（所有章节、表格、图表的数据必须与此一致）。

论文题目：《{title}》
研究方向：{direction}

要求按行动研究范式设计，数据保守合理。只输出 JSON（不要 markdown 代码块、不要解释）：
{{
  "object_desc": "研究对象一句话（如：杭州市某幼儿园中班两个班共 48 名 4—5 岁幼儿）",
  "period_desc": "研究周期一句话（如：2025 年 9 月至 12 月共 12 周，前 4 周现状观察，后 8 周干预）",
  "methods": "研究方法一句话（观察法+行动研究法等）",
  "problem": "干预前存在的 2-3 个具体问题，每条一句话",
  "strategies": [
    {{"name": "策略名（12-20字，动宾结构）", "point": "策略要点一句话", "case": "具体案例一句话（含幼儿化名与材料）"}}
  ],
  "behavior_chart": {{
    "title": "前后测对比维度名（如：游戏行为水平）",
    "categories": ["维度1", "维度2", "维度3"],
    "pre": [百分比1, 百分比2, 百分比3],
    "post": [百分比1, 百分比2, 百分比3],
    "note": "前后测人数说明（如 N=48）"
  }},
  "trend_chart": {{
    "title": "趋势指标名（如：单次游戏平均持续时间（分钟））",
    "points": ["第4周", "第6周", "第8周", "第10周", "第12周"],
    "values": [数值递变的5个数],
    "note": "一句话说明"
  }},
  "table": {{
    "caption": "表1标题（实践清单类）",
    "header": ["列1", "列2", "列3"],
    "rows": [["...", "...", "..."], ["...", "...", "..."], ["...", "...", "..."]]
  }},
  "extra_stat": "一项附加成效数据（如：以物代物行为每周由 9 例增至 31 例）"
}}

注意：pre/post 各 3 个百分比之和为 100；trend values 单调或平稳递变；categories 与论文主题相关。
字符串内不要使用任何英文双引号（如需强调用「」），确保输出是严格合法的 JSON。"""


def _repair_json(text: str) -> str:
    """修复字符串内未转义引号导致的 JSON 损坏：
    扫描每个引号，若其后（跳过空白）不是 , } ] : 或结尾，则视为字符串内部引号并转义。"""
    out = []
    in_str = False
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if not in_str:
            if c == '"':
                in_str = True
            out.append(c)
        else:
            if c == "\\" and i + 1 < n:
                out.append(c)
                out.append(text[i + 1])
                i += 1
            elif c == '"':
                j = i + 1
                while j < n and text[j] in " \t\r\n":
                    j += 1
                if j >= n or text[j] in ",}]:":
                    in_str = False
                    out.append(c)
                else:
                    out.append('\\"')
            else:
                out.append(c)
        i += 1
    return "".join(out)


def _try_parse_facts(raw: str) -> dict:
    """容错解析事实底座 JSON（处理代码块包裹、字符串内未转义引号、缺右括号）"""
    text = str(raw).strip()
    text = re.sub(r"^```(json)?\s*|\s*```$", "", text, flags=re.M)
    start, end = text.find("{"), text.rfind("}")
    if start < 0:
        raise ValueError("输出中未找到 JSON")
    text = text[start:end + 1]
    for candidate in (text, _repair_json(text), text + "}", _repair_json(text) + "}"):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError("JSON 解析失败")


def _validate_facts(data: dict):
    assert len(data["strategies"]) >= 3, "策略少于 3 条"
    assert len(data["behavior_chart"]["categories"]) == 3
    assert len(data["trend_chart"]["values"]) == 5
    assert len(data["table"]["rows"]) >= 2


def _gen_facts(llm, title: str, direction: str) -> dict:
    prompt = FACTS_PROMPT.format(title=title, direction=direction or "不限定")
    last_err = None
    for attempt in range(3):
        raw = llm.invoke([
            SystemMessage(content=DOC_SYSTEM),
            HumanMessage(content=prompt + ("" if attempt == 0 else "\n\n上次输出解析失败，请输出严格合法的 JSON。")),
        ]).content
        try:
            data = _try_parse_facts(raw)
            _validate_facts(data)
            return data
        except (ValueError, KeyError, AssertionError, json.JSONDecodeError) as e:
            last_err = e
            logger.warning("事实底座第 %d 次解析失败: %s", attempt + 1, e)
    raise ValueError(f"研究事实底座生成失败（已重试 3 次）: {last_err}")

SECTION_BRIEFS = [
    {
        "key": "problem",
        "heading": "一、问题的提出",
        "brief": "约 400 字。从《3—6岁儿童学习与发展指南》相关要求切入，用事实底座中的 problem 描述本园现状（具体到幼儿行为），引出研究问题。结尾自然过渡。",
    },
    {
        "key": "strategy",
        "heading": "二、实践策略",
        "brief": "约 1500 字，全文核心。按事实底座 strategies 逐条展开为（一）（二）（三）小节：每节先讲做法要点，再给 1 个具体案例（幼儿化名、动作、语言）。其中一节需自然提到「见表1」。",
    },
    {
        "key": "effect",
        "heading": "三、实践成效",
        "brief": "约 500 字。分（一）（二）（三）：社会性/核心维度提升（引用图1，用 behavior_chart 数据）；投入度/趋势指标（引用图2，用 trend_chart 数据）；附加成效（用 extra_stat）。数据保守克制，可指出一项未显著变化的指标并解释。开头自然提到材料或环境的变化。",
    },
    {
        "key": "reflect",
        "heading": "四、结语",
        "brief": "约 250 字。总结策略价值；诚实指出局限（样本范围、观察者主观性、周期）；提出后续方向。不用口号式结尾。",
    },
]

SECTION_PROMPT = """撰写论文《{title}》中的「{heading}」一节（第 {index}/{total} 节）。

研究事实底座（所有数字必须与此一致，不得改动）：
{facts}

本节写作要求：
{brief}

参考知识库片段（同行真实研究资料，观点可借鉴，不要抄原文）：
{context}

要求：直接输出本节正文（含（一）（二）小标题行，不要重复一级标题，不用 Markdown 符号）；数字与底座严格一致；语言符合一线教师实践研究论文文风。"""

ABSTRACT_PROMPT = """基于以下论文正文撰写摘要与关键词。摘要 180—220 字，概括研究问题、方法（含样本与周期）、核心策略、主要成效数据；关键词 4 个。
输出格式：
摘要：……
关键词：……；……；……；……

论文正文：
{body}"""


# ---------- 事实底座 ----------

def _facts_text(facts: dict) -> str:
    bc, tc = facts["behavior_chart"], facts["trend_chart"]
    lines = [
        f"研究对象：{facts['object_desc']}",
        f"研究周期：{facts['period_desc']}",
        f"研究方法：{facts['methods']}",
        "干预前问题：" + "；".join(facts["problem"]),
        "策略：",
    ]
    for i, s in enumerate(facts["strategies"][:3], 1):
        lines.append(f"  {i}. {s['name']}：{s['point']} 案例：{s['case']}")
    lines += [
        f"前后测对比（{bc['title']}，{bc['note']}）：",
        f"  类别：{'、'.join(bc['categories'])}",
        f"  前测：{'、'.join(str(x) for x in bc['pre'])}",
        f"  后测：{'、'.join(str(x) for x in bc['post'])}",
        f"趋势指标（{tc['title']}）：{'、'.join(tc['points'])} 对应 {'、'.join(str(v) for v in tc['values'])}（{tc['note']}）",
        f"表1：{facts['table']['caption']}，表头 {'/'.join(facts['table']['header'])}，共 {len(facts['table']['rows'])} 行",
        f"附加成效：{facts['extra_stat']}",
    ]
    return "\n".join(lines)


# ---------- 图表 ----------

def _make_charts(facts: dict, out_dir: Path) -> List[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Songti SC", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False
    gray1, gray2 = "#4C4C4C", "#A6A6A6"

    paths = []
    bc, tc = facts["behavior_chart"], facts["trend_chart"]

    fig, ax = plt.subplots(figsize=(5.6, 3.2), dpi=200)
    x = range(3)
    w = 0.32
    b1 = ax.bar([i - w / 2 for i in x], bc["pre"], w, label="前测", color=gray2, edgecolor="black", linewidth=0.6)
    b2 = ax.bar([i + w / 2 for i in x], bc["post"], w, label="后测", color=gray1, edgecolor="black", linewidth=0.6)
    for bars in (b1, b2):
        for r in bars:
            ax.annotate(f"{r.get_height():.1f}%", (r.get_x() + r.get_width() / 2, r.get_height()),
                        textcoords="offset points", xytext=(0, 2), ha="center", fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(bc["categories"], fontsize=10)
    ax.set_ylabel("人数占比（%）", fontsize=9)
    ax.set_ylim(0, max(bc["pre"] + bc["post"]) * 1.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.6)
    ax.legend(fontsize=8.5, frameon=False)
    plt.tight_layout()
    p1 = out_dir / "chart1.png"
    plt.savefig(p1, bbox_inches="tight")
    plt.close()
    paths.append(p1)

    fig, ax = plt.subplots(figsize=(5.6, 3.0), dpi=200)
    ax.plot(tc["points"], tc["values"], marker="o", color=gray1, linewidth=1.4, markersize=4.5)
    for xx, yy in zip(tc["points"], tc["values"]):
        ax.annotate(f"{yy}", (xx, yy), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
    ax.set_ylabel(tc["title"], fontsize=9)
    ax.set_ylim(min(tc["values"]) * 0.75, max(tc["values"]) * 1.2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.6)
    plt.tight_layout()
    p2 = out_dir / "chart2.png"
    plt.savefig(p2, bbox_inches="tight")
    plt.close()
    paths.append(p2)
    return paths


# ---------- docx 排版 ----------

from docx import Document as DocxDocument
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn


def _set_font(run, east: str, size_pt: float, bold=False):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), east)
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)


def _para(doc, text, east="宋体", size=12, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
          indent_chars=2.0, line_spacing=1.5, before=0, after=0, superscript_refs=False):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    if indent_chars:
        pf.first_line_indent = Pt(size * indent_chars)
    pf.line_spacing = line_spacing
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    if superscript_refs:
        # 拆出 [n] 引用标记设为上标
        parts = re.split(r"(\[\d\])", text)
        for part in parts:
            r = p.add_run(part)
            _set_font(r, east, size, bold)
            if re.fullmatch(r"\[\d\]", part):
                r.font.superscript = True
                r.font.size = Pt(size - 4)
    else:
        r = p.add_run(text)
        _set_font(r, east, size, bold)
    return p


def _three_line_table(doc, caption: str, header: List[str], rows: List[List[str]]):
    _para(doc, caption, east="宋体", size=10.5, bold=True,
          align=WD_ALIGN_PARAGRAPH.CENTER, indent_chars=0, before=6, after=4)
    table = doc.add_table(rows=1 + len(rows), cols=len(header))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # 三线表边框：仅顶线/底线粗，表头下细线
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = tblPr.makeelement(qn("w:tblBorders"), {})
    for tag, sz in (("top", "12"), ("bottom", "12")):
        el = borders.makeelement(qn(f"w:{tag}"), {qn("w:val"): "single", qn("w:sz"): sz, qn("w:color"): "000000"})
        borders.append(el)
    for tag in ("left", "right", "insideH", "insideV"):
        el = borders.makeelement(qn(f"w:{tag}"), {qn("w:val"): "none"})
        borders.append(el)
    tblPr.append(borders)

    def fill(cell, text, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER):
        cell.paragraphs[0].text = ""
        p = cell.paragraphs[0]
        p.alignment = align
        p.paragraph_format.line_spacing = 1.2
        r = p.add_run(text)
        _set_font(r, "宋体", 10.5, bold)
        # 表头下细线
        if bold:
            tcPr = cell._tc.get_or_add_tcPr()
            tcB = tcPr.makeelement(qn("w:tcBorders"), {})
            el = tcB.makeelement(qn("w:bottom"), {qn("w:val"): "single", qn("w:sz"): "6", qn("w:color"): "000000"})
            tcB.append(el)
            tcPr.append(tcB)

    for j, h in enumerate(header):
        fill(table.rows[0].cells[j], h, bold=True)
    for i, row in enumerate(rows, 1):
        for j, v in enumerate(row):
            fill(table.rows[i].cells[j], v)


def _build_docx(title: str, abstract: str, sections: List[dict], facts: dict,
                chart_paths: List[Path], refs: List[str], out_path: Path):
    doc = DocxDocument()
    # A4 页边距（学术规范）
    sec = doc.sections[0]
    sec.top_margin = Cm(2.54)
    sec.bottom_margin = Cm(2.54)
    sec.left_margin = Cm(3.0)
    sec.right_margin = Cm(2.5)

    # 标题 + 署名填写线
    _para(doc, title, east="黑体", size=18, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
          indent_chars=0, line_spacing=1.3, after=6)
    _para(doc, "（单位：＿＿＿＿＿＿＿＿　　作者：＿＿＿＿）", east="楷体", size=12,
          align=WD_ALIGN_PARAGRAPH.CENTER, indent_chars=0, after=8)

    # 摘要与关键词
    for line in abstract.split("\n"):
        line = line.strip()
        if line.startswith("摘要"):
            _para(doc, "摘要：" + line.split("：", 1)[-1], east="楷体", size=10.5, line_spacing=1.25)
        elif line.startswith("关键词"):
            _para(doc, "关键词：" + line.split("：", 1)[-1], east="楷体", size=10.5,
                  line_spacing=1.25, after=10)

    table_inserted = False
    for s_i, sec_data in enumerate(sections):
        _para(doc, sec_data["heading"], east="黑体", size=14, bold=True,
              align=WD_ALIGN_PARAGRAPH.LEFT, indent_chars=0, before=10, after=6)
        for line in sec_data["text"].split("\n"):
            line = line.strip()
            if not line:
                continue
            if re.match(r"^[（(][一二三四五六]", line) and len(line) < 40:
                _para(doc, line, east="黑体", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT,
                      indent_chars=0, before=6, after=4)
                continue
            _para(doc, line, superscript_refs=True)
            # 表1 紧随策略节中（二）小节前
        if sec_data["key"] == "strategy" and not table_inserted:
            t = facts["table"]
            _three_line_table(doc, t["caption"], t["header"], t["rows"])
            table_inserted = True

    # 图（成效节末尾）
    captions = [
        f"图1  前后测{facts['behavior_chart']['title']}对比（{facts['behavior_chart']['note']}）",
        f"图2  {facts['trend_chart']['title']}变化趋势",
    ]
    for path, cap in zip(chart_paths, captions):
        doc.add_picture(str(path), width=Cm(13.5))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        _para(doc, cap, east="宋体", size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER,
              indent_chars=0, before=2, after=8)

    # 参考文献
    _para(doc, "参考文献", east="黑体", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT,
          indent_chars=0, before=12, after=6)
    for i, r in enumerate(refs, 1):
        p = _para(doc, f"[{i}] {r}", east="宋体", size=10.5, align=WD_ALIGN_PARAGRAPH.LEFT,
                  indent_chars=0, line_spacing=1.25)
        p.paragraph_format.left_indent = Pt(21)
        p.paragraph_format.first_line_indent = Pt(-21)

    doc.save(str(out_path))


# ---------- 主流程 ----------

def generate_paper_docx(
    title: str,
    direction: Optional[str] = None,
    use_rag: bool = True,
) -> dict:
    """生成图文排版论文 docx，返回 {file, filename, stats}。"""
    llm = get_llm(temperature=0.6)

    # 1. 研究事实底座
    facts = _gen_facts(llm, title, direction)
    facts_str = _facts_text(facts)

    # 2. 分节撰写（并行）
    prompts = []
    kb_refs: List[str] = []
    for idx, sec in enumerate(SECTION_BRIEFS):
        docs = retrieve_for_writing(f"{title} {sec['heading']}", top_k=4) if use_rag else []
        context = "\n\n---\n\n".join(d.page_content for d in docs) if docs else "（未检索到相关资料）"
        for d in docs:
            name = (d.metadata or {}).get("source") or (d.metadata or {}).get("title")
            if name and str(name).lower() != "none" and str(name) not in kb_refs:
                kb_refs.append(str(name))
        prompts.append([
            SystemMessage(content=DOC_SYSTEM),
            HumanMessage(content=SECTION_PROMPT.format(
                title=title, heading=sec["heading"], index=idx + 1, total=len(SECTION_BRIEFS),
                facts=facts_str, brief=sec["brief"], context=context,
            )),
        ])
    results = llm.batch(prompts, config={"max_concurrency": 4})
    sections = []
    for sec, r in zip(SECTION_BRIEFS, results):
        text = str(r.content or "").strip()
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
        # 统一小节标题行（去可能的编号重复）
        sections.append({"key": sec["key"], "heading": sec["heading"], "text": text})

    # 3. 摘要
    body = "\n\n".join(s["text"] for s in sections)
    abstract = str(llm.invoke([
        SystemMessage(content=DOC_SYSTEM),
        HumanMessage(content=ABSTRACT_PROMPT.format(body=body[:5000])),
    ]).content or "").strip()

    # 4. 图表
    with tempfile.TemporaryDirectory() as td:
        chart_paths = _make_charts(facts, Path(td))

        # 5. 参考文献：指南 + 知识库真实文献（不虚构）
        refs = ["中华人民共和国教育部. 3—6岁儿童学习与发展指南[Z]. 北京: 首都师范大学出版社, 2012."]
        refs += [f"{name}（本园实践资料）" for name in kb_refs[:4]]

        # 6. 排版输出
        out_dir = Path("knowledge_uploads/temp")
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_title = re.sub(r'[\\/:*?"<>|]', "_", title)[:40]
        out_path = out_dir / f"{safe_title}_图文版.docx"
        _build_docx(title, abstract, sections, facts, chart_paths, refs, out_path)

    logger.info("图文论文已生成: %s（正文约 %d 字）", out_path, len(body))
    return {
        "file": str(out_path),
        "filename": out_path.name,
        "words": len(body),
        "stats": {"sections": len(sections), "charts": 2, "table": 1, "refs": len(refs)},
    }
