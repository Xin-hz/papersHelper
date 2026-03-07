# 幼儿园教师 AI 论文助手 - 前端

Vue 3 + Vite + Vue Router，对接后端 FastAPI 接口。

## 开发

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173 。接口请求会通过 Vite 代理到 http://localhost:8000/api ，需先启动后端。

## 构建

```bash
npm run build
```

产物在 `dist/`。若后端已启动且存在 `frontend/dist`，访问 http://localhost:8000/app/ 即可使用前端。

## 单独部署前端

将 `dist/` 部署到 Nginx 或静态托管，并配置：

- 环境变量：`VITE_API_BASE` 为后端地址（如 `https://api.example.com`），构建时生效。
- 若前后端同域，无需设置；请求会发往当前域下的 `/api`。

重新构建：

```bash
VITE_API_BASE=https://your-backend.com npm run build
```

## 页面说明

- **首页**：工作台，入口为论文、教案、教学案例、知识库。
- **论文**：生成 / 润色 / 扩写 / 降重 Tab，表单 + 结果展示。
- **教案**：教学主题、年龄段、领域、课时，生成教案。
- **教学案例**：案例主题、场景，生成教学案例。
- **知识库**：上传 PDF/DOCX、输入问题，展示回答与引用来源。

详见 [../docs/FRONTEND_FLOW.md](../docs/FRONTEND_FLOW.md)。
