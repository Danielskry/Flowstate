from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ContextSchema(BaseModel):
    """Validated schema for a grounding snapshot."""

    model_config = ConfigDict(extra="forbid")

    facts: dict[str, Any] = Field(default_factory=dict)
    steps: list[NonEmptyString] = Field(default_factory=list)
    intent: dict[str, Any] = Field(default_factory=dict)
    scope: dict[str, Any] = Field(default_factory=dict)
    max_steps: int | None = None
