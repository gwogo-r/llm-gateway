"""TokenUsage — контракт между llm-gateway и вызывающим сервисом. Не ломать:
любой сервис Meldlane, который считает capacity/стоимость, полагается на эту форму."""
from datetime import datetime

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    stage: str  # extractor | agent_plan | agent_exec_claude_code | agent_exec_codex | ...
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    # api: реальная оплата за токен (OpenRouter/OpenAI platform API).
    # subscription: списано с подписки (Claude Pro/Max, ChatGPT); cost_usd тут —
    #   не отдельный счёт, а cost-эквивалент для сравнения (если провайдер его отдаёт).
    billing: str = "api"
    task_id: str | None = None
    member_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
