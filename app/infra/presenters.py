"""Presenter helpers shared by Tantangan Bebras domains."""
from __future__ import annotations

import re
from typing import Any

from framework.base import PresenterBase

_NAIVE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$")


class UtcPresenterBase(PresenterBase):
    """Presenter that stamps naive ISO timestamps as UTC on the wire.

    SQLite returns naive datetimes even for ``DateTime(timezone=True)``;
    the wire contract is always ISO-8601 with ``+00:00``.
    """

    @classmethod
    def from_model(cls, model: Any, **overrides: Any) -> UtcPresenterBase:
        presenter = super().from_model(model, **overrides)
        for key, value in presenter:
            if isinstance(value, str) and _NAIVE_ISO.fullmatch(value):
                setattr(presenter, key, f"{value}+00:00")
        return presenter


__all__ = ["UtcPresenterBase"]
