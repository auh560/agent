import os
from dataclasses import dataclass
from functools import lru_cache


DEFAULT_BASE_URL = "http://47.85.46.196:8080/v1"
DEFAULT_MODEL = "gpt-5.5"
DEFAULT_EMBEDDING_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_EMBEDDING_MODEL = "text-embedding-v1"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 200


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_base_url: str
    openai_model: str
    openai_embedding_api_key: str | None
    openai_embedding_base_url: str
    openai_embedding_model: str
    temperature: float
    max_tokens: int


@lru_cache
def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        openai_model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        openai_embedding_api_key=os.getenv(
            "OPENAI_EMBEDDING_API_KEY",
            os.getenv("OPENAI_API_KEY"),
        ),
        openai_embedding_base_url=os.getenv(
            "OPENAI_EMBEDDING_BASE_URL",
            DEFAULT_EMBEDDING_BASE_URL,
        ).rstrip("/"),
        openai_embedding_model=os.getenv(
            "OPENAI_EMBEDDING_MODEL",
            DEFAULT_EMBEDDING_MODEL,
        ),
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=DEFAULT_MAX_TOKENS,
    )
