"""Safe local example that never calls the OpenAI API."""

from __future__ import annotations

import os

from gpt_codex_handoff.context import ReviewContext
from gpt_codex_handoff.reviewer import OpenAIReviewer


def main() -> None:
    os.environ["GPT_HANDOFF_REVIEWER_MODE"] = "fake"
    reviewer = OpenAIReviewer()
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
