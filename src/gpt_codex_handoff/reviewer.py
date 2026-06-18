"""OpenAI reviewer client and recommendation schema validation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Protocol

from .context import ReviewContext, SafetyStop


RECOMMENDATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "next_step",
        "priority",
        "reason",
        "should_continue",
        "max_minutes",
        "commands_to_run",
        "files_to_inspect",
        "risk_level",
        "handoff_note",
    ],
    "properties": {
        "next_step": {"type": "string"},
        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
        "reason": {"type": "string"},
        "should_continue": {"type": "boolean"},
        "max_minutes": {"type": "integer", "minimum": 0, "maximum": 120},
        "commands_to_run": {"type": "array", "items": {"type": "string"}},
        "files_to_inspect": {"type": "array", "items": {"type": "string"}},
        "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
        "handoff_note": {"type": "string"},
    },
}


Recommendation = dict[str, Any]


class ReviewerClient(Protocol):
    def create_recommendation(
        self,
        *,
        model: str,
        system_prompt: str,
        payload: dict[str, Any],
        schema: dict[str, Any],
    ) -> Recommendation:
        ...


class OpenAIResponsesClient:
    """Tiny adapter around the OpenAI Responses API."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def create_recommendation(
        self,
        *,
        model: str,
        system_prompt: str,
        payload: dict[str, Any],
        schema: dict[str, Any],
    ) -> Recommendation:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Review this Codex session context and return the next-step JSON:\n"
                    + json.dumps(payload, indent=2, sort_keys=True),
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "codex_next_step_recommendation",
                    "strict": True,
                    "schema": schema,
                }
            },
        )
        return json.loads(response.output_text)


class OpenAIReviewer:
    """Reviewer facade with local safety preflight and schema validation."""

    def __init__(
        self,
        client: ReviewerClient | None = None,
        *,
        model: str | None = None,
        prompt_path: Path | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model or os.getenv("OPENAI_REVIEWER_MODEL", "gpt-4.1-mini")
        self.prompt_path = prompt_path or Path(__file__).resolve().parents[2] / "reviewer_prompt.md"
        self.client = client or OpenAIResponsesClient(api_key or os.getenv("OPENAI_API_KEY"))

    def review(self, context: ReviewContext) -> Recommendation:
        try:
            payload = context.as_payload()
        except SafetyStop as stop:
            return safety_recommendation(stop.reason, stop.risk_level)

        recommendation = self.client.create_recommendation(
            model=self.model,
            system_prompt=self._load_prompt(),
            payload=payload,
            schema=RECOMMENDATION_SCHEMA,
        )
        validate_recommendation(recommendation)
        return recommendation

    def _load_prompt(self) -> str:
        return self.prompt_path.read_text(encoding="utf-8")


def safety_recommendation(reason: str, risk_level: str = "high") -> Recommendation:
    return {
        "next_step": "stop and ask the user for direction",
        "priority": "high",
        "reason": reason,
        "should_continue": False,
        "max_minutes": 0,
        "commands_to_run": [],
        "files_to_inspect": [],
        "risk_level": risk_level,
        "handoff_note": reason,
    }


def validate_recommendation(value: Recommendation) -> None:
    required = RECOMMENDATION_SCHEMA["required"]
    missing = [key for key in required if key not in value]
    if missing:
        raise ValueError(f"Recommendation is missing required fields: {', '.join(missing)}")

    extra = sorted(set(value) - set(required))
    if extra:
        raise ValueError(f"Recommendation has unexpected fields: {', '.join(extra)}")

    _expect_type(value, "next_step", str)
    _expect_enum(value, "priority", {"low", "medium", "high"})
    _expect_type(value, "reason", str)
    _expect_type(value, "should_continue", bool)
    _expect_type(value, "max_minutes", int)
    if value["max_minutes"] < 0 or value["max_minutes"] > 120:
        raise ValueError("Recommendation max_minutes must be between 0 and 120.")
    _expect_str_list(value, "commands_to_run")
    _expect_str_list(value, "files_to_inspect")
    _expect_enum(value, "risk_level", {"low", "medium", "high"})
    _expect_type(value, "handoff_note", str)


def _expect_type(value: Recommendation, key: str, expected_type: type) -> None:
    if not isinstance(value[key], expected_type):
        raise ValueError(f"Recommendation field {key} must be {expected_type.__name__}.")


def _expect_enum(value: Recommendation, key: str, allowed: set[str]) -> None:
    _expect_type(value, key, str)
    if value[key] not in allowed:
        raise ValueError(f"Recommendation field {key} must be one of {sorted(allowed)}.")


def _expect_str_list(value: Recommendation, key: str) -> None:
    if not isinstance(value[key], list) or not all(isinstance(item, str) for item in value[key]):
        raise ValueError(f"Recommendation field {key} must be a list of strings.")

