"""选题库服务：基于浙江省获奖论文结构化数据，提供筛选检索与 AI 选题建议。"""
import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.prompts import SYSTEM_PROMPT
from app.services.llm_service import get_llm

logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "award_topics.json"

SUGGEST_SYSTEM = SYSTEM_PROMPT + """

你同时是论文选题顾问。你熟悉浙江省幼儿园教师教育教学论文评选的获奖趋势，
善于基于获奖选题的方向与命名规律，为教师推荐既有实践基础又有新意的选题。"""

SUGGEST_PROMPT = """我在准备浙江省幼儿园教育教学论文评选，请帮我选题。

我的方向/兴趣：
{direction}
{extra}

我的园所与学段情况：{background}

以下是近年（2024-2025）浙江省获奖论文中与我方向相关的真实选题，供把握趋势、避免撞题：
{samples}

请给出 5 个选题建议，每个包含：
1. 论文题目（仿照获奖选题的命名风格，可含副标题）
2. 选题理由（为什么这个方向值得写，与获奖趋势的关系）
3. 一个可切入的真实实践场景（具体到活动/材料/年龄段）

要求：
- 题目不与上面获奖选题重复
- 方向对我这样的一线教师可操作，不需要大规模数据
- 输出用清晰的编号列表"""


@lru_cache()
def _load_topics() -> List[dict]:
    if not DATA_FILE.exists():
        logger.warning("选题库数据文件不存在: %s", DATA_FILE)
        return []
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def get_topics(
    keyword: Optional[str] = None,
    year: Optional[str] = None,
    award: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """按条件筛选获奖选题，返回 {total, items}。"""
    items = _load_topics()

    def match(e: dict) -> bool:
        if year and e["year"] != year:
            return False
        if award and e["award"] != award:
            return False
        if city and city not in e["city"]:
            return False
        if keyword:
            kw = keyword.strip()
            if kw and kw not in e["title"] and kw not in e["unit"] and kw not in e["authors"]:
                return False
        return True

    filtered = [e for e in items if match(e)]
    return {"total": len(filtered), "items": filtered[offset:offset + limit]}


def get_facets() -> dict:
    """筛选项的可选值（年份/奖级/城市）"""
    items = _load_topics()
    years = sorted({e["year"] for e in items}, reverse=True)
    awards = ["一等奖", "二等奖", "三等奖"]
    cities = sorted({e["city"] for e in items})
    return {"years": years, "awards": awards, "cities": cities, "total": len(items)}


def _keyword_samples(direction: str, count: int = 12) -> List[dict]:
    """按方向关键词从获奖库中取相似选题样本（简单包含匹配 + 去重）"""
    items = _load_topics()
    # 把方向拆成词，任一词命中标题即相似
    words = [w for w in re.split(r"[，,。、\s]+", direction) if len(w) >= 2]
    scored = []
    for e in items:
        score = sum(1 for w in words if w in e["title"])
        if score:
            scored.append((score, e))
    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:count]]


def suggest_topics(
    direction: str,
    background: Optional[str] = None,
    age_group: Optional[str] = None,
) -> dict:
    """AI 选题建议：基于获奖趋势 + 用户方向生成选题推荐。"""
    direction = (direction or "").strip()
    if not direction:
        return {"success": False, "error": "请先填写你的研究方向或兴趣"}

    samples = _keyword_samples(direction)
    if not samples:
        # 关键词没命中就取一等奖样本，保证趋势参考
        samples = [e for e in _load_topics() if e["award"] == "一等奖"][:10]
    sample_lines = "\n".join(
        f"- 《{e['title']}》（{e['city']}·{e['award']}，{e['year']}）" for e in samples
    )

    extra = f"\n关注的幼儿年龄段：{age_group}" if age_group else ""
    prompt = SUGGEST_PROMPT.format(
        direction=direction,
        extra=extra,
        background=background or "未提供（按普通幼儿园一线教师理解）",
        samples=sample_lines,
    )
    llm = get_llm(temperature=0.7)
    content = llm.invoke([SystemMessage(content=SUGGEST_SYSTEM), HumanMessage(content=prompt)]).content

    return {
        "success": True,
        "suggestion": content,
        "referenced": [
            {"title": e["title"], "city": e["city"], "award": e["award"], "year": e["year"]}
            for e in samples
        ],
    }
