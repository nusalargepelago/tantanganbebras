"""Topic repositories — query layer for topics."""
from __future__ import annotations

from app.topic.models import Topic
from framework.base import RepositoryBase
from framework.extensions import db


class TopicRepository(RepositoryBase[Topic]):
    """Query layer for topics."""

    model = Topic

    def find_by_name(self, name: str) -> Topic | None:
        return self.find_one(name=name)

    def name_exists(self, name: str) -> bool:
        return self.count(name=name) > 0

    def list_topics(
        self, *, category: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Topic], int]:
        query = db.session.query(Topic)
        if category:
            query = query.filter(Topic.category == category)
        total = query.count()
        items = (
            query.order_by(Topic.category, Topic.idx, Topic.name)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total


__all__ = ["TopicRepository"]
