import argparse
import json
from pathlib import Path

from embedding_client import get_embedding
from keyword_rag import build_chunks, load_markdown_files
from llm_client import ConfigError, LLMAPIError, LLMResponseError


DEFAULT_INDEX_PATH = Path("vector_index.json")


def build_vector_index(limit: int | None = None) -> list[dict]:
    documents = load_markdown_files()
    chunks = build_chunks(documents)

    if limit is not None:
        chunks = chunks[:limit]

    index_items: list[dict] = []
    total_chunks = len(chunks)

    for index, chunk in enumerate(chunks, start=1):
        print(f"Embedding chunk {index}/{total_chunks}: {chunk['source']}#{chunk['chunk_id']}")
        result = get_embedding(chunk["text"])
        index_items.append(
            {
                "source": chunk["source"],
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "embedding": result.embedding,
            }
        )

    return index_items


def save_vector_index(index_items: list[dict], index_path: Path = DEFAULT_INDEX_PATH) -> None:
    index_path.write_text(
        json.dumps(index_items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local vector index for notes.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only embed the first N chunks. Useful for testing.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help="Output JSON index path.",
    )
    args = parser.parse_args()

    try:
        index_items = build_vector_index(limit=args.limit)
    except (ValueError, ConfigError, LLMAPIError, LLMResponseError) as exc:
        print("\nVector index build failed:")
        print(exc)
        return 1

    save_vector_index(index_items, args.output)
    print(f"\nSaved {len(index_items)} indexed chunks to {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
