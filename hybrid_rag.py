from keyword_rag import build_chunks, build_rag_prompt, load_markdown_files, search_chunks
from llm_client import (
    ChatMessage,
    ConfigError,
    LLMAPIError,
    LLMResponseError,
    Role,
    call_llm,
)
from vector_rag import load_vector_index, search_similar_chunks


def merge_results(
    vector_results: list[dict],
    keyword_results: list[dict],
    limit: int = 5,
) -> list[dict]:
    merged: list[dict] = []
    seen: set[tuple[str, int]] = set()

    for result in vector_results + keyword_results:
        key = (result["source"], result["chunk_id"])
        if key in seen:
            continue

        seen.add(key)
        merged.append(result)

        if len(merged) >= limit:
            break

    return merged


def hybrid_search(query: str, limit: int = 5) -> list[dict]:
    documents = load_markdown_files()
    chunks = build_chunks(documents)
    index_items = load_vector_index()

    vector_results = search_similar_chunks(query, index_items, top_k=limit)
    keyword_results = search_chunks(query, chunks, limit=limit)

    return merge_results(
        vector_results=vector_results,
        keyword_results=keyword_results,
        limit=limit,
    )


def format_search_results(results: list[dict]) -> str:
    if not results:
        return "No relevant knowledge base chunks found."

    formatted_results: list[str] = []

    for index, result in enumerate(results, start=1):
        formatted_results.append(
            f"[{index}] source: {result['source']}, chunk_id: {result['chunk_id']}\n"
            f"{result['text']}"
        )

    return "\n\n".join(formatted_results)


def search_knowledge_base(query: str) -> str:
    results = hybrid_search(query)
    return format_search_results(results)


def main() -> int:
    query = input("Query: ").strip()
    if not query:
        print("Please enter a query.")
        return 1

    try:
        results = hybrid_search(query)
        prompt = build_rag_prompt(query, results)
        llm_result = call_llm([ChatMessage(role=Role.USER, content=prompt)])
    except FileNotFoundError:
        print("vector_index.json does not exist. Run build_vector_index.py first.")
        return 1
    except (ValueError, ConfigError, LLMAPIError, LLMResponseError) as exc:
        print("\nHybrid RAG failed:")
        print(exc)
        return 1

    print("\nRetrieved chunks:")
    for result in results:
        score = result.get("score")
        if score is None:
            print(f"- keyword {result['source']}#{result['chunk_id']}")
        else:
            print(f"- vector score={score:.4f} {result['source']}#{result['chunk_id']}")

    print("\nAnswer:")
    print(llm_result.answer)

    print("\nDebug info:")
    print(f"finish_reason: {llm_result.finish_reason}")
    print(f"elapsed_seconds: {llm_result.elapsed_seconds:.2f}")
    print(f"usage: {llm_result.usage}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
