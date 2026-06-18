from __future__ import annotations

import unittest

from examples.fake_reviewer import FakeReviewerClient
from gpt_codex_handoff.context import ReviewContext
from gpt_codex_handoff.reviewer import OpenAIReviewer


class FakeExampleTests(unittest.TestCase):
    def test_fake_reviewer_example_does_not_need_api_key(self):
        reviewer = OpenAIReviewer(client=FakeReviewerClient(), api_key=None)

        result = reviewer.review(ReviewContext(summary="Local dry run."))

        self.assertEqual(result["next_step"], "run the test suite")
        self.assertTrue(result["should_continue"])
        self.assertIn("pytest", result["commands_to_run"])


if __name__ == "__main__":
    unittest.main()
