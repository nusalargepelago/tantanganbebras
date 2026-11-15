"""Master data repositories — queries only, no commit boundary."""
from __future__ import annotations

from app.school.models import City, School
from app.school.names import normalize_name
from framework.base import RepositoryBase
from framework.extensions import db


class CityRepository(RepositoryBase[City]):
    model = City

    def list_all(self) -> list[City]:
        return self.list(order_by=City.name)

    def find_by_normalized_name(self, name: str) -> City | None:
        norm = normalize_name(name)
        return next(
            (c for c in db.session.query(City).all() if normalize_name(c.name) == norm),
            None,
        )


class SchoolRepository(RepositoryBase[School]):
    model = School

    def list_active(self, *, q: str | None = None, include_disabled: bool = False) -> list[School]:
        query = db.session.query(School)
        if not include_disabled:
            query = query.filter(School.is_active.is_(True))
        if q:
            like = f"%{q}%"
            query = query.filter(School.name.ilike(like))
        return query.order_by(School.name.asc()).all()

    def find_by_normalized_name(self, name: str) -> School | None:
        norm = normalize_name(name)
        return next(
            (s for s in db.session.query(School).all() if normalize_name(s.name) == norm),
            None,
        )


__all__ = ["CityRepository", "SchoolRepository"]
