"""Topic services — business logic for topic CRUD and ordering."""
from __future__ import annotations

from app.infra.audit import log as audit_log
from app.infra.naming import next_name, slugify
from app.question.repositories import QuestionRepository
from app.topic.dto import ReorderItem, TopicCreateIn, TopicUpdateIn
from app.topic.models import Topic
from app.topic.repositories import TopicRepository
from framework.base import ServiceBase
from framework.exceptions import Conflict, NotFound


class TopicService(ServiceBase[TopicRepository]):
    """Business logic for topics."""

    repository_class = TopicRepository

    def __init__(
        self,
        repo: TopicRepository | None = None,
        questions: QuestionRepository | None = None,
    ):
        super().__init__(repo)
        self._questions = questions or QuestionRepository()

    def list_topics(
        self, *, category: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Topic], int]:
        return self._repo.list_topics(category=category, page=page, per_page=per_page)

    def get_topic(self, name: str) -> Topic:
        topic = self._repo.find_by_name(name)
        if topic is None:
            raise NotFound("topic_not_found")
        return topic

    def create_topic(self, dto: TopicCreateIn, *, actor_id: str) -> Topic:
        title = dto.title.strip()
        if not title:
            raise Conflict("title_required")
        name = next_name(slugify(title, fallback="topic"), self._repo.name_exists)
        topic = Topic(
            name=name,
            title=title,
            category=dto.category,
            idx=dto.idx,
            creator_id=actor_id,
        )
        self._repo.add(topic)
        audit_log(
            "topic_created",
            user_id=actor_id,
            resource=f"topic/{name}",
            details={"category": dto.category},
        )
        self._commit()
        return topic

    def update_topic(self, name: str, dto: TopicUpdateIn, *, actor_id: str) -> Topic:
        topic = self.get_topic(name)
        data = dto.model_dump(exclude_unset=True, exclude_none=True)
        if "title" in data:
            title = data["title"].strip()
            if not title:
                raise Conflict("title_required")
            data["title"] = title
        for key, value in data.items():
            setattr(topic, key, value)
        audit_log(
            "topic_updated",
            user_id=actor_id,
            resource=f"topic/{name}",
            details={"changed": sorted(data)},
        )
        self._commit()
        return topic

    def delete_topic(self, name: str, *, actor_id: str) -> None:
        topic = self.get_topic(name)
        self._questions.detach_topic(name)
        self._repo.delete(topic)
        audit_log("topic_deleted", user_id=actor_id, resource=f"topic/{name}")
        self._commit()

    def reorder(self, items: list[ReorderItem], *, actor_id: str) -> int:
        count = 0
        for item in items:
            topic = self._repo.find_by_name(item.name)
            if topic is None:
                continue
            topic.idx = item.idx
            count += 1
        audit_log(
            "topic_reordered",
            user_id=actor_id,
            resource="topic/reorder",
            details={"count": count},
        )
        self._commit()
        return count


__all__ = ["TopicService"]
