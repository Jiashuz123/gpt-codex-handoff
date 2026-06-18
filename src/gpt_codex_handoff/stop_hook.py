"""Small stdin/stdout hook for conservative stop decisions."""

from __future__ import annotations

import json
import sys
from typing import Any

from .context import ReviewContext
from .reviewer import OpenAIReviewer


def recommend_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    context = ReviewContext.from_tool_args(
        summary=payload.get("summary", ""),
        changed_files=payload.get("changed_files"),
        test_results=payload.get("test_results", ""),
        open_questions=payload.get("open_questions"),
        recent_log=payload.get("recent_log", ""),
        diff=payload.get("diff", ""),
        constraints=payload.get("constraints"),
    )
    return OpenAIReviewer().review(context)


def main() -> None:
    payload = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(recommend_from_payload(payload), sort_keys=True))


if __name__ == "__main__":
    main()

