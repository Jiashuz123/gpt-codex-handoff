# GPT Codex Handoff

An MVP MCP server that gives Codex a tool named `ask_gpt_next_step`. Codex can call it during long-running work to ask an OpenAI-powered reviewer for a structured recommendation about what to do next.

Flow:

```text
Codex -> MCP tool ask_gpt_next_step -> OpenAI API reviewer -> strict JSON recommendation
```

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Copy `.env.example` to `.env` or set the variables in your shell:

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:OPENAI_REVIEWER_MODEL = "gpt-4.1-mini"
```

## Run Tests

```powershell
pytest
```

Or, without installing the optional test runner:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

The tests validate schema handling and safety behavior without making real API calls.

## Codex MCP Registration

Register this server as a local MCP command in your Codex configuration:

```toml
[mcp_servers.gpt_codex_handoff]
command = "gpt-codex-handoff"
```

If the package is not installed globally, point Codex at the Python module from this checkout:

```toml
[mcp_servers.gpt_codex_handoff]
command = "python"
args = ["-m", "gpt_codex_handoff.mcp_server"]
env = { OPENAI_API_KEY = "sk-..." }
```

## Tool

`ask_gpt_next_step` accepts:

- `summary`
- `changed_files`
- `test_results`
- `open_questions`
- `recent_log`
- `diff`
- `constraints`

It returns strict JSON:

```json
{
  "next_step": "inspect failing tests",
  "priority": "high",
  "reason": "The current failure blocks verification.",
  "should_continue": true,
  "max_minutes": 15,
  "commands_to_run": ["pytest -q"],
  "files_to_inspect": ["tests/test_example.py"],
  "risk_level": "medium",
  "handoff_note": "Focus on the failing test before editing more code."
}
```

## Example Usage

```python
from gpt_codex_handoff.reviewer import OpenAIReviewer
from gpt_codex_handoff.context import ReviewContext

reviewer = OpenAIReviewer()
recommendation = reviewer.review(
    ReviewContext(
        summary="Implemented first MCP server skeleton.",
        changed_files=["src/gpt_codex_handoff/mcp_server.py"],
        test_results="pytest passes",
        open_questions=[],
        recent_log="No errors.",
        diff="",
        constraints=["Do not commit."]
    )
)
print(recommendation)
```

## Safety

The local preflight check stops before sending context to the API when it sees likely credentials, ambiguous product decisions, high-risk changes, or repeated failures. In those cases the tool returns a conservative JSON recommendation with `should_continue: false`.
