# llm-gateway

[Русская версия](README.ru.md)

![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

One import for every way your code talks to an LLM: **API calls** (OpenRouter/OpenAI chat completions) and **subscription-based CLI agents** (Claude Code, Codex) — both returning the same `TokenUsage` shape, so cost tracking never has to special-case the provider.

A library, not a service — no server, no config file, just functions.

## Why

- **Two very different billing models, one contract.** API calls cost real money per token (`billing="api"`). CLI agents run against a subscription you already pay for (`billing="subscription"`) — the cost you see there is a cost-equivalent for comparison, not a separate charge. Mixing them up in a dashboard is a real bug we hit; this library keeps them distinguishable from the source.
- **The CLI agent path carries real, hard-won fixes.** Windows chokes on `.cmd` shims (WinError 193), `cmd.exe` mangles multi-line prompts and silently drops `--json`, Codex defaults to a read-only sandbox. All fixed here once instead of rediscovered per project.
- **No surprise hangs.** Every subprocess call has a timeout and raises `CliAgentError` instead of hanging forever or failing silently.

## Install

```bash
pip install llm-gateway
```

Python 3.11+.

## Usage

### API chat completion (OpenRouter / OpenAI)

```python
from llm_gateway import chat_completion

text, usage = await chat_completion(
    system="You are a helpful assistant.",
    user="Summarize this meeting transcript.",
    model="openai/gpt-4o",
    api_key="sk-...",
    base_url="https://openrouter.ai/api/v1",
    price_in=2.5, price_out=10.0,   # $/1M tokens, for cost_usd
    stage="extractor",
)
print(usage.cost_usd, usage.billing)  # billing == "api"
```

### Real execution via a subscription CLI agent

```python
from llm_gateway import run_claude_code, run_codex

text, usage = await run_claude_code(
    "Write unit tests for capacity.py", cwd="/path/to/workspace", model="haiku",
)
# usage.billing == "subscription" -- cost_usd here is Claude Code's own
# reported cost-equivalent, not a separate charge on top of your plan

text, usage = await run_codex(
    "Write unit tests for capacity.py", cwd="/path/to/workspace", effort="low",
)
# Codex doesn't report a $ figure under a ChatGPT subscription -- cost_usd is 0.0
```

Both raise `llm_gateway.CliAgentError` if the binary is missing, the process exits non-zero, or it hangs past a 15-minute timeout (killed automatically).

## The TokenUsage contract

```python
class TokenUsage(BaseModel):
    stage: str            # "extractor", "agent_plan", "agent_exec_codex", ...
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    billing: str = "api"   # "api" (real charge) | "subscription" (cost-equivalent)
    task_id: str | None = None
    member_id: str | None = None
    created_at: datetime
```

Every function in this library returns `(text, TokenUsage)` — aggregate across calls with plain arithmetic, splitting by `billing` when you display totals.

## Windows fixes carried by `run_claude_code` / `run_codex`

| Problem | Fix |
|---|---|
| `.cmd` shims (npm-installed CLIs) can't be exec'd directly — `WinError 193` | Routed through `cmd.exe /c` |
| `cmd.exe` splits the command line on embedded newlines, silently dropping flags after them | Newlines in arguments are collapsed to spaces before building the command |
| npm global bin dir not always on `PATH` even when the CLI is installed | Falls back to `%APPDATA%\npm` |
| A bare-name file next to `name.cmd` in the npm folder is a WSL/git-bash shell script, not a Windows exe | `.cmd`/`.exe` are tried before the extension-less name on Windows |
| Codex `exec` defaults to `sandbox=read-only` — can't write files even with a correct plan | `run_codex` passes `--sandbox workspace-write` |
| A hung agent process blocks the caller forever | 15-minute timeout, process is killed and `CliAgentError` raised |

## License

MIT
