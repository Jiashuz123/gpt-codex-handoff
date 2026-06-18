"""Write repo-local Codex MCP configuration for this project."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import getpass
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


def build_config(python_path: Path, mode: str, dotenv_path: Path | None = None) -> str:
    env_values = [f'GPT_HANDOFF_REVIEWER_MODE = "{mode}"']
    if dotenv_path is not None:
        env_values.append(
            f'GPT_HANDOFF_DOTENV_PATH = "{_toml_string(dotenv_path.resolve())}"'
        )

    lines = [
        f"[mcp_servers.{SERVER_NAME}]",
        f'command = "{_toml_string(python_path)}"',
        f'args = ["-m", "{MODULE_NAME}"]',
        f"env = {{ {', '.join(env_values)} }}",
    ]
    if mode == "real":
        lines.append('env_vars = ["OPENAI_API_KEY"]')
    lines.append("")
    return "\n".join(lines)


def write_config(
    mode: str, start: Path | None = None, dotenv_path: Path | None = None
) -> Path:
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
    config_path.write_text(
        build_config(python_path.resolve(), mode, dotenv_path), encoding="utf-8"
    )
    return config_path


def write_local_env(repo_root: Path, api_key: str) -> Path:
    config_dir = repo_root / ".codex"
    config_dir.mkdir(exist_ok=True)

    dotenv_path = config_dir / ".env"
    dotenv_path.write_text(f"OPENAI_API_KEY={api_key}\n", encoding="utf-8")
    return dotenv_path


def read_or_prompt_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key

    api_key = getpass.getpass("OPENAI_API_KEY: ")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for --write-local-env.")
    return api_key


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Write .codex/config.toml for the gpt-codex-handoff MCP server."
    )
    parser.add_argument("--mode", choices=["fake", "real"], required=True)
    parser.add_argument(
        "--write-local-env",
        action="store_true",
        help="In real mode, write OPENAI_API_KEY to ignored .codex/.env.",
    )
    args = parser.parse_args(argv)

    if args.write_local_env and args.mode != "real":
        parser.error("--write-local-env can only be used with --mode real")

    repo_root = find_repo_root()
    dotenv_path = None
    if args.write_local_env:
        api_key = read_or_prompt_api_key()
        dotenv_path = write_local_env(repo_root, api_key)

    if args.mode == "real" and not os.getenv("OPENAI_API_KEY"):
        if dotenv_path is None:
            print(
                "Warning: OPENAI_API_KEY is not set. Real mode will fail until it is set."
            )

    config_path = write_config(args.mode, repo_root, dotenv_path)
    print(f"Wrote {config_path}")
    if dotenv_path is not None:
        print(f"Wrote local environment file at {dotenv_path}")
    print("Restart Codex, then type /mcp in Codex chat.")


def _toml_string(value: Path) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


if __name__ == "__main__":
    main()
