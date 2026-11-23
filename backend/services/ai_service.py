"""Optional LLM-backed answers for the SkillPulse assistant."""

from __future__ import annotations

import logging
import os
from typing import Sequence

from dotenv import load_dotenv
from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI

load_dotenv()

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are SkillPulse Intelligence Assistant.

SkillPulse AI is an Indian Labour Market Intelligence platform.

Your responsibilities:
1. Explain state-wise skill gaps.
2. Analyse employment trends.
3. Explain sector-wise skill requirements.
4. Interpret employment forecasts.
5. Provide evidence-based recommendations.
6. Help policymakers understand labour market challenges.

IMPORTANT RULES:
- Use only the supplied analytical context for factual project-specific statistics.
- Never invent employment statistics or forecasting results.
- Clearly distinguish actual observations from predictions.
- Explain limitations when data is unavailable.
- Give practical and understandable recommendations.
- If information is insufficient, explicitly say so.
"""


class AIServiceError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _provider_error_message(status_code: int | None) -> str:
    if status_code in {401, 403}:
        return (
            "The AI provider rejected the API key or account permissions. "
            "Check that the replacement key is active and has model access."
        )
    if status_code == 404:
        return (
            "The AI model was not found or is unavailable to this account. "
            "Check the LLM_MODEL value and model access."
        )
    if status_code == 429:
        return (
            "The AI provider rate limit or usage quota was reached. "
            "Check provider billing and usage limits."
        )
    if status_code == 400:
        return (
            "The AI provider rejected the request. Check that the selected "
            "model supports chat completions."
        )
    if status_code is not None:
        return (
            f"The AI provider returned HTTP {status_code}. "
            "Check provider settings and backend logs."
        )
    return "The AI provider could not generate a response. Check provider settings."


def _settings() -> tuple[str, str, str | None]:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "").strip() or None
    if not api_key or not model:
        raise AIServiceError(
            503,
            "The AI assistant is not configured. Set LLM_API_KEY and LLM_MODEL to enable chat.",
        )
    return api_key, model, base_url


def llm_status() -> dict[str, str | bool]:
    return {
        "configured": bool(
            os.getenv("LLM_API_KEY", "").strip()
            and os.getenv("LLM_MODEL", "").strip()
        ),
        "provider": os.getenv("LLM_PROVIDER", "openai-compatible"),
        "model": os.getenv("LLM_MODEL", "").strip(),
    }


async def generate_answer(
    question: str,
    history: Sequence[tuple[str, str]],
    context: str,
) -> str:
    api_key, model, base_url = _settings()
    client = AsyncOpenAI(api_key=api_key, base_url=base_url or None)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(
        {"role": role, "content": content}
        for role, content in history
        if role in {"user", "assistant"}
    )
    messages.append({
        "role": "user",
        "content": f"ANALYTICAL CONTEXT:\n\n{context}\n\nUSER QUESTION:\n\n{question}",
    })

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
        )
    except (APIConnectionError, APITimeoutError) as error:
        raise AIServiceError(
            503, "The AI provider could not be reached. Please try again later."
        ) from error
    except APIError as error:
        status_code = getattr(error, "status_code", None)
        if not isinstance(status_code, int):
            status_code = None
        logger.warning(
            "AI provider request failed (HTTP %s)",
            status_code or "unknown",
        )
        raise AIServiceError(502, _provider_error_message(status_code)) from error

    answer = response.choices[0].message.content
    if not answer:
        raise AIServiceError(502, "The AI provider returned an empty response.")
    return answer


async def ask_ai(question: str, context: str = "") -> str:
    """Keep compatibility with the original single-turn helper."""
    return await generate_answer(question, [], context)
