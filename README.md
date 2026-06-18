# GPT Codex Handoff

An MVP MCP server that gives Codex a tool named `ask_gpt_next_step`. Codex can call it during long-running work to ask an OpenAI-powered reviewer for a structured recommendation about what to do next.

Flow:

```text
Codex -> MCP tool ask_gpt_next_step -> OpenAI API reviewer -> strict JSON recommendation
```

## Windows Setup

From a fresh checkout on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run the tests:

```powershell
pytest
```

PowerShell can treat brackets as wildcard syntax in some contexts, so keep `".[dev]"` quoted.

## Environment

Fake reviewer mode is for local wiring tests. It returns valid recommendation JSON without importing the OpenAI client, without requiring `OPENAI_API_KEY`, and without contacting OpenAI:

```powershell
$env:GPT_HANDOFF_REVIEWER_MODE = "fake"
```

Live reviewer calls require `OPENAI_API_KEY` and must not use fake mode.

Copy `.env.example` to `.env` for your own notes, or set variables in the shell that launches Codex:

```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:OPENAI_REVIEWER_MODEL = "gpt-4.1-mini"
```

Do not paste secrets into tool inputs, logs, diffs, or test fixtures.

## Codex MCP Registration

After installing the package in the same environment Codex will use, register this server as a local MCP command in your Codex configuration:

```toml
[mcp_servers.gpt_codex_handoff]
command = "gpt-codex-handoff"
```

For a repository-local virtual environment on Windows, point Codex at that Python executable:

```toml
[mcp_servers.gpt_codex_handoff]
command = "C:\\path\\to\\gpt-codex-handoff\\.venv\\Scripts\\python.exe"
args = ["-m", "gpt_codex_handoff.mcp_server"]
env = { OPENAI_API_KEY = "sk-...", OPENAI_REVIEWER_MODEL = "gpt-4.1-mini" }
```

For this checkout, replace the command path with:

```toml
command = "C:\\Users\\jiash\\OneDrive\\Documents\\GPT CodeX integration\\.venv\\Scripts\\python.exe"
```

Restart Codex after changing MCP configuration so it can discover `ask_gpt_next_step`.

### Fake Mode Registration

For the first Codex wiring test, register the MCP server in fake mode and do not set `OPENAI_API_KEY`:

```toml
[mcp_servers.gpt_codex_handoff]
command = "C:\\Users\\jiash\\OneDrive\\Documents\\GPT CodeX integration\\.venv\\Scripts\\python.exe"
args = ["-m", "gpt_codex_handoff.mcp_server"]
env = { GPT_HANDOFF_REVIEWER_MODE = "fake" }
```

Restart Codex, then type `/mcp` in Codex chat. You should see `gpt_codex_handoff` as enabled. Some Codex UI versions show only the server row rather than an expandable tool list.

After `/mcp` shows the server, you can safely ask Codex to call the tool:

```text
Call ask_gpt_next_step with summary="Fake-mode wiring test", changed_files=[], test_results="not run", open_questions=[], recent_log="", diff="", constraints=["Do not call OpenAI."]
```

The response should include a `handoff_note` saying fake reviewer mode is enabled and no OpenAI API call was made.

Fake mode is only for wiring tests. It does not evaluate the session with a real model.

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

### Safe Fake Reviewer

This example uses `GPT_HANDOFF_REVIEWER_MODE=fake` and does not need `OPENAI_API_KEY`:

```powershell
python examples\fake_reviewer.py
```

The same pattern is useful in tests:

```python
import os

from gpt_codex_handoff.context import ReviewContext
from gpt_codex_handoff.reviewer import OpenAIReviewer


os.environ["GPT_HANDOFF_REVIEWER_MODE"] = "fake"
reviewer = OpenAIReviewer()
print(reviewer.review(ReviewContext(summary="Local dry run.")))
```

### Live Reviewer

Unset `GPT_HANDOFF_REVIEWER_MODE` and set `OPENAI_API_KEY` first. Live calls send the provided context to the OpenAI API after the local safety preflight passes.

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
