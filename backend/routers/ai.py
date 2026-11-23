"""POST /api/ai/chat: grounded labour-market assistant."""

import logging
import os
import time
from collections import defaultdict, deque
from typing import Any, Deque, Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from services.ai_context import build_chat_context
from services.ai_service import AIServiceError, generate_answer, llm_status

logger = logging.getLogger("skillpulse.ai.router")

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])

MAX_HISTORY = 12


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: List[ChatTurn] = Field(default_factory=list)


class ChatResponse(BaseModel):
    success: bool
    answer: str
    sources: List[Dict[str, Any]]
    data_timestamp: Optional[str] = None
    data_retrieved_at: str
    focus_states: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)


class SlidingWindowLimiter:
    """Small in-memory per-client limiter (single-process deployments)."""

    def __init__(self, max_calls: int, window_seconds: int = 60) -> None:
        self.max_calls = max_calls
        self.window = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def check(self, key: str) -> Optional[int]:
        now = time.monotonic()
        hits = self._hits[key]
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) >= self.max_calls:
            return max(1, int(self.window - (now - hits[0])))
        hits.append(now)
        return None


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


_limiter = SlidingWindowLimiter(_int_env("AI_RATE_LIMIT_PER_MINUTE", 15))


def _enforce_rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    retry_after = _limiter.check(client)
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment and try again.",
            headers={"Retry-After": str(retry_after)},
        )


def _prepare(payload: ChatRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Please enter a question.")
    history = [(t.role, t.content) for t in payload.history[-MAX_HISTORY:]]
    return question, history


@router.get("/health")
def ai_health():
    return {"status": "ok", **llm_status()}


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request):
    _enforce_rate_limit(request)
    question, history = _prepare(payload)
    try:
        context = await build_chat_context(question, history)
        answer = await generate_answer(question, history, context.text)
    except AIServiceError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error in /api/ai/chat")
        raise HTTPException(
            status_code=500, detail="Unexpected error while generating the answer."
        )

    return ChatResponse(
        success=True,
        answer=answer,
        sources=context.sources,
        data_timestamp=context.data_timestamp,
        data_retrieved_at=context.retrieved_at,
        focus_states=context.states,
        topics=context.topics,
    )


@router.post("/debug-context")
async def debug_context(payload: ChatRequest, request: Request):
    """Shows what data the LLM would receive. Off unless AI_DEBUG_CONTEXT=true."""
    if os.getenv("AI_DEBUG_CONTEXT", "").strip().lower() not in {"1", "true", "yes"}:
        raise HTTPException(status_code=404, detail="Not found")
    _enforce_rate_limit(request)
    question, history = _prepare(payload)
    context = await build_chat_context(question, history)
    return {
        "focus_states": context.states,
        "topics": context.topics,
        "sources": context.sources,
        "context_text": context.text,
    }