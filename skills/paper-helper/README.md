# paper-helper 使用手册

幼儿园教师论文写作与修改助手。**能力随本 skill 分发，知识库数据各机器自维护，断网可用。**

---

## 一、它是什么

一个装进 ZCode / Claude Code 的论文助手 skill，包含两条经过实战打磨的工作流：

- **写论文**（四步）：借鉴获奖选题 → 检索本地知识库 → 生成提纲 → 补充素材正式撰写
- **改论文**（四操作）：按意见优化 / 三档降重 / 评审报告（五维打分）/ 按评审建议修改

内置资产：浙江省 2024-2025 幼教获奖选题 **1459 条**（查重与趋势参考）、评选规范 Word 排版器（黑体标题/宋体正文/三线表/GB/T 7714 文献）、评审报告模板。

## 二、安装（每台机器一次，约 2 分钟）

**最快路径：把 [INSTALL.md](INSTALL.md) 方式一的那段安装提示词原样发给同事**，让他们粘贴给自己的 AI 即可。
也可按下述手动安装，或用 WorkBuddy 纯提示词版（见 `prompts/一键导入提示词.md`）。

```bash
# 1. 拿到本文件夹（拷贝或 git clone 整个 paper-helper/）

# 2. 软链为 CLI 的 skill
mkdir -p ~/.agents/skills ~/.claude/skills
ln -s /软件所在路径/paper-helper ~/.agents/skills/paper-helper
ln -s /软件所在路径/paper-helper ~/.claude/skills/paper-helper   # 用 Claude Code 的话

# 3. 建自己的知识库
python3 /软件所在路径/paper-helper/scripts/init_kb.py
#    把自己的文档（Word/PDF/txt）放进分类文件夹，然后建索引：
python3 /软件所在路径/paper-helper/scripts/kb_build.py
python3 /软件所在路径/paper-helper/scripts/doctor.py   # 自检到无 ❌
```

**依赖**：核心功能零依赖（Python 3.8+ 自带 SQLite）。排版 Word 需 `pip3 install python-docx`，配图另需 matplotlib。
联网检索（可选）：到 [tavily.com](https://tavily.com) 免费申请 Key（每月 1000 次）后执行
`echo "tvly-你的key" > ~/paper-kb/.tavily_key`——本地知识库缺资料时自动联网补充，不配也能用。

## 三、日常怎么用（对 CLI 说人话即可）

### 写一篇论文

> **你**："帮我写一篇论文，题目是《××××》"
> （没想好题目就说"帮我选个题"，会基于获奖数据推荐并查重）

流程会走：给候选题目 → 检索你的知识库展示素材 → 出提纲给你改 → **问你要真实素材**（班级人数、真实数据、亲历案例——提供了就不像 AI 文）→ 分章撰写 → 排版成评选规范的 Word 并自动打开。

### 改一篇论文

> **你**："这篇论文帮我优化一下，第二部分太薄、结论别口号化"（贴文本或给文件路径）
> **你**："这段帮我降重" / "给这篇论文出评审报告" / "按评审建议改"

- 优化：按你的意见逐条落实
- 降重：轻/中/重三档，数字引用原样保留
- 评审：模拟评委出报告——总体评价、五维打分（50 分制）、问题清单、修改建议、水平判断
- 按建议改：逐条落实并交代"意见→落实"对照

### 维护知识库

> **你**："把 xx.docx 加进知识库'园本课程'分类"

或自己动手：

```bash
cp 我的论文.docx ~/paper-kb/园本课程/
python3 ~/.../paper-helper/scripts/kb_build.py        # 增删文档后重建索引
python3 ~/.../paper-helper/scripts/kb_query.py "观察记录" -c 园本课程   # 手动检索
```

## 四、脚本速查

| 脚本 | 用途 | 示例 |
|---|---|---|
| `kb_build.py` | 建索引（子文件夹=分类，自动过滤扫描版/乱码） | `python3 kb_build.py` |
| `kb_query.py` | 检索（中文子串匹配，OR 召回按相关度排序） | `kb_query.py "低结构材料 投放" -k 5 -c 园本课程` |
| `topic_search.py` | 获奖选题检索 | `topic_search.py 自主游戏 一等奖 宁波` |
| `make_docx.py` | 文本 → 评选规范 Word（表/图/文献） | `make_docx.py 论文.txt 输出.docx` |
| `check_paper.py` | 成稿自检（结构/字数/引文/图表/样本量） | `check_paper.py 论文.txt` |
| `init_kb.py` | 一键初始化知识库骨架（幂等） | `init_kb.py` |
| `doctor.py` | 环境自检 + 冒烟测试，装完必跑 | `doctor.py` |
| `drafts.py` | 列近期成稿，写作前比对防雷同 | `drafts.py` |
| `web_search.py` | 联网检索公开资料（Tavily，可选） | `web_search.py "户外自主游戏" -k 5` |

知识库位置默认 `~/paper-kb/`，设环境变量 `PAPER_KB` 可改。索引文件是 `<KB>/.index.db`，删掉重跑 kb_build 即完全重建。

## 五、成稿质量从哪来（skill 内置的规矩）

1. **事实底座先行**：动笔前定死样本量/时间线/前后测数据/案例名单，全文数字不许漂
2. **真实素材优先**：用户提供的细节直接写进正文；未提供则用示范数据并显著标注"需替换"
3. **文献不编造**：只列真实文献，文中 [n] 与文末一一对应
4. **评审闭环**：内行检查点包括统计口径、行动研究循环、理论对话、概念张力、因果归因强度
5. **评选合规**：正文 ≤4000 字、标题下署名、三线表、图题在下表题在上

## 六、目录结构

```
paper-helper/
├── SKILL.md              # 工作流定义（CLI 据此触发与执行）
├── README.md             # 本手册
├── INSTALL.md            # 安装迁移指南（含发给同事的一键安装提示词）
├── scripts/              # kb_build / kb_query / topic_search / make_docx
├── prompts/              # 评审模板 / 写作参考卡 / WorkBuddy 一键导入提示词
└── data/award_topics.json # 浙江 2024-2025 获奖选题 1459 条
```

## 七、常见问题

- **检索不到刚加的文档？** 重跑 `kb_build.py`（索引不会自动更新）
- **某文档被跳过？** 多为扫描版 PDF（无文字层）或加密文档，需先 OCR 或另存
- **中文搜不到？** v1.1 已改用 instr 匹配，兼容 macOS 系统 SQLite；若仍异常请确认用的是本目录最新脚本
- **多人共用一台机器？** 各自设 `PAPER_KB` 环境变量指向不同目录即可
