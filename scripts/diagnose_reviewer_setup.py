"""Print safe reviewer setup diagnostics without exposing secrets."""

from __future__ import annotations

from collections.abc import Mapping
import importlib
import os
from pathlib import Path
from typing import Any


Status = dict[str, bool | str]


def collect_status(env: Mapping[str, str] | None = None) -> Status:
    values = os.environ if env is None else env
    dotenv_path = values.get("GPT_HANDOFF_DOTENV_PATH")

    return {
        "package_import_works": _module_importable("gpt_codex_handoff"),
        "reviewer_mode": _reviewer_mode(values.get("GPT_HANDOFF_REVIEWER_MODE")),
        "openai_api_key_present": bool(values.get("OPENAI_API_KEY")),
        "gpt_handoff_dotenv_path_configured": bool(dotenv_path),
        "dotenv_file_exists": bool(dotenv_path) and Path(dotenv_path).is_file(),
        "mcp_server_module_importable": _module_importable("gpt_codex_handoff.mcp_server"),
    }


def print_status(status: Status) -> None:
    labels = [
        ("package_import_works", "package import works"),
        ("reviewer_mode", "GPT_HANDOFF_REVIEWER_MODE"),
        ("openai_api_key_present", "OPENAI_API_KEY present"),
        ("gpt_handoff_dotenv_path_configured", "GPT_HANDOFF_DOTENV_PATH configured"),
        ("dotenv_file_exists", "dotenv file exists"),
        ("mcp_server_module_importable", "MCP server module importable"),
    ]

    for key, label in labels:
        print(f"{label}: {_format_value(status[key])}")


def main() -> None:
    print_status(collect_status())


def _module_importable(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
    except Exception:
        return False
    return True


def _reviewer_mode(value: str | None) -> str:
    if not value:
        return "unset"

    normalized = value.strip().lower()
    if normalized in {"fake", "real"}:
        return normalized
    return "other"


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


if __name__ == "__main__":
    main()
