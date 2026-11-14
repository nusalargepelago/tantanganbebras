"""Type aliases for Flask response tuples."""
from __future__ import annotations

from typing import Any

from flask import Response as FlaskResponse

JsonBody = dict[str, Any]
Status = int

ResponseTuple = tuple[FlaskResponse, Status]

__all__ = [
    "JsonBody",
    "ResponseTuple",
    "Status",
]
