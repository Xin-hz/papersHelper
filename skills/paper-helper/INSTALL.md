# 安装与迁移指南（发给同事看这篇就够了）

paper-helper 分两层：**能力层**（本目录，随仓库分发）+ **数据层**（`~/paper-kb/`，各机器自维护）。
装好能力层 → 初始化自己的知识库 → 跑一次自检，即完成闭环。

---

## 方式一：同事也用 Codex / ZCode / Claude Code（推荐，一句话安装）

**一句话版**——把这句原样发给同事，他们粘贴给自己的 AI 即可：

```
帮我把 GitHub 公开仓库 Xin-hz/papersHelper 里的 skills/paper-helper 技能装到 ~/.agents/skills/（clone 到 /tmp 后整目录拷贝；还用 Claude Code 就再软链一份到 ~/.claude/skills/），运行它的 doctor.py 并按提示把环境修到无 ❌，最后用「帮我选个论文题目，方向是户外自主游戏」验证一遍，并告诉我日常怎么用。
```

Codex 用户可用自带 skill-installer，更短：

```
用 skill-installer 从 GitHub 仓库 Xin-hz/papersHelper 安装 skills/paper-helper 技能，
装完运行 scripts/doctor.py 自检并按提示初始化知识库。
```

**分步版**（一句话没装成时，把这段发给同事的 AI 逐条核对）：

```
请帮我安装 paper-helper 幼儿园论文助手技能：
1. 克隆仓库 git clone https://github.com/Xin-hz/papersHelper.git /tmp/papersHelper
2. 把 /tmp/papersHelper/skills/paper-helper 完整拷贝到 ~/.agents/skills/paper-helper
   （如还用 Claude Code，再软链一份：ln -s ~/.agents/skills/paper-helper ~/.claude/skills/paper-helper）
3. 运行 python3 ~/.agents/skills/paper-helper/scripts/init_kb.py 初始化知识库
4. 运行 python3 ~/.agents/skills/paper-helper/scripts/doctor.py 自检，按提示修复到无 ❌
5. 完成后告诉我用法，并用「帮我选个论文题目，方向是户外自主游戏」测试一遍
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

## 可选：联网检索兜底（Tavily，通常不用配）

本地知识库覆盖不到的主题，技能会联网补公开资料。**用的 AI 宿主自带联网检索（ZCode / Claude Code / Codex 均内置）时无需任何配置**，技能会直接用宿主的检索。Tavily Key 只是无宿主检索环境下 `web_search.py` 脚本的兜底：

```bash
# 如需兜底：到 https://tavily.com 注册 → API Keys → 复制（tvly- 开头），免费额度每月 1000 次
echo "tvly-你的key" > ~/paper-kb/.tavily_key
chmod 600 ~/paper-kb/.tavily_key

# 测试
python3 ~/.agents/skills/paper-helper/scripts/web_search.py "幼儿园户外自主游戏"
```

也可用环境变量 `TAVILY_API_KEY`。各机器配各自的 Key（**不会进 git，别共用**）。

日常使用**不需要记任何命令**——直接对 AI 说「帮我写一篇论文…」「这篇帮我降重」「出评审报告」即可，
技能会自动调用脚本。核心功能零依赖（macOS/Linux 自带 Python 即可），可选项如下。

## 可选依赖总表（doctor.py 会逐项检测）

| 可选项 | 安装 | 不装的影响 |
|---|---|---|
| python-docx | `pip3 install python-docx` | 无法排版 Word（文字流程不受影响） |
| matplotlib | `pip3 install matplotlib` | 无法生成论文配图 |
| poppler（pdftotext） | `brew install poppler` | PDF 入库改由 AI 宿主读 PDF 后存 .txt，等效 |
| LibreOffice + poppler | `brew install --cask libreoffice` + `brew install poppler` | 跳过排版视觉验收，交付前人工查看 Word |
| Tavily Key | 见上一节 | 宿主自带联网检索时用不上；仅纯本地脚本兜底需要 |

## ZCode 用户自动增强（无需额外安装）

同一份技能装在 ZCode 里，以下环节自动升级；用 Claude Code / Codex / WorkBuddy 的同事不受影响，能力按各自宿主取长：

- **联网检索**：直接用 ZCode 内置检索，免配任何 Key；找公开论文可限定百度学术/知网/万方/维普/汉斯
- **改论文**：草稿在文档面板打开，选中一段说"改这段"即可，免整篇粘贴
- **交付**：成稿 Word 在文档面板打开，自动高亮需替换的示范数据段落
- **PDF 入库**：宿主直接读 PDF 存 .txt 入库，免装 poppler
- **评审报告**：五维打分另出交互雷达卡片（文字版仍是交付主体）
- **排版验收**：LibreOffice+poppler 装齐时，成稿逐页渲染交视觉评审代理按评选规范复核

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
→ 撰写 → 自检(check_paper) → Word排版(make_docx) → 视觉验收(render_docx，可选)
→ 归档(.drafts) → 下一篇动笔前 drafts.py 比对近期成稿，防结构/化名雷同
```

遇到问题先跑 `doctor.py`，按提示修；仍不行看 `README.md` 常见问题。
