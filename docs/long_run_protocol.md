# Long Run Protocol

This protocol explains how to use `ask_gpt_next_step` as a checkpoint tool during long Codex sessions. The reviewer is a second-pass planning aid, not an autopilot. Codex should still inspect the repo, run local checks, protect secrets, and stop when the evidence says the task is unsafe or underspecified.

Use fake mode for wiring tests. Use real mode only after the MCP server is configured, billing is active, and `.codex/.env` is present locally when needed. Do not paste API keys or other secrets into prompts, logs, diffs, or reviewer inputs.

## When To Call The Reviewer

Call `ask_gpt_next_step` at meaningful decision points:

- After meaningful code changes, before continuing into the next implementation chunk.
- After test failures, especially when the failure changes the likely plan.
- Before large refactors, migrations, broad rewrites, or cross-module API changes.
- Before touching credentials, config, deployment, CI/CD, billing, auth, or production-like files.
- Every 20-40 minutes during long work, even if everything appears healthy.
- At the end of a trial, with a concise summary, changed files, tests run, open questions, and known risks.

Keep reviewer inputs brief and sanitized. Include file names, test results, and summarized logs, but remove secrets, tokens, account identifiers, private URLs, and unrelated chat history.

## Stop Conditions

Stop and ask the user for direction when any of these happen:

- The workspace is the wrong repo, missing the repo, missing `.git`, or missing the files the task depends on.
- A product decision is unclear and guessing would shape user-facing behavior.
- Credentials are needed, a secret appears in context, or continuing would require inspecting or exposing private values.
- The task touches high-risk files such as auth, billing, deployment, production config, migrations, security policy, destructive data operations, or release automation.
- The same issue fails repeatedly after reasonable focused attempts.
- The reviewer returns `should_continue=false`.
- The implementation path would require making a live API call, spending money, deleting data, or changing external state beyond what the user authorized.

When stopping, summarize the current evidence, the exact blocker, files changed, tests run, and the smallest question the user needs to answer.

## Mission Prompt Templates

Use `python -m pytest` for Windows test commands so the active Python environment chooses the pytest module directly. Prefer a repo-local temp directory such as:

```powershell
python -m pytest --basetemp=".venv\pytest-tmp"
```

If pytest reports `PermissionError: Access is denied` under `AppData\Local\Temp\pytest-of-...`, rerun with `--basetemp` pointing at a repo-local directory. If that repo-local temp directory is locked, close stale Python or Codex processes or choose a fresh path such as `.venv\pytest-tmp-trial`.

### 30-Minute Trial

```text
Run a controlled 30-minute autonomous trial in this repo.

Mission:
- Work only on the specific small task I give below.
- Inspect the current repo state before editing.
- Keep changes narrow and reversible.
- Do not commit.
- Do not make live external API calls unless I explicitly authorize them.
- Do not inspect, print, or expose secrets.

Reviewer checkpoints:
- Call ask_gpt_next_step after meaningful code changes.
- Call it after any test failure before trying a second fix.
- Call it before touching credentials, config, deployment, auth, billing, or CI.
- Call it at the end of the 30-minute trial.

Stop immediately if:
- This is the wrong repo or required files are missing.
- The product decision is unclear.
- Credentials are needed.
- High-risk files would need changes.
- The same issue fails twice.
- The reviewer says should_continue=false.

Verification:
- Run focused tests for the touched area.
- If practical, run the repo's standard Windows-safe test command:
  python -m pytest --basetemp=".venv\pytest-tmp"

Final response:
- Summarize files changed.
- Summarize tests run.
- Report reviewer checkpoints and decisions.
- List any remaining risks or follow-ups.

Task:
<insert one small, concrete task here>
```

### 1-Hour Trial

```text
Run a controlled 1-hour autonomous trial in this repo.

Mission:
- Work on the task below in small checkpoints.
- Inspect current repo state before editing.
- Prefer existing patterns over new abstractions.
- Keep changes scoped to the requested behavior.
- Do not commit.
- Do not make live external API calls unless I explicitly authorize them.
- Do not inspect, print, or expose secrets.

Reviewer checkpoints:
- Call ask_gpt_next_step after each meaningful implementation chunk.
- Call it after test failures before changing strategy.
- Call it before large refactors or shared API changes.
- Call it before touching credentials, config, deployment, auth, billing, CI, or release files.
- Call it every 20-40 minutes during the run.
- Call it before the final summary.

Stop immediately if:
- This is the wrong repo or required files are missing.
- A product decision is unclear.
- Credentials are needed.
- High-risk files would need changes.
- The same issue fails twice.
- The reviewer says should_continue=false.

Verification:
- Run focused tests after each completed chunk when available.
- Run the repo's standard Windows-safe test command near the end if the changes warrant it:
  python -m pytest --basetemp=".venv\pytest-tmp"

Final response:
- Summarize files changed.
- Summarize tests run.
- Report reviewer checkpoints and decisions.
- Identify remaining risks and the next best task.

Task:
<insert a medium-sized, clearly scoped task here>
```

### 3-5-Hour Unattended Run

```text
Run a controlled 3-5-hour unattended session in this repo.

Mission:
- Work through the task below in small, reviewable chunks.
- Inspect current repo state before editing.
- Maintain a concise running log of decisions, files changed, tests run, and blockers.
- Prefer existing project patterns and avoid broad rewrites unless the reviewer confirms the plan.
- Do not commit unless I explicitly authorize it.
- Do not make live external API calls unless I explicitly authorize them.
- Do not inspect, print, or expose secrets.
- Avoid destructive commands and external-state changes.

Reviewer checkpoints:
- Call ask_gpt_next_step after each meaningful implementation chunk.
- Call it after any test failure before trying another fix.
- Call it before large refactors, migrations, shared API changes, or dependency changes.
- Call it before touching credentials, config, deployment, auth, billing, CI, release, or security-sensitive files.
- Call it every 20-40 minutes even if work is going smoothly.
- Call it before final verification and before the final summary.

Stop immediately if:
- This is the wrong repo or required files are missing.
- A product decision is unclear.
- Credentials are needed.
- High-risk files would need changes.
- The same issue fails twice.
- The reviewer says should_continue=false.
- The task would require spending money, using a live service, deleting data, or changing external state beyond this prompt.

Verification:
- Run focused tests after each completed chunk when available.
- Run broader tests before the final summary if feasible:
  python -m pytest --basetemp=".venv\pytest-tmp"
- If tests cannot run, record the exact reason and avoid claiming success.

Final response:
- Summarize files changed.
- Summarize tests run.
- Report reviewer checkpoints and decisions.
- State what was completed, what was deferred, and why.
- Provide the next safest follow-up task.

Task:
<insert a larger but still bounded task here>
```

## First Real Trial

Use this repository itself as the first target. The first real trial should last 30 minutes and should avoid live API calls unless the task is specifically to test the reviewer. A good first target is documentation or a small test-only improvement because it exercises repo inspection, editing, tests, and reviewer checkpoints without touching credentials or deployment.

Recommended first task:

```text
Improve the project documentation for long-running Codex sessions. Keep the change docs-only, do not call live APIs, run tests if available, and stop if the repo state is not clean or the reviewer advises stopping.
```

Success for the first trial means Codex:

- Inspects repo state before editing.
- Makes a small, understandable change.
- Calls the reviewer at least once after the meaningful change or before finalizing.
- Runs the requested local verification.
- Stops cleanly with a concise summary and no commit.
