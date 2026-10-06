#!/usr/bin/env python3
"""paper-helper 环境自检（仅标准库）。装完或换机器后跑一次，确认闭环可用。

用法：
  python3 doctor.py
输出 ✅ 通过 / ⚠️ 提示（不阻断）/ ❌ 失败（需修复）。
核心项全过退出码 0；任何 ❌ 退出码 1。
"""
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
KB_ROOT = Path(os.environ.get("PAPER_KB", str(Path.home() / "paper-kb")))
DB_PATH = KB_ROOT / ".index.db"

results = []  # (level, name, detail, fix)


def ok(name, detail=""):
    results.append(("ok", name, detail, ""))


def warn(name, detail, fix):
    results.append(("warn", name, detail, fix))


def fail(name, detail, fix):
    results.append(("fail", name, detail, fix))


# ---------- 1 运行环境 ----------
if sys.version_info >= (3, 8):
    ok(f"Python {sys.version_info.major}.{sys.version_info.minor}（≥3.8）")
else:
    fail(f"Python 版本过低（{sys.version_info.major}.{sys.version_info.minor}）",
         "脚本需要 3.8+", "安装 Python 3.8+ 后重试")

# ---------- 2 技能文件完整性 ----------
need_files = ["SKILL.md", "README.md", "INSTALL.md",
              "data/award_topics.json", "prompts/写作参考卡.md", "prompts/评审模板.md"]
missing = [f for f in need_files if not (SKILL / f).is_file()]
if missing:
    fail("技能文件完整", f"缺失：{missing}", "重新拷贝完整的 paper-helper 目录")
else:
    ok("技能文件完整（6 个核心文件在位）")

# ---------- 3 获奖选题数据 ----------
try:
    data = json.loads((SKILL / "data" / "award_topics.json").read_text(encoding="utf-8"))
    ok(f"获奖选题数据可解析（{len(data)} 条）")
except Exception as e:
    fail("获奖选题数据", str(e)[:80], "重新拷贝 data/award_topics.json")

# ---------- 4 脚本可运行 ----------
for s in ["kb_build.py", "kb_query.py", "topic_search.py",
          "check_paper.py", "make_docx.py", "init_kb.py", "drafts.py"]:
    p = SKILL / "scripts" / s
    try:
        compile(p.read_text(encoding="utf-8"), str(p), "exec")  # 仅语法检查，不产生 __pycache__
        ok(f"脚本可编译：{s}")
    except Exception as e:
        fail(f"脚本可编译：{s}", str(e)[:80], "检查文件是否损坏")

# ---------- 5 可选依赖 ----------
if importlib.util.find_spec("docx"):
    ok("python-docx 已安装（Word 排版可用）")
else:
    warn("python-docx 未安装", "make_docx.py 排版 Word 需要", "pip3 install python-docx")
if importlib.util.find_spec("matplotlib"):
    ok("matplotlib 已安装（配图可用）")
else:
    warn("matplotlib 未安装", "仅影响论文配图，不影响文字流程", "pip3 install matplotlib")

# ---------- 6 文档格式支持 ----------
if sys.platform == "darwin":
    ok("macOS：.doc 经 textutil 转换支持")
else:
    warn("非 macOS", "老式 .doc 文档不被支持", "先另存为 .docx 再入库")
if shutil.which("pdftotext"):
    ok("pdftotext 已安装（PDF 入库可用）")
else:
    warn("pdftotext 未安装", "PDF 文档无法提取文字", "brew install poppler（或 apt install poppler-utils）")

# ---------- 6b 联网检索（可选） ----------
if os.environ.get("TAVILY_API_KEY", "").strip() or (KB_ROOT / ".tavily_key").is_file():
    ok("Tavily 已配置（知识库缺资料时可联网补充）")
else:
    warn("Tavily 未配置", "本地知识库无相关内容时无法联网补公开资料（可选）",
         "tavily.com 免费申请后：echo tvly-你的key > ~/paper-kb/.tavily_key")

# ---------- 7 知识库 ----------
if not KB_ROOT.is_dir():
    warn("知识库目录不存在", str(KB_ROOT), f"python3 \"{SKILL}/scripts/init_kb.py\" 一键初始化")
else:
    ok(f"知识库目录：{KB_ROOT}")
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(DB_PATH)
            n = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            conn.close()
            if n:
                ok(f"索引就绪（{n} 个文本块）")
            else:
                warn("索引为空", "尚未收录任何文档",
                     f"把文档放入分类子文件夹后运行 \"{SKILL}/scripts/kb_build.py\"")
        except Exception as e:
            fail("索引读取", str(e)[:80], "删除 .index.db 后重跑 kb_build.py")
    else:
        warn("索引未构建", "知识库里还没有 .index.db",
             f"python3 \"{SKILL}/scripts/kb_build.py\"")

# ---------- 8 冒烟测试 ----------
try:
    r = subprocess.run([sys.executable, str(SKILL / "scripts" / "topic_search.py"), "游戏"],
                       capture_output=True, text=True, timeout=15)
    if r.returncode == 0 and ("条" in r.stdout or "未找到" in r.stdout):
        ok("选题检索冒烟测试通过")
    else:
        fail("选题检索冒烟测试", (r.stderr or r.stdout)[:80], "查看上方报错")
except Exception as e:
    fail("选题检索冒烟测试", str(e)[:80], "")
if DB_PATH.exists():
    try:
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "kb_query.py"), "幼儿", "-k", "1"],
                           capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            ok("知识库检索冒烟测试通过")
        else:
            fail("知识库检索冒烟测试", (r.stderr or r.stdout)[:80], "重跑 kb_build.py")
    except Exception as e:
        fail("知识库检索冒烟测试", str(e)[:80], "")

# ---------- 输出 ----------
icons = {"ok": "✅", "warn": "⚠️ ", "fail": "❌"}
n_fail = sum(1 for r in results if r[0] == "fail")
n_warn = sum(1 for r in results if r[0] == "warn")
for level, name, detail, fix in results:
    line = f"{icons[level]} {name}" + (f"  —— {detail}" if detail else "")
    print(line)
    if fix:
        print(f"      修复：{fix}")
print(f"\n结论：{'核心功能全部就绪' if n_fail == 0 else f'{n_fail} 项失败，需修复'}"
      + (f"；{n_warn} 项提示" if n_warn else ""))
if n_fail == 0 and n_warn == 0:
    print("可直接对 AI 说：「帮我选个论文题目，方向是户外自主游戏」试用。")
sys.exit(1 if n_fail else 0)
