# llm-gateway

[English version](README.md)

![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

Один импорт для любого способа обращения к LLM: **API-вызовы** (OpenRouter/OpenAI chat completions) и **CLI-агенты по подписке** (Claude Code, Codex) — оба возвращают одну и ту же форму `TokenUsage`, поэтому учёт стоимости никогда не превращается в разбор частных случаев по провайдеру.

Библиотека, не сервис — без сервера, без конфиг-файла, только функции.

## Зачем

- **Две разные модели оплаты, один контракт.** API-вызовы стоят реальные деньги за токен (`billing="api"`). CLI-агенты работают по уже оплаченной подписке (`billing="subscription"`) — цифра стоимости там для сравнения, не отдельный счёт. Перепутать их на дашборде — реальный баг, который мы поймали; библиотека держит их различимыми с источника.
- **Путь CLI-агентов несёт реальные, выстраданные фиксы.** Windows давится на `.cmd`-обёртках (WinError 193), `cmd.exe` калечит многострочные промпты и тихо теряет `--json`, Codex по умолчанию в read-only sandbox. Всё это починено один раз здесь, а не заново в каждом проекте.
- **Никаких неожиданных зависаний.** У каждого подпроцесс-вызова есть таймаут, при сбое — `CliAgentError`, а не вечное ожидание или молчаливая ошибка.

## Установка

```bash
pip install llm-gateway
```

Python 3.11+.

## Использование

### API chat completion (OpenRouter / OpenAI)

```python
from llm_gateway import chat_completion

text, usage = await chat_completion(
    system="Ты полезный ассистент.",
    user="Сделай саммари транскрипта митинга.",
    model="openai/gpt-4o",
    api_key="sk-...",
    base_url="https://openrouter.ai/api/v1",
    price_in=2.5, price_out=10.0,   # $/1M токенов, для cost_usd
    stage="extractor",
)
print(usage.cost_usd, usage.billing)  # billing == "api"
```

### Реальное исполнение через CLI-агента по подписке

```python
from llm_gateway import run_claude_code, run_codex

text, usage = await run_claude_code(
    "Напиши unit-тесты для capacity.py", cwd="/path/to/workspace", model="haiku",
)
# usage.billing == "subscription" — cost_usd тут собственная оценка Claude Code,
# не отдельный счёт поверх подписки

text, usage = await run_codex(
    "Напиши unit-тесты для capacity.py", cwd="/path/to/workspace", effort="low",
)
# Codex не публикует $-цифру под подпиской ChatGPT — cost_usd всегда 0.0
```

Обе функции бросают `llm_gateway.CliAgentError`, если бинарник не найден, процесс завершился с ошибкой, или завис дольше 15 минут (убивается автоматически).

## `cwd` — не песочница

`run_claude_code` и `run_codex` запускают настоящего, полноценного кодинг-агента как подпроцесс. Аргумент `cwd` задаёт его рабочую директорию — это **не** файловая тюрьма. Подтверждено прямым тестированием: агент может читать и писать где угодно в пределах прав ОС-пользователя, включая за пределами `cwd` (например, он найдёт editable pip-установку и пойдёт в соседний проект, или запустит `git`, который сам ищет `.git` вверх по родительским папкам и закоммитит в репозиторий выше `cwd`).

Если нужна реальная изоляция агента в конкретной директории — это требует OS-уровня (контейнер, урезанный пользователь, VM); библиотека этого не даёт. Не полагайся на «копию проекта в cwd» как на защиту оригинала — это не так.

## Контракт TokenUsage

```python
class TokenUsage(BaseModel):
    stage: str            # "extractor", "agent_plan", "agent_exec_codex", ...
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    billing: str = "api"   # "api" (реальная оплата) | "subscription" (cost-эквивалент)
    task_id: str | None = None
    member_id: str | None = None
    created_at: datetime
```

Каждая функция библиотеки возвращает `(text, TokenUsage)` — суммируй между вызовами обычной арифметикой, разделяя по `billing`, когда показываешь итоги.

## Windows-фиксы в `run_claude_code` / `run_codex`

| Проблема | Фикс |
|---|---|
| `.cmd`-обёртки (npm-инсталляции CLI) нельзя запустить напрямую — `WinError 193` | Через `cmd.exe /c` |
| `cmd.exe` рвёт командную строку на переносах строк, тихо теряя флаги после них | Переносы строк в аргументах схлопываются в пробел перед сборкой команды |
| npm-глобальный bin не всегда в `PATH`, даже если CLI установлен | Fallback на `%APPDATA%\npm` |
| Файл без расширения рядом с `name.cmd` в npm-папке — шелл-скрипт для WSL/git-bash, не Windows exe | `.cmd`/`.exe` пробуются раньше файла без расширения на Windows |
| Codex `exec` по умолчанию в `sandbox=read-only` — не может писать файлы даже с верным планом | `run_codex` передаёт `--sandbox workspace-write` |
| Зависший процесс агента блокирует вызывающего навсегда | Таймаут 15 минут, процесс убивается, бросается `CliAgentError` |

## Лицензия

MIT
