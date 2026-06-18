"""Safe local example that never calls the OpenAI API."""

from __future__ import annotations

from gpt_codex_handoff.context import ReviewContext
from gpt_codex_handoff.reviewer import OpenAIReviewer


class FakeReviewerClient:
    def create_recommendation(self, **kwargs):
        return {
            "next_step": "run the test suite",
            "priority": "high",
            "reason": "The skeleton should be verified locally before using a live API key.",
            "should_continue": True,
            "max_minutes": 5,
            "commands_to_run": ["pytest"],
            "files_to_inspect": ["README.md", "pyproject.toml"],
            "risk_level": "low",
            "handoff_note": "This recommendation came from a fake client; no API call was made.",
        }


def main() -> None:
    reviewer = OpenAIReviewer(client=FakeReviewerClient())
    recommendation = reviewer.review(
        ReviewContext(
            summary="Trying the reviewer locally without a real API key.",
            changed_files=["README.md"],
            test_results="not run yet",
            open_questions=[],
            recent_log="No errors.",
            diff="",
            constraints=["Do not commit."],
        )
    )
    print(recommendation)


if __name__ == "__main__":
    main()
