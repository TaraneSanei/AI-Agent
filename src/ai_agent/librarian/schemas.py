from __future__ import annotations

from pydantic import BaseModel, Field

from ai_agent.schemas import MemoryItem, MessageItem


class StoredMessage(MessageItem):
    internal_id: int
    relevance_score: float | None = None


class RollingSummary(BaseModel):
    """Structured operational memory with provenance."""

    current_goal: MemoryItem | None = None
    constraints: list[MemoryItem] = Field(default_factory=list, max_length=30)
    decisions: list[MemoryItem] = Field(default_factory=list, max_length=30)
    facts: list[MemoryItem] = Field(default_factory=list, max_length=50)
    open_questions: list[MemoryItem] = Field(default_factory=list, max_length=30)
    progress: list[MemoryItem] = Field(default_factory=list, max_length=30)

    def iter_items(self) -> list[tuple[str, int, MemoryItem]]:
        items: list[tuple[str, int, MemoryItem]] = []
        if self.current_goal is not None:
            items.append(("current_goal", 0, self.current_goal))
        for field_name in (
            "constraints",
            "decisions",
            "facts",
            "open_questions",
            "progress",
        ):
            values = getattr(self, field_name)
            items.extend((field_name, index, item) for index, item in enumerate(values))
        return items


class ContextBundle(BaseModel):
    query: str
    summary: RollingSummary
    summary_version: int = Field(ge=0)
    relevant_messages: list[StoredMessage] = Field(default_factory=list)
    recent_messages: list[StoredMessage] = Field(default_factory=list)
    selected_message_ids: list[str] = Field(default_factory=list)
