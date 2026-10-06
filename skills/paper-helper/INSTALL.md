# 安装与迁移指南（发给同事看这篇就够了）

paper-helper 分两层：**能力层**（本目录，随仓库分发）+ **数据层**（`~/paper-kb/`，各机器自维护）。
装好能力层 → 初始化自己的知识库 → 跑一次自检，即完成闭环。

---

## 方式一：同事也用 Codex / ZCode / Claude Code（推荐，一句话安装）

把下面这段话**原样发给同事**，让他们粘贴给自己的 AI：

```
请帮我安装 paper-helper 幼儿园论文助手技能：
1. 克隆仓库 git clone https://github.com/Xin-hz/papersHelper.git /tmp/papersHelper
2. 把 /tmp/papersHelper/skills/paper-helper 完整拷贝到 ~/.agents/skills/paper-helper
   （如还用 Claude Code，再软链一份：ln -s ~/.agents/skills/paper-helper ~/.claude/skills/paper-helper）
3. 运行 python3 ~/.agents/skills/paper-helper/scripts/init_kb.py 初始化知识库
4. 运行 python3 ~/.agents/skills/paper-helper/scripts/doctor.py 自检，按提示修复到无 ❌
5. 完成后告诉我用法，并用「帮我选个论文题目，方向是户外自主游戏」测试一遍
```

Codex 用户更简单，一句即可：

```
用 skill-installer 从 GitHub 仓库 Xin-hz/papersHelper 安装 skills/paper-helper 技能，
装完运行 scripts/doctor.py 自检并按提示初始化知识库。
```

> 仓库是公开的，同事无需任何 GitHub 权限，克隆即可。

## 方式二：同事用 WorkBuddy 等纯提示词产品（无本地文件能力）

把 [`prompts/一键导入提示词.md`](prompts/一键导入提示词.md) 分隔线内的全部内容粘贴到
“角色设定/系统提示词”；若产品支持上传知识文件，把 `data/award_topics.json` 一并上传。
此路径只有写作/改稿智能，没有本地知识库、自检和 Word 排版脚本。

## 方式三：离线拷贝（无 GitHub 访问）

1. 把本目录 `paper-helper/` 整个打包发给同事（ZIP / U盘 / 微信传文件）
2. 同事解压到任意固定位置，如 `~/tools/paper-helper`
3. 执行：
   ```bash
   mkdir -p ~/.agents/skills
   cp -R ~/tools/paper-helper ~/.agents/skills/paper-helper   # 拷贝而非软链，独立于原目录
   python3 ~/.agents/skills/paper-helper/scripts/init_kb.py
   python3 ~/.agents/skills/paper-helper/scripts/doctor.py
   ```

---

## 装完之后（每台机器一次，约 2 分钟）

```bash
# 1. 初始化知识库目录（幂等）
python3 ~/.agents/skills/paper-helper/scripts/init_kb.py

# 2. 把自己的文档放进 ~/paper-kb/ 下的分类文件夹（获奖论文/园本课程/政策文件/一般参考）

# 3. 建索引
python3 ~/.agents/skills/paper-helper/scripts/kb_build.py

# 4. 自检：全部 ✅/⚠️ 且无 ❌ 即就绪
python3 ~/.agents/skills/paper-helper/scripts/doctor.py
```

## 可选：联网检索（Tavily，推荐每人配一个）

本地知识库覆盖不到的主题，技能会联网补公开资料。免费额度每月 1000 次，各机器配各自的 Key（**不会进 git，别共用**）：

```bash
# 1. 到 https://tavily.com 注册 → API Keys → 复制（tvly- 开头）
echo "tvly-你的key" > ~/paper-kb/.tavily_key
chmod 600 ~/paper-kb/.tavily_key

# 2. 测试
python3 ~/.agents/skills/paper-helper/scripts/web_search.py "幼儿园户外自主游戏"
```

也可用环境变量 `TAVILY_API_KEY`。不配置不影响其他功能，只是知识库缺资料时退化为"如实说明并建议补充文档"。

日常使用**不需要记任何命令**——直接对 AI 说「帮我写一篇论文…」「这篇帮我降重」「出评审报告」即可，
技能会自动调用脚本。依赖：核心功能零依赖（macOS/Linux 自带 Python 即可）；
Word 排版需 `pip3 install python-docx`；配图另需 matplotlib；PDF 入库需 pdftotext（doctor 会逐项提示）。

## 升级技能（不影响各自的知识库数据）

```bash
git -C /tmp/papersHelper pull          # 或重新拷贝新版目录
cp -R /tmp/papersHelper/skills/paper-helper/. ~/.agents/skills/paper-helper/
python3 ~/.agents/skills/paper-helper/scripts/doctor.py
```

知识库在 `~/paper-kb/`，与技能目录分离，升级覆盖技能不会动数据。

## 闭环链路（装好后自动生效）

```
选题查重(topic_search) → 知识库检索(kb_query) → 结构选型(写作参考卡)
→ 撰写 → 自检(check_paper) → Word排版(make_docx) → 归档(.drafts)
→ 下一篇动笔前 drafts.py 比对近期成稿，防结构/化名雷同
```

遇到问题先跑 `doctor.py`，按提示修；仍不行看 `README.md` 常见问题。
