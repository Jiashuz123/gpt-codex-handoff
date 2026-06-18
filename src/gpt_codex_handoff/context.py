"""Context and safety preflight helpers for reviewer calls."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any


class SafetyStop(Exception):
    """Raised when context should not be sent to the reviewer."""

    def __init__(self, reason: str, risk_level: str = "high") -> None:
        super().__init__(reason)
        self.reason = reason
        self.risk_level = risk_level


_SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bOPENAI_API_KEY\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"\b[A-Z0-9_]*(TOKEN|SECRET|PASSWORD|API_KEY)\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]

_HIGH_RISK_TERMS = [
    "auth",
    "authentication",
    "authorization",
    "billing",
    "payment",
    "production deploy",
    "prod deploy",
    "database migration",
    "drop table",
    "delete all",
    "security",
]

_AMBIGUOUS_PRODUCT_TERMS = [
    "ambiguous product",
    "unclear product",
    "product decision",
    "needs product input",
]

_REPEATED_FAILURE_TERMS = [
    "repeated failure",
    "same failure",
    "failed again",
    "third failure",
    "stuck",
]


@dataclass(frozen=True)
class ReviewContext:
    """The information Codex sends to the reviewer."""

    summary: str
    changed_files: list[str] = field(default_factory=list)
    test_results: str = ""
    open_questions: list[str] = field(default_factory=list)
    recent_log: str = ""
    diff: str = ""
    constraints: list[str] = field(default_factory=list)

    @classmethod
    def from_tool_args(
        cls,
        summary: str,
        changed_files: list[str] | str | None = None,
        test_results: str = "",
        open_questions: list[str] | str | None = None,
        recent_log: str = "",
        diff: str = "",
        constraints: list[str] | str | None = None,
    ) -> "ReviewContext":
        return cls(
            summary=summary,
            changed_files=_coerce_list(changed_files),
            test_results=test_results,
            open_questions=_coerce_list(open_questions),
            recent_log=recent_log,
            diff=diff,
            constraints=_coerce_list(constraints),
        )

    def as_payload(self) -> dict[str, Any]:
        self.check_safety()
        return asdict(self)

    def combined_text(self) -> str:
        values = [
            self.summary,
            *self.changed_files,
            self.test_results,
            *self.open_questions,
            self.recent_log,
            self.diff,
            *self.constraints,
        ]
        return "\n".join(value for value in values if value)

    def check_safety(self) -> None:
        text = self.combined_text()
        lower_text = text.lower()

        if any(pattern.search(text) for pattern in _SECRET_PATTERNS):
            raise SafetyStop("Possible credentials or secrets were found in the context.")

        if any(term in lower_text for term in _AMBIGUOUS_PRODUCT_TERMS):
            raise SafetyStop("The next step depends on an ambiguous product decision.", "medium")

        if any(term in lower_text for term in _HIGH_RISK_TERMS):
            raise SafetyStop("The context includes high-risk changes that need human review.")

        if any(term in lower_text for term in _REPEATED_FAILURE_TERMS):
            raise SafetyStop("Repeated failures detected; stop for human direction.", "medium")


def _coerce_list(value: list[str] | str | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [line.strip() for line in value.splitlines() if line.strip()]
    return [str(item) for item in value]

