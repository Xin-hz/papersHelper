"""LLM 调用：Kimi / 通义千问（OpenAI 兼容）"""
import os
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.config import get_settings


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> BaseChatModel:
    """根据配置返回 Kimi 或 Qwen 的 LangChain Chat 模型"""
    settings = get_settings()
    provider = provider or settings.llm_provider
    provider = provider.lower()

    if provider == "kimi":
        api_key = settings.kimi_api_key or os.environ.get("KIMI_API_KEY", "")
        base_url = settings.kimi_base_url
        model_name = model or settings.kimi_model
        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=temperature,
        )
    if provider == "qwen":
        api_key = settings.qwen_api_key or os.environ.get("DASHSCOPE_API_KEY", "")
        base_url = settings.qwen_base_url
        model_name = model or settings.qwen_model
        return ChatOpenAI(
            model=model_name,
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=temperature,
        )
    raise ValueError(f"不支持的 LLM 提供商: {provider}，请使用 kimi 或 qwen")


def get_chat_llm(temperature: float = 0.7) -> BaseChatModel:
    return get_llm(temperature=temperature)
