"""Topic domain — re-exports bp, TopicService, model, DTOs, and presenter."""
from __future__ import annotations

from app.topic.api import bp
from app.topic.dto import TopicCreateIn, TopicUpdateIn
from app.topic.models import Topic
from app.topic.presenters import TopicOut
from app.topic.services import TopicService

__all__ = [
    "Topic",
    "TopicCreateIn",
    "TopicOut",
    "TopicService",
    "TopicUpdateIn",
    "bp",
]
