"""大模型接入: DeepSeek(OpenAI 兼容接口,可配置切换其他兼容服务)"""
from app.config import settings


def get_chat_model(streaming: bool = True):
    """返回支持流式的 ChatOpenAI 实例"""
    if not settings.deepseek_api_key:
        raise ValueError("未配置 DEEPSEEK_API_KEY,请在 backend/.env 中填写后重启后端")
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.3,
        streaming=streaming,
        timeout=60,
    )
