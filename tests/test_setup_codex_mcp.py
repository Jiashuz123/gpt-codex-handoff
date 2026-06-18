from __future__ import annotations

from pathlib import Path

import pytest

from scripts.setup_codex_mcp import build_config, find_repo_root, main, write_config


ROOT = Path(__file__).resolve().parents[1]


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
    assert "env_vars" not in content
    assert "OPENAI_API_KEY" not in content
    assert "\\\\.venv\\\\Scripts\\\\python.exe" in content


def test_write_config_requires_venv_python(tmp_path: Path):
    repo = make_repo(tmp_path)
    (repo / ".venv" / "Scripts" / "python.exe").unlink()

    with pytest.raises(RuntimeError, match="Expected virtual environment Python"):
        write_config("fake", repo)


def test_build_config_real_mode():
    content = build_config(Path(r"C:\repo\.venv\Scripts\python.exe"), "real")

    assert 'env = { GPT_HANDOFF_REVIEWER_MODE = "real" }' in content
    assert 'env_vars = ["OPENAI_API_KEY"]' in content
    assert 'command = "C:\\\\repo\\\\.venv\\\\Scripts\\\\python.exe"' in content


def test_build_config_real_mode_with_dotenv_path():
    content = build_config(
        Path(r"C:\repo\.venv\Scripts\python.exe"),
        "real",
        Path(r"C:\repo\.codex\.env"),
    )

    assert (
        'env = { GPT_HANDOFF_REVIEWER_MODE = "real", '
        'GPT_HANDOFF_DOTENV_PATH = "C:\\\\repo\\\\.codex\\\\.env" }'
    ) in content
    assert 'env_vars = ["OPENAI_API_KEY"]' in content


def test_build_config_does_not_write_secret_value():
    content = build_config(Path(r"C:\repo\.venv\Scripts\python.exe"), "real")

    assert "SHOULD_NOT_APPEAR_SECRET_VALUE" not in content
    assert "OPENAI_API_KEY =" not in content


def test_main_writes_local_env_without_printing_secret(tmp_path: Path, monkeypatch, capsys):
    repo = make_repo(tmp_path)
    secret = "test-secret-value"

    monkeypatch.chdir(repo)
    monkeypatch.setenv("OPENAI_API_KEY", secret)

    main(["--mode", "real", "--write-local-env"])

    dotenv_path = repo / ".codex" / ".env"
    config_path = repo / ".codex" / "config.toml"
    assert dotenv_path.read_text(encoding="utf-8") == f"OPENAI_API_KEY={secret}\n"

    config = config_path.read_text(encoding="utf-8")
    assert "GPT_HANDOFF_DOTENV_PATH" in config
    assert 'env_vars = ["OPENAI_API_KEY"]' in config
    assert secret not in config

    output = capsys.readouterr().out
    assert "Wrote" in output
    assert secret not in output


def test_codex_directory_is_ignored():
    gitignore = ROOT / ".gitignore"

    assert ".codex/" in gitignore.read_text(encoding="utf-8").splitlines()
