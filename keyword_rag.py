import re
from pathlib import Path

from llm_client import (
    ChatMessage,
    ConfigError,
    LLMAPIError,
    LLMResponseError,
    Role,
    call_llm,
)


STOP_WORDS = {
    "的",
    "了",
    "是",
    "有",
    "什么",
    "作用",
    "一下",
    "吗",
    "么",
}


def load_markdown_files(note_dir: Path = Path("note")) -> list[dict]:
    documents: list[dict] = []

    for path in sorted(note_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        documents.append(
            {
                "source": str(path),
                "text": text,
            }
        )

    return documents


def split_into_chunks(text: str) -> list[str]:
    chunks: list[str] = []

    for paragraph in text.split("\n\n"):
        chunk = paragraph.strip()
        if chunk:
            chunks.append(chunk)

    return chunks


def build_chunks(documents: list[dict]) -> list[dict]:
    all_chunks: list[dict] = []

    for document in documents:
        chunks = split_into_chunks(document["text"])
        for index, chunk in enumerate(chunks, start=1):
            all_chunks.append(
                {
                    "source": document["source"],
                    "chunk_id": index,
                    "text": chunk,
                }
            )

    return all_chunks


def extract_keywords(query: str) -> list[str]:
    keywords: list[str] = []
    normalized_query = query.strip().lower()

    for word in normalized_query.split():
        if word and word not in STOP_WORDS:
            keywords.append(word)

    for word in re.findall(r"[a-zA-Z0-9_]+", normalized_query):
        if word and word not in STOP_WORDS:
            keywords.append(word)

    if keywords:
        return list(dict.fromkeys(keywords))

    if normalized_query:
        return [normalized_query]

    return []


def search_chunks(query: str, chunks: list[dict], limit: int = 5) -> list[dict]:
    keywords = extract_keywords(query)
    if not keywords:
        return []

    scored_results: list[tuple[int, dict]] = []

    for chunk in chunks:
        text = chunk["text"].lower()
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            scored_results.append((score, chunk))

    scored_results.sort(key=lambda item: item[0], reverse=True)
    return [chunk for score, chunk in scored_results[:limit]]



def build_rag_prompt(query: str, results: list[dict]) -> str:
    context_parts: list[str] = []

    for index, result in enumerate(results, start=1):
        context_parts.append(
            f"[{index}] source: {result['source']}, chunk_id: {result['chunk_id']}\n"
            f"{result['text']}"
        )

    context = "\n\n".join(context_parts)

    return f"""You are a learning assistant.
Answer the user's question based only on the context below.
If the context is not enough, say you do not have enough information.
Merge duplicate information and do not repeat the same point.

Context:
{context}

Question:
{query}
"""


def main() -> int:
    documents = load_markdown_files()
    chunks = build_chunks(documents)

    print(f"Loaded documents: {len(documents)}")
    print(f"Built chunks: {len(chunks)}")

    query = input("Query: ").strip()
    results = search_chunks(query, chunks)

    if not results:
        print("No matching chunks found.")
        return 0

    prompt = build_rag_prompt(query, results)

    messages = [
        ChatMessage(role=Role.USER, content=prompt),
    ]

    try:
        result = call_llm(messages)
    except (ConfigError, LLMAPIError, LLMResponseError) as exc:
        print("\nLLM request failed:")
        print(exc)
        return 1

    print("\nAnswer:")
    print(result.answer)

    print("\nDebug info:")
    print(f"finish_reason: {result.finish_reason}")
    print(f"elapsed_seconds: {result.elapsed_seconds:.2f}")
    print(f"usage: {result.usage}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
