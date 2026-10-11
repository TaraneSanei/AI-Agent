from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


Role = Literal["user", "agent"]


class MemoryItem(BaseModel):
    """One summary claim with links to the raw messages supporting it."""

    text: str = Field(min_length=1, max_length=2_000)
    source_message_ids: list[str] = Field(min_length=1, max_length=50)

    @field_validator("source_message_ids")
    @classmethod
    def source_ids_must_be_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("source_message_ids must be unique")
        return value


class Decision(BaseModel):
    decision_maker: Role
    decision_text: str = Field(min_length=1, max_length=2_000)
    supporting_evidence: list[MemoryItem] = Field(default_factory=list)


class MessageItem(BaseModel):
    """A retry-safe message entering the Librarian."""

    message_id: str = Field(min_length=1, max_length=255)
    sender: Role
    decision: Decision | None = None
    content: str = Field(min_length=1, max_length=200_000)
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)
    recipient: Role
