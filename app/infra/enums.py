"""Tantangan Bebras enum catalogs — shared value sets for topic, question, event, student, practice."""
from __future__ import annotations

CATEGORIES = ("cub", "scout", "rover")
DIFFICULTY_LEVELS = ("Easy", "Medium", "Hard")
QUESTION_TYPES = ("Multiple Choice", "Essay")
OPTION_LETTERS = ("a", "b", "c", "d")
STATUSES = ("Active", "Inactive")
STUDENT_STATUSES = ("Active", "Inactive")

__all__ = [
    "CATEGORIES",
    "DIFFICULTY_LEVELS",
    "OPTION_LETTERS",
    "QUESTION_TYPES",
    "STATUSES",
    "STUDENT_STATUSES",
]
