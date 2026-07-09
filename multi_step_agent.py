import json

from pydantic import ValidationError

from llm_client import (
    ChatMessage,
    ConfigError,
    LLMAPIError,
    LLMResponseError,
    Role,
    call_llm,
)
from tool_decision import (
    SYSTEM_PROMPT,
    execute_tool_decision,
    parse_tool_decision,
)


MULTI_STEP_INSTRUCTIONS = """You are running in a multi-step agent loop.

You will receive:
- The original user task
- Previous tool decisions and observations

Decide the next action.
If you have enough information, use final_answer.
If you need more information or calculation, use one tool.
Do not repeat a tool call if the previous observation already contains enough information.
"""


def format_scratchpad(scratchpad: list[str]) -> str:
    if not scratchpad:
        return "No previous steps."

    return "\n\n".join(scratchpad)


def build_agent_messages(user_request: str, scratchpad: list[str]) -> list[ChatMessage]:
    user_prompt = f"""Original user task:
{user_request}

Previous steps:
{format_scratchpad(scratchpad)}

Now decide the next action.
"""

    return [
        ChatMessage(
            role=Role.SYSTEM,
            content=f"{SYSTEM_PROMPT}\n\n{MULTI_STEP_INSTRUCTIONS}",
        ),
        ChatMessage(role=Role.USER, content=user_prompt),
    ]


def run_agent(user_request: str, max_steps: int = 5) -> str:
    scratchpad: list[str] = []

    for step in range(1, max_steps + 1):
        messages = build_agent_messages(user_request, scratchpad)
        result = call_llm(messages)
        decision = parse_tool_decision(result.answer)

        print(f"\nStep {step} decision:")
        print(f"action: {decision.action}")
        print(f"arguments: {decision.arguments}")

        tool_result = execute_tool_decision(decision)

        if decision.action == "final_answer":
            return tool_result

        print("\nObservation:")
        print(tool_result)

        scratchpad.append(
            f"""Step {step}:
Action: {decision.action}
Arguments: {decision.model_dump_json()}
Observation:
{tool_result}
"""
        )

    return "Agent stopped because max_steps was reached."


def main() -> int:
    user_request = input("Task: ").strip()
    if not user_request:
        print("Please enter a task.")
        return 1

    try:
        answer = run_agent(user_request)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        print("\nAgent decision parsing or validation failed:")
        print(exc)
        return 1
    except (ConfigError, LLMAPIError, LLMResponseError) as exc:
        print("\nAgent API call or tool execution failed:")
        print(exc)
        return 1

    print("\nFinal answer:")
    print(answer)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
