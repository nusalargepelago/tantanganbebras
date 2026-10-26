"""Event domain — re-exports blueprints, services, models, DTOs, and presenters."""
from __future__ import annotations

from app.event.api import bp
from app.event.api_student import bp as event_student_bp
from app.event.dto import EventCreateIn, EventUpdateIn
from app.event.models import Event, EventAttempt
from app.event.presenters import EventAttemptOut, EventOut
from app.event.services import EventAttemptService, EventService

__all__ = [
    "Event",
    "EventAttempt",
    "EventAttemptOut",
    "EventAttemptService",
    "EventCreateIn",
    "EventOut",
    "EventService",
    "EventUpdateIn",
    "bp",
    "event_student_bp",
]
