#!/usr/bin/env python3
"""联网检索公开资料（Tavily，仅标准库）。本地知识库命中不足时使用，引用必须注明来源。

用法：
  python3 web_search.py "幼儿园 户外自主游戏 指导策略"
  python3 web_search.py "低结构材料 投放" -k 3 --depth advanced --no-answer
  python3 web_search.py "幼小衔接 规则意识" --paper        # 学术模式：限定学术站点找论文
  python3 web_search.py "观察记录" --domain hanspub.org    # 自定义限定站点（可重复）

Key 读取顺序：环境变量 TAVILY_API_KEY > ~/paper-kb/.tavily_key（每台机器自配，勿入 git）
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# 学术模式预设站点（开放获取 + 学术聚合/库；知网/万方/维普付费全文仍需人工去库下载）
PAPER_DOMAINS = ["xueshu.baidu.com", "cnki.net", "wanfangdata.com.cn", "cqvip.com", "hanspub.org"]


def get_key():
    key = os.environ.get("TAVILY_API_KEY", "").strip()
    if key:
        return key
    kf = Path(os.environ.get("PAPER_KB", str(Path.home() / "paper-kb"))) / ".tavily_key"
    if kf.is_file():
        return kf.read_text(encoding="utf-8").strip()
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="检索词")
    ap.add_argument("-k", "--top", type=int, default=5, help="结果条数（默认 5）")
    ap.add_argument("--depth", choices=["basic", "advanced"], default="basic",
                    help="检索深度（advanced 更准更慢，默认 basic）")
    ap.add_argument("--no-answer", action="store_true", help="不请求 AI 摘要，只要来源列表")
    ap.add_argument("--paper", action="store_true",
                    help="学术模式：限定百度学术/知网/万方/维普/汉斯等学术站点检索论文")
    ap.add_argument("--domain", action="append", default=[], metavar="SITE",
                    help="限定站点（可重复使用），如 --domain hanspub.org")
    args = ap.parse_args()

    key = get_key()
    if not key:
        print("未配置 Tavily Key。两种方式任选（Key 不会进入 git）：\n"
              "  echo \"tvly-你的key\" > ~/paper-kb/.tavily_key\n"
              "  或设环境变量 TAVILY_API_KEY\n"
              "免费申请：https://tavily.com（每月 1000 次额度）", file=sys.stderr)
        sys.exit(2)

    domains = list(args.domain) + (PAPER_DOMAINS if args.paper else [])
    payload = {
        "query": args.query,
        "search_depth": args.depth,
        "max_results": max(1, min(args.top, 10)),
        "include_answer": not args.no_answer,
    }
    if domains:
        payload["include_domains"] = domains
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:200]
        if e.code == 401:
            print(f"Key 无效（401）：请到 tavily.com 重新生成。{detail}", file=sys.stderr)
        elif e.code in (429, 432):
            print(f"额度不足/限流（{e.code}）：免费版每月 1000 次。{detail}", file=sys.stderr)
        else:
            print(f"Tavily 请求失败（HTTP {e.code}）：{detail}", file=sys.stderr)
        sys.exit(1)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"网络错误：{e}\n请检查网络后重试；断网时只用本地知识库。", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("Tavily 返回了无法解析的内容。", file=sys.stderr)
        sys.exit(1)

    answer = (data.get("answer") or "").strip()
    results = data.get("results") or []
    if not results and not answer:
        print("联网检索无结果，请换关键词。")
        return
    if answer:
        print(f"【AI 摘要】{answer}\n")
    if results:
        print(f"【来源】共 {len(results)} 条（写入论文时须注明出处）：")
        for i, r in enumerate(results, 1):
            title = (r.get("title") or "（无标题）").strip()
            url = (r.get("url") or "").strip()
            content = " ".join((r.get("content") or "").split())[:220]
            print(f"\n[{i}] {title}\n    {url}\n    {content}")


if __name__ == "__main__":
    main()
