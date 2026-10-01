#!/usr/bin/env python3
"""获奖选题检索（本地 JSON，无外部依赖）。

用法：
  python3 topic_search.py 自主游戏
  python3 topic_search.py 游戏 一等奖
  python3 topic_search.py 材料 一等奖 宁波
数据：data/award_topics.json（浙江省教育教学论文评选 2024-2025 幼教获奖选题 1459 条）
"""
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "award_topics.json"


def main():
    args = [a for a in sys.argv[1:] if a]
    if not args:
        print(__doc__)
        sys.exit(1)
    kw = args[0]
    award = next((a for a in args[1:] if "等奖" in a), None)
    city = next((a for a in args[1:] if "等奖" not in a), None)

    data = json.loads(DATA.read_text(encoding="utf-8"))
    hits = [e for e in data if kw in e["title"] or kw in e["unit"]]
    if award:
        hits = [e for e in hits if e["award"] == award]
    if city:
        hits = [e for e in hits if city in e["city"]]
    hits = hits[:20]

    if not hits:
        print(f"未找到匹配「{kw}」的获奖选题")
        return
    print(f"共 {len(hits)} 条（最多显示 20）：")
    for e in hits:
        print(f"  【{e['award']}】《{e['title']}》 {e['city']} {e['year']} | {e['unit']} | {e['authors']}")


if __name__ == "__main__":
    main()
