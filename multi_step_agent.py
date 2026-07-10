import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

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


class AgentStep(BaseModel):
    step: int
    action: str
    arguments: dict[str, Any]
    observation: str


class AgentError(BaseModel):
    step: int
    error: str
    action: str | None = None
    arguments: dict[str, Any] | None = None


class AgentState(BaseModel):
    scratchpad: list[str] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    steps: list[AgentStep] = Field(default_factory=list)
    errors: list[AgentError] = Field(default_factory=list)


class AgentResult(BaseModel):
    answer: str
    state: AgentState


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


def run_agent(user_request: str, max_steps: int = 5) -> AgentResult:
    state = AgentState()

    for step in range(1, max_steps + 1):
        messages = build_agent_messages(user_request, state.scratchpad)
        result = call_llm(messages)
        decision = parse_tool_decision(result.answer)

        print(f"\nStep {step} decision:")
        print(f"action: {decision.action}")
        print(f"arguments: {decision.arguments}")

        if decision.action != "final_answer":
            current_call = {
                "action": decision.action,
                "arguments": decision.arguments,
            }

            if current_call in state.tool_calls:
                state.errors.append(
                    AgentError(
                        step=step,
                        action=decision.action,
                        arguments=decision.arguments,
                        error="repeated tool call",
                    )
                )
                return AgentResult(
                    answer="Agent stopped because it repeated the same tool call.",
                    state=state,
                )

            state.tool_calls.append(current_call)

        try:
            tool_result = execute_tool_decision(decision)
        except (ValidationError, ValueError, ConfigError, LLMAPIError, LLMResponseError) as exc:
            state.errors.append(
                AgentError(
                    step=step,
                    action=decision.action,
                    arguments=decision.arguments,
                    error=str(exc),
                )
            )
            return AgentResult(
                answer="Agent stopped because tool execution failed.",
                state=state,
            )

        if decision.action == "final_answer":
            state.steps.append(
                AgentStep(
                    step=step,
                    action=decision.action,
                    arguments=decision.arguments,
                    observation=tool_result,
                )
            )
            return AgentResult(answer=tool_result, state=state)

        print("\nObservation:")
        print(tool_result)

        state.steps.append(
            AgentStep(
                step=step,
                action=decision.action,
                arguments=decision.arguments,
                observation=tool_result,
            )
        )

        state.scratchpad.append(
            f"""Step {step}:
Action: {decision.action}
Arguments: {decision.model_dump_json()}
Observation:
{tool_result}
"""
        )

    state.errors.append(
        AgentError(
            step=max_steps,
            error="max_steps reached",
        )
    )
    return AgentResult(
        answer="Agent stopped because max_steps was reached.",
        state=state,
    )


def main() -> int:
    user_request = input("Task: ").strip()
    if not user_request:
        print("Please enter a task.")
        return 1

    try:
        result = run_agent(user_request)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        print("\nAgent decision parsing or validation failed:")
        print(exc)
        return 1
    except (ConfigError, LLMAPIError, LLMResponseError) as exc:
        print("\nAgent API call or tool execution failed:")
        print(exc)
        return 1

    print("\nFinal answer:")
    print(result.answer)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
