import json
import time
import urllib.error
import urllib.request
from enum import Enum
from dataclasses import dataclass
from typing import Any

from config import get_settings


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatMessage:
    role: Role
    content: str

    def __post_init__(self) -> None:
        if not isinstance(self.role, Role):
            raise ValueError(f"Invalid role: {self.role}")

    def to_dict(self) -> dict[str, str]:
        return {
            "role": self.role.value,
            "content": self.content,
        }


@dataclass
class LLMResult:
    answer: str
    finish_reason: str | None
    usage: dict[str, Any]
    elapsed_seconds: float


class ConfigError(Exception):
    pass


class LLMAPIError(Exception):
    pass


class LLMResponseError(Exception):
    pass


def call_llm(messages: list[ChatMessage]) -> LLMResult:
    settings = get_settings()

    if not settings.openai_api_key:
        raise ConfigError("Missing OPENAI_API_KEY environment variable.")

    request_body = {
        "model": settings.openai_model,
        "messages": [message.to_dict() for message in messages],
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
    }

    data = json.dumps(request_body).encode("utf-8")
    request = urllib.request.Request(
        url=f"{settings.openai_base_url}/chat/completions",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
    )

    start_time = time.perf_counter()

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise LLMAPIError(f"API request failed: HTTP {exc.code}\n{error_body}") from exc
    except urllib.error.URLError as exc:
        raise LLMAPIError(f"API request failed: {exc.reason}") from exc

    elapsed_seconds = time.perf_counter() - start_time

    try:
        result = json.loads(response_body)
        choice = result["choices"][0]
        answer = choice["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise LLMResponseError("Invalid model response format.") from exc

    return LLMResult(
        answer=answer,
        finish_reason=choice.get("finish_reason"),
        usage=result.get("usage", {}),
        elapsed_seconds=elapsed_seconds,
    )
