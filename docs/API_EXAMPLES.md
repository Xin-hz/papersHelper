# 接口请求示例（调试用）

默认 base：`http://localhost:8000`，若端口不同请替换。

---

## 1. 知识库问答

**POST** `/api/ask_knowledge`

```bash
curl -X POST "http://localhost:8000/api/ask_knowledge" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "幼儿园游戏化教学有哪些常见策略？",
    "top_k": 5
  }'
```

最小请求（不指定 top_k）：
```json
{"question": "什么是区域活动？"}
```

---

## 2. 论文生成

**POST** `/api/generate_paper`

```bash
curl -X POST "http://localhost:8000/api/generate_paper" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "幼儿园区域活动中教师指导策略研究",
    "outline": "一、引言 二、文献综述 三、研究方法 四、结果与讨论 五、结论",
    "use_rag": true
  }'
```

最小请求：
```json
{"title": "幼儿园家园共育的实践与思考"}
```

---

## 3. 教案生成

**POST** `/api/generate_lesson_plan`

```bash
curl -X POST "http://localhost:8000/api/generate_lesson_plan" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "认识四季",
    "grade": "大班",
    "subject": "科学",
    "duration": "一课时",
    "use_rag": true
  }'
```

最小请求：
```json
{"topic": "有趣的图形"}
```

---

## 4. 教学案例生成

**POST** `/api/generate_teaching_case`

```bash
curl -X POST "http://localhost:8000/api/generate_teaching_case" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "区域活动中幼儿争抢材料",
    "scenario": "区域活动",
    "use_rag": true
  }'
```

最小请求：
```json
{"topic": "幼儿不愿午睡时的教师应对"}
```

---

## 5. 论文润色

**POST** `/api/improve_paper`

```bash
curl -X POST "http://localhost:8000/api/improve_paper" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "幼儿教育很重要，老师要好好教。",
    "focus": "学术性与语言流畅"
  }'
```

最小请求：
```json
{"content": "这是你的一段论文正文，需要润色。"}
```

---

## 6. 论文降重

**POST** `/api/reduce_weight`

```bash
curl -X POST "http://localhost:8000/api/reduce_weight" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "幼儿园教师应当尊重幼儿的主体性，关注幼儿的个体差异。",
    "focus": "同义替换与句式改写"
  }'
```

最小请求：
```json
{"content": "待降重的论文段落内容..."}
```

---

## 7. 论文扩写

**POST** `/api/expand_paper`

```bash
curl -X POST "http://localhost:8000/api/expand_paper" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "本研究采用观察法。",
    "target_section": "研究方法",
    "use_rag": true
  }'
```

最小请求：
```json
{"content": "需要扩写的段落..."}
```

---

## 8. 上传知识库（PDF/DOCX/DOC，支持多文件）

**POST** `/api/upload_knowledge`  
**Content-Type:** `multipart/form-data`  
**字段名:** `files`（可传多个文件，多次 `-F "files=@路径"`）

支持格式：`.pdf`、`.docx`、`.doc`（.doc 仅 macOS）。

```bash
# 单文件
curl -X POST "http://localhost:8000/api/upload_knowledge" -F "files=@/path/to/document.pdf"

# 多文件
curl -X POST "http://localhost:8000/api/upload_knowledge" \
  -F "files=@/path/to/a.pdf" -F "files=@/path/to/b.docx"
```

Windows PowerShell 多文件示例：
```powershell
curl.exe -X POST "http://localhost:8000/api/upload_knowledge" -F "files=@C:\path\to\a.pdf" -F "files=@C:\path\to\b.docx"
```

---

## 响应格式说明

- **成功**：`success: true`，业务内容在 `content` / `answer` / `message` 等字段。
- **失败**：`success: false`，错误信息在对应内容字段或 HTTP 状态码 4xx/5xx 的 `detail` 中。

示例（知识库问答成功）：
```json
{
  "success": true,
  "answer": "根据知识库内容……",
  "sources": ["片段1……", "片段2……"]
}
```

示例（生成类成功）：
```json
{
  "success": true,
  "content": "生成的正文内容……"
}
```

---

## 在 Swagger 中调试

打开 **http://localhost:8000/docs**，选择对应接口 → **Try it out** → 填写 Request body（JSON）→ **Execute**。
