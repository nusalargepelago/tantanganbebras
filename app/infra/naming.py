"""Slug helpers — unique natural-key names for topic, question, and event."""
from __future__ import annotations

import re
from collections.abc import Callable
from datetime import UTC, datetime

from framework.exceptions import Conflict

_MAX_SLUG = 80
_MAX_ATTEMPTS = 999


def slugify(value: str, *, fallback: str) -> str:
    """Collapse ``value`` to a URL-safe slug; ``fallback`` when nothing survives."""
    text = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    text = text[:_MAX_SLUG].strip("-")
    return text or fallback


def next_name(base: str, exists: Callable[[str], bool], *, year: bool = False) -> str:
    """Resolve a unique name: ``base``, then ``base-0001``…``base-0999``.

    With ``year=True`` the numeric suffix is preceded by the current year
    (``base-2026-0001``), matching the question-bank convention.
    Raises ``Conflict`` when all candidates are taken.
    """
    if not exists(base):
        return base
    marker = f"-{datetime.now(UTC).year}" if year else ""
    for seq in range(1, _MAX_ATTEMPTS + 1):
        candidate = f"{base}{marker}-{seq:04d}"
        if not exists(candidate):
            return candidate
    raise Conflict("could_not_generate_unique_name")


__all__ = ["next_name", "slugify"]
