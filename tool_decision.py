import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

from llm_client import ChatMessage, Role, call_llm


SYSTEM_PROMPT = """You are a tool decision assistant.

You must output exactly one valid JSON object.
Do not output Markdown.
Do not output code fences.
Do not output extra explanation.

Available actions:
- final_answer: use this when you can answer directly without tools
- search_docs: use this when the user asks about local notes, documents, or project knowledge
- calculator: use this when the user asks for arithmetic or numeric calculation

JSON schema:
{
  "action": "final_answer" | "search_docs" | "calculator",
  "arguments": object
}

Rules:
- If action is final_answer, arguments must include "answer".
- If action is search_docs, arguments must include "query".
- If action is calculator, arguments must include "expression".
"""

FINAL_ANSWER_PROMPT_TEMPLATE = """The user asked:
{user_request}

The tool decision was:
{decision_json}

The tool result was:
{tool_result}

Please provide a concise final answer to the user.
"""


class ToolDecision(BaseModel):
    action: Literal["final_answer", "search_docs", "calculator"]
    arguments: dict[str, Any]


class FinalAnswerArguments(BaseModel):
    answer: str


class CalculatorArguments(BaseModel):
    expression: str


class SearchDocsArguments(BaseModel):
    query: str


@dataclass(frozen=True)
class Tool:
    function: Any
    arguments_model: type[BaseModel]


def calculator(expression: str) -> str:
    allowed_chars = set("0123456789+-*/(). ")
    if any(char not in allowed_chars for char in expression):
        raise ValueError("expression contains unsupported characters")

    result = eval(expression, {"__builtins__": {}}, {})
    return str(result)


def search_docs(query: str) -> str:
    note_dir = Path("note")
    if not note_dir.exists():
        return "note directory does not exist."

    normalized_query = query.strip().lower()
    if not normalized_query:
        return "query is empty."

    matches: list[str] = []
    for path in sorted(note_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if normalized_query in line.lower():
                matches.append(f"{path}:{line_number}: {line.strip()}")
                if len(matches) >= 5:
                    return "\n".join(matches)

    if not matches:
        return f"No matches found for query: {query}"

    return "\n".join(matches)


TOOLS: dict[str, Tool] = {
    "calculator": Tool(
        function=calculator,
        arguments_model=CalculatorArguments,
    ),
    "search_docs": Tool(
        function=search_docs,
        arguments_model=SearchDocsArguments,
    ),
}


def parse_tool_decision(text: str) -> ToolDecision:
    parsed_output = json.loads(text)
    return ToolDecision.model_validate(parsed_output)


def execute_tool_decision(decision: ToolDecision) -> str:
    if decision.action == "final_answer":
        args = FinalAnswerArguments.model_validate(decision.arguments)
        return args.answer

    tool = TOOLS.get(decision.action)
    if tool is not None:
        args = tool.arguments_model.model_validate(decision.arguments)
        return tool.function(**args.model_dump())

    raise ValueError(f"unsupported action: {decision.action}")


def main() -> int:
    user_request = input("Task: ").strip()

    if not user_request:
        print("Please enter a task.")
        return 1

    messages = [
        ChatMessage(role=Role.SYSTEM, content=SYSTEM_PROMPT),
        ChatMessage(role=Role.USER, content=user_request),
    ]

    result = call_llm(messages)

    print("\nRaw model output:")
    print(result.answer)

    try:
        decision = parse_tool_decision(result.answer)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        print("\nTool decision parsing failed:")
        print(exc)
        return 1
    
    print("\nParsed tool decision:")
    print(f"action: {decision.action}")
    print(f"arguments: {decision.arguments}")

    try:
        tool_result = execute_tool_decision(decision)
    except ValueError as exc:
        print("\nTool execution failed:")
        print(exc)
        return 1

    print("\nTool result:")
    print(tool_result)

    if decision.action != "final_answer":
        final_prompt = FINAL_ANSWER_PROMPT_TEMPLATE.format(
            user_request=user_request,
            decision_json=decision.model_dump_json(),
            tool_result=tool_result,
        )
        final_messages = [
            ChatMessage(role=Role.USER, content=final_prompt),
        ]
        final_result = call_llm(final_messages)

        print("\nFinal answer:")
        print(final_result.answer)

    print("\nDebug info:")
    print(f"finish_reason: {result.finish_reason}")
    print(f"elapsed_seconds: {result.elapsed_seconds:.2f}")
    print(f"usage: {result.usage}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
