"""Master data presenters — wire serialization for schools and cities."""
from __future__ import annotations

from app.school.models import City, School
from framework.base import PresenterBase


class SchoolOut(PresenterBase):
    id: str
    name: str
    is_active: bool = PresenterBase.field(True, alias="isActive")
    city_id: str | None = PresenterBase.field(None, alias="cityId")
    city: dict | None = None

    @classmethod
    def from_school(cls, school: School) -> SchoolOut:
        city = getattr(school, "city", None)
        return cls.from_model(
            school,
            city={"id": city.id, "name": city.name} if city else None,
        )


class CityOut(PresenterBase):
    id: str
    name: str

    @classmethod
    def from_city(cls, city: City) -> CityOut:
        return cls.from_model(city)


__all__ = [
    "CityOut",
    "SchoolOut",
]
