"""Question domain — re-exports bp, QuestionService, model, DTOs, and presenter."""
from __future__ import annotations

from app.question.api import bp
from app.question.dto import QuestionCreateIn, QuestionUpdateIn
from app.question.models import Question
from app.question.presenters import QuestionOut
from app.question.services import QuestionService

__all__ = [
    "Question",
    "QuestionCreateIn",
    "QuestionOut",
    "QuestionService",
    "QuestionUpdateIn",
    "bp",
]
