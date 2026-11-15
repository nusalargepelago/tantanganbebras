"""School domain — public surface."""
from __future__ import annotations

from app.school.api import bp
from app.school.dto import SchoolCreateIn, SchoolUpdateIn
from app.school.models import City, School
from app.school.presenters import CityOut, SchoolOut
from app.school.repositories import CityRepository, SchoolRepository
from app.school.services import CityService, SchoolService

__all__ = [
    "City",
    "CityOut",
    "CityRepository",
    "CityService",
    "School",
    "SchoolCreateIn",
    "SchoolOut",
    "SchoolRepository",
    "SchoolService",
    "SchoolUpdateIn",
    "bp",
]
