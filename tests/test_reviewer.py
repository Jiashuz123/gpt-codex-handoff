from __future__ import annotations

import unittest
from unittest.mock import patch

from gpt_codex_handoff.context import ReviewContext
from gpt_codex_handoff.reviewer import (
    FakeReviewerClient,
    OpenAIResponsesClient,
    OpenAIReviewer,
    validate_recommendation,
)


VALID_RECOMMENDATION = {
    "next_step": "run the focused tests",
    "priority": "high",
    "reason": "The implementation should be verified before more changes.",
    "should_continue": True,
    "max_minutes": 10,
    "commands_to_run": ["pytest -q"],
    "files_to_inspect": ["tests/test_reviewer.py"],
    "risk_level": "low",
    "handoff_note": "Run the focused tests and inspect failures if any appear.",
}


class FakeClient:
    def __init__(self, recommendation=None):
        self.recommendation = recommendation or VALID_RECOMMENDATION
        self.calls = []

    def create_recommendation(self, **kwargs):
        self.calls.append(kwargs)
        return self.recommendation


class ReviewerTests(unittest.TestCase):
    def test_validate_recommendation_accepts_valid_schema(self):
        validate_recommendation(dict(VALID_RECOMMENDATION))

    def test_validate_recommendation_rejects_missing_field(self):
        invalid = dict(VALID_RECOMMENDATION)
        invalid.pop("handoff_note")

        with self.assertRaisesRegex(ValueError, "missing required fields"):
            validate_recommendation(invalid)

    def test_reviewer_calls_client_and_returns_valid_recommendation(self):
        client = FakeClient()
        reviewer = OpenAIReviewer(client=client)

        result = reviewer.review(
            ReviewContext(
                summary="Created MCP server.",
                changed_files=["src/gpt_codex_handoff/mcp_server.py"],
                test_results="not run yet",
            )
        )

        self.assertEqual(result, VALID_RECOMMENDATION)
        self.assertTrue(client.calls)
        self.assertEqual(client.calls[0]["payload"]["summary"], "Created MCP server.")

    def test_reviewer_stops_before_api_when_secret_is_present(self):
        client = FakeClient()
        reviewer = OpenAIReviewer(client=client)

        result = reviewer.review(
            ReviewContext(
                summary="Need to debug config.",
                recent_log="OPENAI_API_KEY=sk-thisshouldnotbesent123456",
            )
        )

        self.assertIs(result["should_continue"], False)
        self.assertEqual(result["risk_level"], "high")
        self.assertIn("credentials", result["reason"])
        self.assertEqual(client.calls, [])

    def test_reviewer_stops_on_ambiguous_product_decision(self):
        client = FakeClient()
        reviewer = OpenAIReviewer(client=client)

        result = reviewer.review(
            ReviewContext(
                summary="Implementation is blocked by an ambiguous product decision.",
            )
        )

        self.assertIs(result["should_continue"], False)
        self.assertEqual(result["risk_level"], "medium")
        self.assertEqual(client.calls, [])

    def test_live_client_requires_api_key_before_importing_openai(self):
        client = OpenAIResponsesClient(api_key=None)

        with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY is required"):
            client.create_recommendation(
                model="test-model",
                system_prompt="Return JSON.",
                payload={"summary": "No API key."},
                schema={},
            )

    def test_real_reviewer_mode_requires_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            reviewer = OpenAIReviewer()

            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY is required"):
                reviewer.review(ReviewContext(summary="No API key in real mode."))

    def test_fake_reviewer_client_response_is_valid(self):
        client = FakeReviewerClient()

        result = client.create_recommendation(
            model="unused",
            system_prompt="unused",
            payload={"summary": "Fake mode.", "changed_files": ["README.md"]},
            schema={},
        )

        validate_recommendation(result)
        self.assertIn("no OpenAI API call was made", result["handoff_note"])


if __name__ == "__main__":
    unittest.main()
