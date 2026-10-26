"""Scoring engine — shared by practice and event attempts."""
from __future__ import annotations

POINTS_PER_CORRECT = 10
SHEET_SIZE = 10


def is_correct(question, answer: str | None) -> bool:
    """Grade one answer. Empty and Essay answers are always wrong."""
    if answer is None or not answer.strip():
        return False
    if question.question_type == "Multiple Choice":
        return bool(question.correct_answer) and (
            answer.strip().lower() == question.correct_answer.strip().lower()
        )
    return False


def score_for(correct_count: int) -> int:
    return correct_count * POINTS_PER_CORRECT


__all__ = ["POINTS_PER_CORRECT", "SHEET_SIZE", "is_correct", "score_for"]
