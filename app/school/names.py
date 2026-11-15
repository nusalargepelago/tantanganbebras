"""City / school normalisation — casefold + whitespace-collapsed matching."""
from __future__ import annotations

import re

_WS = re.compile(r"\s+")


def normalize_name(value: str) -> str:
    return _WS.sub(" ", value.strip()).casefold()


__all__ = ["normalize_name"]
