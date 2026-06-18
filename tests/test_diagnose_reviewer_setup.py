from __future__ import annotations

from pathlib import Path

from scripts.diagnose_reviewer_setup import collect_status, print_status


def test_collect_status_reports_safe_booleans(tmp_path: Path):
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("OPENAI_API_KEY=test-secret-value\n", encoding="utf-8")

    status = collect_status(
        {
            "GPT_HANDOFF_REVIEWER_MODE": "real",
            "OPENAI_API_KEY": "test-secret-value",
            "GPT_HANDOFF_DOTENV_PATH": str(dotenv_path),
        }
    )

    assert status["package_import_works"] is True
    assert status["reviewer_mode"] == "real"
    assert status["openai_api_key_present"] is True
    assert status["gpt_handoff_dotenv_path_configured"] is True
    assert status["dotenv_file_exists"] is True
    assert status["mcp_server_module_importable"] is True


def test_collect_status_handles_missing_environment():
    status = collect_status({})

    assert status["reviewer_mode"] == "unset"
    assert status["openai_api_key_present"] is False
    assert status["gpt_handoff_dotenv_path_configured"] is False
    assert status["dotenv_file_exists"] is False


def test_collect_status_does_not_echo_unexpected_mode():
    status = collect_status({"GPT_HANDOFF_REVIEWER_MODE": "do-not-print-this"})

    assert status["reviewer_mode"] == "other"


def test_print_status_never_outputs_secret_values(tmp_path: Path, capsys):
    dotenv_path = tmp_path / ".env"
    secret = "test-secret-value"
    dotenv_path.write_text(f"OPENAI_API_KEY={secret}\n", encoding="utf-8")
    status = collect_status(
        {
            "GPT_HANDOFF_REVIEWER_MODE": "fake",
            "OPENAI_API_KEY": secret,
            "GPT_HANDOFF_DOTENV_PATH": str(dotenv_path),
        }
    )

    print_status(status)

    output = capsys.readouterr().out
    assert "OPENAI_API_KEY present: true" in output
    assert "GPT_HANDOFF_DOTENV_PATH configured: true" in output
    assert "dotenv file exists: true" in output
    assert secret not in output
    assert str(dotenv_path) not in output
    assert "OPENAI_API_KEY=" not in output
