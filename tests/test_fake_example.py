from __future__ import annotations

import unittest
from unittest.mock import patch

from gpt_codex_handoff.context import ReviewContext
from gpt_codex_handoff.reviewer import OpenAIReviewer, RECOMMENDATION_SCHEMA, validate_recommendation


class FakeExampleTests(unittest.TestCase):
    def test_fake_reviewer_mode_does_not_need_api_key(self):
        with patch.dict(
            "os.environ",
            {"GPT_HANDOFF_REVIEWER_MODE": "fake"},
            clear=True,
        ):
            reviewer = OpenAIReviewer()
            result = reviewer.review(ReviewContext(summary="Local dry run."))

        self.assertEqual(result["next_step"], "verify the MCP wiring in fake reviewer mode")
        self.assertTrue(result["should_continue"])
        self.assertIn("Fake reviewer mode", result["handoff_note"])
        self.assertIn("no OpenAI API call was made", result["handoff_note"])

    def test_fake_reviewer_mode_returns_full_schema(self):
        with patch.dict(
            "os.environ",
            {"GPT_HANDOFF_REVIEWER_MODE": "fake"},
            clear=True,
        ):
            reviewer = OpenAIReviewer()
            result = reviewer.review(
                ReviewContext(
                    summary="Check schema.",
                    changed_files=["README.md", "pyproject.toml"],
                )
            )

        validate_recommendation(result)
        self.assertEqual(set(result), set(RECOMMENDATION_SCHEMA["required"]))


if __name__ == "__main__":
    unittest.main()
