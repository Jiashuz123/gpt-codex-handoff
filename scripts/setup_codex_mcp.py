"""Write repo-local Codex MCP configuration for this project."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


SERVER_NAME = "gpt_codex_handoff"
MODULE_NAME = "gpt_codex_handoff.mcp_server"


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    candidates = [current, *current.parents]

    for candidate in candidates:
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "src" / "gpt_codex_handoff"
        ).is_dir():
            return candidate

    raise RuntimeError("Could not find the gpt-codex-handoff repository root.")


def venv_python_path(repo_root: Path) -> Path:
    return repo_root / ".venv" / "Scripts" / "python.exe"


def build_config(python_path: Path, mode: str) -> str:
    lines = [
        f"[mcp_servers.{SERVER_NAME}]",
        f'command = "{_toml_string(python_path)}"',
        f'args = ["-m", "{MODULE_NAME}"]',
        f'env = {{ GPT_HANDOFF_REVIEWER_MODE = "{mode}" }}',
    ]
    if mode == "real":
        lines.append('env_vars = ["OPENAI_API_KEY"]')
    lines.append("")
    return "\n".join(lines)


def write_config(mode: str, start: Path | None = None) -> Path:
    repo_root = find_repo_root(start)
    python_path = venv_python_path(repo_root)

    if not python_path.is_file():
        raise RuntimeError(
            f"Expected virtual environment Python at {python_path}. "
            "Create it with: python -m venv .venv"
        )

    config_dir = repo_root / ".codex"
    config_dir.mkdir(exist_ok=True)

    config_path = config_dir / "config.toml"
    config_path.write_text(build_config(python_path.resolve(), mode), encoding="utf-8")
    return config_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write .codex/config.toml for the gpt-codex-handoff MCP server."
    )
    parser.add_argument("--mode", choices=["fake", "real"], required=True)
    args = parser.parse_args()

    if args.mode == "real" and not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY is not set. Real mode will fail until it is set.")

    config_path = write_config(args.mode)
    print(f"Wrote {config_path}")
    print("Restart Codex, then type /mcp in Codex chat.")


def _toml_string(value: Path) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


if __name__ == "__main__":
    main()
