#!/usr/bin/env python3
"""一键初始化本地知识库（仅标准库，幂等，可重复运行）。

在 ~/paper-kb/（或环境变量 PAPER_KB 指定目录）创建：
  获奖论文/  园本课程/  政策文件/  一般参考/  .drafts/（成稿归档）  .使用说明.txt
用法：python3 init_kb.py
"""
import os
from pathlib import Path

KB_ROOT = Path(os.environ.get("PAPER_KB", str(Path.home() / "paper-kb")))
DIRS = ["获奖论文", "园本课程", "政策文件", "一般参考", ".drafts"]

README = """这是 paper-helper 的本地知识库。

用法：
1. 每个子文件夹 = 一个分类；把你的 Word/PDF/txt 文档放进对应分类
   （新增分类 = 新建一个子文件夹；散放在根目录的文件归"未分类"）
2. 增删文档后运行建索引：
   python3 <skill目录>/scripts/kb_build.py
3. 检索测试：
   python3 <skill目录>/scripts/kb_query.py "观察记录" -k 5

.drafts/ 是成稿归档目录，写作流程会自动把每篇终稿存进来，
用于下一篇选题时比对结构组合与化名，防止论文模式雷同。
"""


def main():
    created = []
    for d in DIRS:
        p = KB_ROOT / d
        if not p.is_dir():
            p.mkdir(parents=True)
            created.append(d)
    readme = KB_ROOT / ".使用说明.txt"   # 隐藏文件不会被 kb_build 收录进索引
    if not readme.exists():
        readme.write_text(README, encoding="utf-8")
        created.append(".使用说明.txt")

    print(f"知识库目录：{KB_ROOT}")
    if created:
        print(f"已创建：{', '.join(created)}")
    else:
        print("目录结构已存在，未做改动（幂等）。")
    print("\n下一步：")
    print("  1. 把你的文档放进上面的分类文件夹")
    print("  2. 运行 kb_build.py 建索引")
    print("  3. 运行 doctor.py 确认全部就绪")


if __name__ == "__main__":
    main()
