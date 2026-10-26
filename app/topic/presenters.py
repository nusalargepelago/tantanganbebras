"""Topic presenters — wire serialization for topics."""
from __future__ import annotations

from app.infra.presenters import UtcPresenterBase
from app.topic.models import Topic
from framework.base import PresenterBase


class TopicOut(UtcPresenterBase):
    """Topic on the wire."""

    name: str
    title: str
    category: str
    idx: int
    creator_id: str | None = PresenterBase.field(None, alias="creatorId")
    created_at: str | None = PresenterBase.field(None, alias="createdAt")
    updated_at: str | None = PresenterBase.field(None, alias="updatedAt")

    @classmethod
    def from_topic(cls, topic: Topic) -> TopicOut:
        return cls.from_model(topic)


__all__ = ["TopicOut"]
