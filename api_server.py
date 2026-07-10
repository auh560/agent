import json
import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError, field_validator

from agent_run_store import find_agent_run, generate_run_id, load_agent_runs, save_agent_run
from llm_client import (
    ChatMessage,
    ConfigError,
    LLMAPIError,
    LLMResponseError,
    Role,
    call_llm,
)
from multi_step_agent import AgentError, run_agent


logger = logging.getLogger(__name__)

app = FastAPI(
    title="LLM Chat API",
    description="A small FastAPI service that wraps an OpenAI-compatible chat model.",
    version="0.1.0",
)


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="User message sent to the chat model.",
    )

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("message must not be blank")
        return stripped_value


class ChatResponse(BaseModel):
    answer: str
    finish_reason: str | None
    usage: dict
    elapsed_seconds: float


class AgentChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="User task sent to the multi-step agent.",
    )
    max_steps: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of agent loop steps.",
    )

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("message must not be blank")
        return stripped_value


class AgentPublicStep(BaseModel):
    step: int
    action: str
    arguments: dict

# 给用户回复的消息
class AgentChatResponse(BaseModel):
    run_id: str
    answer: str
    steps: list[AgentPublicStep]
    errors: list[AgentError]


class AgentRunSummary(BaseModel):
    run_id: str | None
    created_at: str | None
    user_message: str | None
    answer: str | None
    steps_count: int
    errors_count: int


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    logger.info("Chat request received")

    messages = [
        ChatMessage(role=Role.SYSTEM, content="你是一个后端工程师视角的学习助手。"),
        ChatMessage(role=Role.USER, content=request.message),
    ]

    try:
        result = call_llm(messages)
    except ConfigError as exc:
        logger.exception("Server configuration error")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error.",
        ) from exc
    except LLMAPIError as exc:
        logger.exception("Upstream model service failed")
        raise HTTPException(
            status_code=502,
            detail="Upstream model service failed.",
        ) from exc
    except LLMResponseError as exc:
        logger.exception("Invalid model response")
        raise HTTPException(
            status_code=500,
            detail="Invalid model response.",
        ) from exc
    except Exception as exc:
        logger.exception("Model API request failed")
        raise HTTPException(
            status_code=500,
            detail="Model API request failed.",
        ) from exc

    logger.info(
        "Model API request completed: finish_reason=%s elapsed_seconds=%.2f total_tokens=%s",
        result.finish_reason,
        result.elapsed_seconds,
        result.usage.get("total_tokens"),
    )

    return ChatResponse(
        answer=result.answer,
        finish_reason=result.finish_reason,
        usage=result.usage,
        elapsed_seconds=result.elapsed_seconds,
    )


@app.post("/agent/chat")
def agent_chat(request: AgentChatRequest) -> AgentChatResponse:
    logger.info("Agent chat request received")
    run_id = generate_run_id()

    try:
        result = run_agent(request.message, max_steps=request.max_steps)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        logger.exception("Agent decision parsing or validation failed")
        raise HTTPException(
            status_code=500,
            detail="Agent decision parsing or validation failed.",
        ) from exc
    except (ConfigError, LLMAPIError, LLMResponseError) as exc:
        logger.exception("Agent API call or tool execution failed")
        raise HTTPException(
            status_code=502,
            detail="Agent API call or tool execution failed.",
        ) from exc
    except Exception as exc:
        logger.exception("Agent request failed")
        raise HTTPException(
            status_code=500,
            detail="Agent request failed.",
        ) from exc

    logger.info(
        "Agent request completed: run_id=%s steps=%s errors=%s",
        run_id,
        len(result.state.steps),
        len(result.state.errors),
    )
    save_agent_run(run_id, request.message, result)

    return AgentChatResponse(
        run_id=run_id,
        answer=result.answer,
        steps=[
            AgentPublicStep(
                step=step.step,
                action=step.action,
                arguments=step.arguments,
            )
            for step in result.state.steps
        ],
        errors=result.state.errors,
    )


@app.get("/agent/runs")
def list_agent_runs() -> list[AgentRunSummary]:
    records = load_agent_runs()

    summaries: list[AgentRunSummary] = []
    for record in reversed(records):
        result = record.get("result", {})
        state = result.get("state", {})
        steps = state.get("steps", [])
        errors = state.get("errors", [])

        summaries.append(
            AgentRunSummary(
                run_id=record.get("run_id"),
                created_at=record.get("created_at"),
                user_message=record.get("user_message"),
                answer=result.get("answer"),
                steps_count=len(steps),
                errors_count=len(errors),
            )
        )

    return summaries


@app.get("/agent/runs/{run_id}")
def get_agent_run(run_id: str) -> dict:
    record = find_agent_run(run_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Agent run not found.",
        )

    return record
