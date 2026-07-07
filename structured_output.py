import json
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from llm_client import ChatMessage, Role, call_llm


SYSTEM_PROMPT = """你是一个结构化输出助手。

你必须只输出一个合法 JSON 对象。
不要输出 Markdown。
不要输出代码块。
不要输出任何额外解释。

JSON 字段必须是：
{
  "answer": string,
  "confidence": "low" | "medium" | "high",
  "need_tool": boolean
}

字段含义：
- answer: 对用户问题的简短回答
- confidence: 你对回答的信心，只能是 low、medium 或 high
- need_tool: 如果问题需要实时信息、外部资料或本地文件，填 true；否则填 false
"""

REPAIR_PROMPT_TEMPLATE = """Your previous output could not be parsed as the required JSON schema.

Error:
{error}

Previous output:
{raw_output}

Please output the corrected JSON object only.
Do not output Markdown, code fences, or extra explanation.
"""


class StructuredOutput(BaseModel):
    answer: str = Field(min_length=1)
    confidence: Literal["low", "medium", "high"]
    need_tool: bool

    @field_validator("answer")
    @classmethod
    def answer_must_not_be_blank(cls, value: str) -> str:
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("answer must not be blank")
        return stripped_value


def parse_structured_output(text: str) -> StructuredOutput:
    parsed_output = json.loads(text)
    return StructuredOutput.model_validate(parsed_output)


def main() -> int:
    user_question = input("Question: ").strip()

    if not user_question:
        print("Please enter a question.")
        return 1

    messages = [
        ChatMessage(role=Role.SYSTEM, content=SYSTEM_PROMPT),
        ChatMessage(role=Role.USER, content=user_question),
    ]

    result = call_llm(messages)

    print("\nRaw model output:")
    print(result.answer)

    try:
        structured_output = parse_structured_output(result.answer)
    except (json.JSONDecodeError, ValidationError) as exc:
        print("\nStructured output validation failed. Asking model to repair once.")
        print(exc)

        repair_prompt = REPAIR_PROMPT_TEMPLATE.format(
            error=exc,
            raw_output=result.answer,
        )
        repair_messages = [
            *messages,
            ChatMessage(role=Role.ASSISTANT, content=result.answer),
            ChatMessage(role=Role.USER, content=repair_prompt),
        ]
        repair_result = call_llm(repair_messages)

        print("\nRaw repaired model output:")
        print(repair_result.answer)

        try:
            structured_output = parse_structured_output(repair_result.answer)
        except (json.JSONDecodeError, ValidationError) as repair_exc:
            print("\nRepair failed:")
            print(repair_exc)
            print("\nRaw output that failed after repair:")
            print(repair_result.answer)
            return 1

        result = repair_result

    print("\nParsed output:")
    print(f"answer: {structured_output.answer}")
    print(f"confidence: {structured_output.confidence}")
    print(f"need_tool: {structured_output.need_tool}")

    print("\nDebug info:")
    print(f"finish_reason: {result.finish_reason}")
    print(f"elapsed_seconds: {result.elapsed_seconds:.2f}")
    print(f"usage: {result.usage}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
