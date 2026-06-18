from __future__ import annotations

from pathlib import Path

import pytest

from scripts.setup_codex_mcp import build_config, find_repo_root, write_config


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "src" / "gpt_codex_handoff").mkdir(parents=True)
    (repo / ".venv" / "Scripts").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")
    (repo / ".venv" / "Scripts" / "python.exe").write_text("", encoding="utf-8")
    return repo


def test_find_repo_root_from_nested_path(tmp_path: Path):
    repo = make_repo(tmp_path)
    nested = repo / "src" / "gpt_codex_handoff"

    assert find_repo_root(nested) == repo


def test_write_config_fake_mode(tmp_path: Path):
    repo = make_repo(tmp_path)

    config_path = write_config("fake", repo)

    assert config_path == repo / ".codex" / "config.toml"
    content = config_path.read_text(encoding="utf-8")
    assert "[mcp_servers.gpt_codex_handoff]" in content
    assert 'args = ["-m", "gpt_codex_handoff.mcp_server"]' in content
    assert 'env = { GPT_HANDOFF_REVIEWER_MODE = "fake" }' in content
    assert "\\\\.venv\\\\Scripts\\\\python.exe" in content


def test_write_config_requires_venv_python(tmp_path: Path):
    repo = make_repo(tmp_path)
    (repo / ".venv" / "Scripts" / "python.exe").unlink()

    with pytest.raises(RuntimeError, match="Expected virtual environment Python"):
        write_config("fake", repo)


def test_build_config_real_mode():
    content = build_config(Path(r"C:\repo\.venv\Scripts\python.exe"), "real")

    assert 'env = { GPT_HANDOFF_REVIEWER_MODE = "real" }' in content
    assert 'command = "C:\\\\repo\\\\.venv\\\\Scripts\\\\python.exe"' in content
