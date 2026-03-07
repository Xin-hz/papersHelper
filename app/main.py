"""FastAPI 应用入口"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from app.config import get_settings
from app.api.routes import router

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

# 前端静态资源路径（与启动时 cwd 无关）
_frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
_has_frontend = _frontend_dist.is_dir()

if _has_frontend:
    # 静态资源：/app/assets/* -> dist/assets/*
    assets_dir = _frontend_dist / "assets"
    if assets_dir.is_dir():
        app.mount("/app/assets", StaticFiles(directory=str(assets_dir)), name="app_assets")

    @app.get("/app", include_in_schema=False)
    def serve_app_root():
        return RedirectResponse(url="/app/", status_code=302)

    @app.get("/app/", include_in_schema=False)
    def serve_app_index():
        index_file = _frontend_dist / "index.html"
        if index_file.is_file():
            return FileResponse(str(index_file), media_type="text/html")
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="frontend/index.html not found")

    @app.get("/app/{path:path}", include_in_schema=False)
    def serve_app_path(path: str):
        if not path:
            return RedirectResponse(url="/app/", status_code=302)
        f = (_frontend_dist / path).resolve()
        # 只允许在 dist 目录内的文件，避免路径穿越
        try:
            f.relative_to(_frontend_dist)
        except ValueError:
            return FileResponse(str(_frontend_dist / "index.html"), media_type="text/html")
        if f.is_file():
            return FileResponse(str(f))
        # SPA 子路由：返回 index.html
        index_file = _frontend_dist / "index.html"
        if index_file.is_file():
            return FileResponse(str(index_file), media_type="text/html")
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="frontend not built")


if not _has_frontend:
    @app.get("/app", include_in_schema=False)
    @app.get("/app/", include_in_schema=False)
    def app_not_built():
        return {
            "detail": "前端未构建",
            "hint": "请在项目根目录执行: cd frontend && npm run build && cd ..",
            "docs": "/docs",
        }

@app.on_event("startup")
def log_embedding_provider():
    p = getattr(settings, "embedding_provider", "local")
    if p == "dashscope":
        print("[Embedding] 使用通义 API（无需下载本地模型）")
    else:
        print("[Embedding] 使用本地 BGE（首次会从 HuggingFace 下载约 1.3GB）")
    if _has_frontend:
        print("[Frontend] 已挂载: http://<本机IP>:8000/app/  或  http://<本机IP>:8000/")
    else:
        print("[Frontend] 未检测到 frontend/dist，请执行: cd frontend && npm run build")


@app.get("/")
def root():
    """根路径：有前端构建则跳转到 /app/，便于局域网访问"""
    if _has_frontend:
        return RedirectResponse(url="/app/", status_code=302)
    return {"app": settings.app_name, "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
