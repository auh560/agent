import json
import math
from pathlib import Path

from embedding_client import get_embedding
from keyword_rag import build_rag_prompt
from llm_client import (
    ChatMessage,
    ConfigError,
    LLMAPIError,
    LLMResponseError,
    Role,
    call_llm,
)


DEFAULT_INDEX_PATH = Path("vector_index.json")


def load_vector_index(index_path: Path = DEFAULT_INDEX_PATH) -> list[dict]:
    text = index_path.read_text(encoding="utf-8")
    return json.loads(text)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimensions")

    dot_product = sum(x * y for x, y in zip(a, b))
    a_length = math.sqrt(sum(x * x for x in a))
    b_length = math.sqrt(sum(y * y for y in b))

    if a_length == 0 or b_length == 0:
        return 0.0

    return dot_product / (a_length * b_length)


def search_similar_chunks(
    query: str,
    index_items: list[dict],
    top_k: int = 5,
) -> list[dict]:
    query_embedding = get_embedding(query).embedding
    scored_results: list[tuple[float, dict]] = []

    for item in index_items:
        score = cosine_similarity(query_embedding, item["embedding"])
        scored_results.append((score, item))

    scored_results.sort(key=lambda result: result[0], reverse=True)

    results: list[dict] = []
    for score, item in scored_results[:top_k]:
        result = dict(item)
        result["score"] = score
        results.append(result)

    return results


def main() -> int:
    query = input("Query: ").strip()
    if not query:
        print("Please enter a query.")
        return 1

    try:
        index_items = load_vector_index()
        results = search_similar_chunks(query, index_items)
        prompt = build_rag_prompt(query, results)
        llm_result = call_llm([ChatMessage(role=Role.USER, content=prompt)])
    except FileNotFoundError:
        print("vector_index.json does not exist. Run build_vector_index.py first.")
        return 1
    except (ValueError, ConfigError, LLMAPIError, LLMResponseError) as exc:
        print("\nVector RAG failed:")
        print(exc)
        return 1

    print("\nRetrieved chunks:")
    for result in results:
        print(f"- score={result['score']:.4f} {result['source']}#{result['chunk_id']}")

    print("\nAnswer:")
    print(llm_result.answer)

    print("\nDebug info:")
    print(f"finish_reason: {llm_result.finish_reason}")
    print(f"elapsed_seconds: {llm_result.elapsed_seconds:.2f}")
    print(f"usage: {llm_result.usage}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
