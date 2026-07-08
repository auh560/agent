import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from config import get_settings
from llm_client import ConfigError, LLMAPIError, LLMResponseError


@dataclass
class EmbeddingResult:
    embedding: list[float]
    usage: dict[str, Any]
    elapsed_seconds: float


def get_embedding(text: str) -> EmbeddingResult:
    settings = get_settings()

    if not settings.openai_embedding_api_key:
        raise ConfigError("Missing OPENAI_EMBEDDING_API_KEY environment variable.")

    if not text.strip():
        raise ValueError("text must not be blank")

    request_body = {
        "model": settings.openai_embedding_model,
        "input": text,
    }

    data = json.dumps(request_body).encode("utf-8")
    request = urllib.request.Request(
        url=f"{settings.openai_embedding_base_url}/embeddings",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {settings.openai_embedding_api_key}",
            "Content-Type": "application/json",
        },
    )

    start_time = time.perf_counter()

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise LLMAPIError(f"Embedding request failed: HTTP {exc.code}\n{error_body}") from exc
    except urllib.error.URLError as exc:
        raise LLMAPIError(f"Embedding request failed: {exc.reason}") from exc

    elapsed_seconds = time.perf_counter() - start_time

    try:
        result = json.loads(response_body)
        embedding = result["data"][0]["embedding"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
        raise LLMResponseError("Invalid embedding response format.") from exc

    return EmbeddingResult(
        embedding=embedding,
        usage=result.get("usage", {}),
        elapsed_seconds=elapsed_seconds,
    )


def main() -> int:
    text = input("Text: ").strip()

    try:
        result = get_embedding(text)
    except (ValueError, ConfigError, LLMAPIError, LLMResponseError) as exc:
        print("\nEmbedding request failed:")
        print(exc)
        return 1

    print(f"\nEmbedding dimensions: {len(result.embedding)}")
    print(f"First 5 values: {result.embedding[:5]}")
    print(f"elapsed_seconds: {result.elapsed_seconds:.2f}")
    print(f"usage: {result.usage}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
