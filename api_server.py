import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

from llm_client import (
    ChatMessage,
    ConfigError,
    LLMAPIError,
    LLMResponseError,
    Role,
    call_llm,
)


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
