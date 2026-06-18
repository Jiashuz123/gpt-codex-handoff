from __future__ import annotations

import unittest
from unittest.mock import patch

from gpt_codex_handoff import mcp_server


class MCPServerTests(unittest.TestCase):
    def test_ask_gpt_next_step_tool_uses_reviewer(self):
        expected = {
            "next_step": "run tests",
            "priority": "high",
            "reason": "Verification is the next useful step.",
            "should_continue": True,
            "max_minutes": 5,
            "commands_to_run": ["pytest -q"],
            "files_to_inspect": [],
            "risk_level": "low",
            "handoff_note": "Run the test suite.",
        }

        class FakeReviewer:
            def review(self, context):
                self_context = context
                assert self_context.summary == "Skeleton created"
                assert self_context.changed_files == ["README.md"]
                return expected

        with patch.object(mcp_server, "OpenAIReviewer", lambda: FakeReviewer()):
            result = mcp_server.ask_gpt_next_step(
                summary="Skeleton created",
                changed_files=["README.md"],
                test_results="not run",
                open_questions=[],
                recent_log="",
                diff="",
                constraints=["Do not commit."],
            )

        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
