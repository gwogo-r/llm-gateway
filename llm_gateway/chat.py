"""Единая точка вызова planning-only LLM (OpenRouter/OpenAI Chat Completions).

Не для реального исполнения (файлы/shell) — для этого cli_runner.py
(Claude Code / Codex CLI, списывается с подписки). chat_completion() платит
по цене модели за токен (billing="api") через platform API.
"""
from openai import AsyncOpenAI

from .logger import usage_from_response
from .models import TokenUsage


def strip_code_fence(raw: str) -> str:
    """LLM часто оборачивает JSON-ответ в ```json ... ``` — снимаем перед парсингом."""
    return (
        raw.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )


async def chat_completion(
    *,
    system: str,
    user: str,
    model: str,
    api_key: str,
    base_url: str,
    price_in: float | None = None,
    price_out: float | None = None,
    stage: str = "chat",
    task_id: str | None = None,
    member_id: str | None = None,
    temperature: float = 0,
) -> tuple[str, TokenUsage]:
    """system+user -> (текст ответа, TokenUsage). billing="api" всегда.

    api_key/base_url передаются явно (не читаются из окружения) — вызывающий
    сервис сам решает, откуда брать конфиг (OpenRouter, OpenAI, self-hosted).
    """
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    usage = usage_from_response(
        response,
        stage=stage,
        model=model,
        price_in=price_in,
        price_out=price_out,
        task_id=task_id,
        member_id=member_id,
    )
    text = response.choices[0].message.content or ""
    return text, usage
