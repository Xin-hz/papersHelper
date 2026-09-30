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

    if provider == "deepseek":
        api_key = settings.deepseek_api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            raise ValueError("未配置 DeepSeek API Key：请在 .env 中设置 DEEPSEEK_API_KEY（https://platform.deepseek.com 获取）")
        return _chat_openai(model or settings.deepseek_model, api_key, settings.deepseek_base_url, temperature)
    if provider == "glm":
        api_key = settings.glm_api_key or os.environ.get("GLM_API_KEY", "") or os.environ.get("ZHIPU_API_KEY", "")
        if not api_key:
            raise ValueError("未配置智谱 GLM API Key：请在 .env 中设置 GLM_API_KEY（https://open.bigmodel.cn 获取）")
        base_url = settings.glm_base_url
        model_name = model or settings.glm_model
        return _chat_openai(model_name, api_key, base_url, temperature)
    if provider == "kimi":
        api_key = settings.kimi_api_key or os.environ.get("KIMI_API_KEY", "")
        base_url = settings.kimi_base_url
        model_name = model or settings.kimi_model
        return _chat_openai(model_name, api_key, base_url, temperature)
    if provider == "qwen":
        api_key = settings.qwen_api_key or os.environ.get("DASHSCOPE_API_KEY", "")
        base_url = settings.qwen_base_url
        model_name = model or settings.qwen_model
        return _chat_openai(model_name, api_key, base_url, temperature)
    raise ValueError(f"不支持的 LLM 提供商: {provider}，请使用 deepseek / glm / kimi / qwen")


def _chat_openai(model_name: str, api_key: str, base_url: str, temperature: float) -> ChatOpenAI:
    """统一构造：显式超时 + 自动重试，避免个别请求挂死导致整个流程卡住"""
    return ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        openai_api_base=base_url,
        temperature=temperature,
        timeout=300,
        max_retries=2,
    )


def get_chat_llm(temperature: float = 0.7, model: Optional[str] = None) -> BaseChatModel:
    """获取对话模型；不传 model 时若配置了 PAPER_MODEL 则使用它（长文生成用更强模型）"""
    settings = get_settings()
    return get_llm(model=model or getattr(settings, "paper_model", "") or None, temperature=temperature)
