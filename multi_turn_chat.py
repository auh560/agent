import logging
from pathlib import Path

from llm_client import ChatMessage, LLMResult, call_llm
from llm_client import Role


SYSTEM_PROMPT = "你是一个后端工程师视角的学习助手，回答要清晰、具体、偏工程实践。"
SESSION_SUMMARY = (
    "会话摘要：用户有 C++ / 后端基础，正在学习 Agent。"
    "当前阶段是 LLM API 基础，已经完成单轮调用、多轮对话和最近 N 轮历史截断。"
)

MAX_HISTORY_ROUNDS = 3
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "app.log"


def setup_logging() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s:%(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )


def print_debug_info(result: LLMResult) -> None:
    logging.info("--- Debug Info ---")
    logging.info("finish_reason: %s", result.finish_reason)
    logging.info("elapsed_seconds: %.2f", result.elapsed_seconds)

    usage = result.usage
    if usage:
        logging.info("prompt_tokens: %s", usage.get("prompt_tokens"))
        logging.info("completion_tokens: %s", usage.get("completion_tokens"))
        logging.info("total_tokens: %s", usage.get("total_tokens"))
    else:
        logging.info("usage: not returned")


def print_context_info(messages: list[ChatMessage]) -> None:
    logging.info("messages_count: %s", len(messages))


def trim_messages(
    messages: list[ChatMessage],
    max_rounds: int,
) -> list[ChatMessage]:
    fixed_messages = messages[:2]
    recent_messages = messages[2:][-max_rounds * 2:]
    return fixed_messages + recent_messages


def main() -> int:
    setup_logging()

    messages = [
        ChatMessage(role=Role.SYSTEM, content=SYSTEM_PROMPT),
        ChatMessage(role=Role.SYSTEM, content=SESSION_SUMMARY),
    ]

    logging.info("Multi-turn chat started. Type 'exit' to quit.")


    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("Bye.")
            return 0

        if not user_input:
            print("Please enter a question.")
            continue

        messages.append(
            ChatMessage(role=Role.USER, content=user_input)
        )

        try:
            result = call_llm(messages)
        except Exception as exc:
            logging.error("Error: %s", exc)
            messages.pop()
            continue

        answer = result.answer
        messages.append(
            ChatMessage(role=Role.ASSISTANT, content=answer)
        )
        messages = trim_messages(messages, MAX_HISTORY_ROUNDS)
        print(f"\nAssistant: {answer}")
        print_debug_info(result)
        print_context_info(messages)
        print()


if __name__ == "__main__":
    raise SystemExit(main())
