import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    OpenAIChatCompletionsModel,
    set_default_openai_client,
    set_default_openai_api,
    set_tracing_disabled,
)

load_dotenv(override=True)

MODEL_NAME = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

_CLIENT = None


def configure_agents_sdk():
    """Create the Groq client once and reuse it everywhere."""
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing - check your .env file.")

    _CLIENT = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        timeout=120,
        max_retries=8,
    )
    set_default_openai_client(_CLIENT)
    set_default_openai_api("chat_completions")
    set_tracing_disabled(True)
    return _CLIENT


def build_model():
    """Return a model OBJECT so the name reaches Groq unchanged."""
    return OpenAIChatCompletionsModel(
        model=MODEL_NAME,
        openai_client=configure_agents_sdk(),
    ) 
