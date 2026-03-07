"""应用配置"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """从环境变量读取配置"""
    # 应用
    app_name: str = "幼儿园教师论文助手"
    debug: bool = False

    # 数据库 (PostgreSQL + pgvector)
    database_url: str = "postgresql://postgres:postgres@localhost:5432/papers_helper"

    # LLM: kimi | qwen
    llm_provider: str = "kimi"
    # Kimi API (OpenAI 兼容)
    kimi_api_key: str = ""
    kimi_base_url: str = "https://api.moonshot.cn/v1"
    kimi_model: str = "moonshot-v1-128k"
    # 通义千问 API
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-turbo"

    # Embedding: local(本地 BGE) | dashscope(通义 API，无需下载模型)
    embedding_provider: str = "local"  # local | dashscope
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    embedding_device: str = "cpu"  # cpu | cuda（仅 local 时有效）
    dashscope_api_key: str = ""  # 通义 Embedding，可与 QWEN_API_KEY 共用
    dashscope_embedding_model: str = "text-embedding-v3"

    # RAG
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_retrieve: int = 5

    # 知识库上传目录
    upload_dir: str = "knowledge_uploads"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
