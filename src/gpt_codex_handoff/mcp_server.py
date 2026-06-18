"""MCP server exposing ask_gpt_next_step."""

from __future__ import annotations

from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - exercised only before package install
    class FastMCP:  # type: ignore[no-redef]
        def __init__(self, name: str) -> None:
            self.name = name

        def tool(self):
            def decorator(func):
                return func

            return decorator

        def run(self) -> None:
            raise RuntimeError("The 'mcp' package is required to run the MCP server.")

from .context import ReviewContext
from .reviewer import OpenAIReviewer, Recommendation


mcp = FastMCP("gpt-codex-handoff")


@mcp.tool()
def ask_gpt_next_step(
    summary: str,
    changed_files: list[str] | str | None = None,
    test_results: str = "",
    open_questions: list[str] | str | None = None,
    recent_log: str = "",
    diff: str = "",
    constraints: list[str] | str | None = None,
) -> Recommendation:
    """Ask the GPT reviewer for a strict JSON next-step recommendation."""

    context = ReviewContext.from_tool_args(
        summary=summary,
        changed_files=changed_files,
        test_results=test_results,
        open_questions=open_questions,
        recent_log=recent_log,
        diff=diff,
        constraints=constraints,
    )
    return OpenAIReviewer().review(context)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
