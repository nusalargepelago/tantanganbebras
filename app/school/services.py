"""Master data business logic — city lookup and school admin CRUD."""
from __future__ import annotations

from app.infra.audit import log as audit_log
from app.school.models import School
from app.school.repositories import CityRepository, SchoolRepository
from framework.base import ServiceBase
from framework.exceptions import Conflict, InvalidOperation, NotFound, ValidationFailed
from framework.infra.uuid7 import uuid7


class CityService:
    """Read access to the Indonesian kabupaten/kota master (no mutation)."""

    def __init__(self, repo: CityRepository | None = None):
        self._repo = repo or CityRepository()

    def list_cities(self) -> list:
        return self._repo.list_all()

    def require_city(self, city_id: str):
        city = self._repo.get(city_id)
        if city is None:
            raise ValidationFailed("city_not_in_master")
        return city

    def find_city_by_name(self, name: str):
        return self._repo.find_by_normalized_name(name)


class SchoolService(ServiceBase[SchoolRepository]):
    repository_class = SchoolRepository

    def __init__(self, repo: SchoolRepository | None = None, cities: CityService | None = None):
        super().__init__(repo)
        self._cities = cities or CityService()

    # --- reads -----------------------------------------------------------

    def list_schools(self, *, q: str | None = None, include_disabled: bool = False) -> list[School]:
        return self._repo.list_active(q=q, include_disabled=include_disabled)

    def require_school(self, school_id: str) -> School:
        """School must exist **and be active** — inactive schools can't be
        picked for new student/teacher links (422 ``school_inactive``).
        Existence and activity are separate errors: ``school_not_in_master``
        (unknown id) vs ``school_inactive`` (known but deactivated)."""
        school = self._repo.get(school_id)
        if school is None:
            raise ValidationFailed("school_not_in_master")
        if not school.is_active:
            raise InvalidOperation("school_inactive")
        return school

    def find_school_by_name(self, name: str) -> School | None:
        return self._repo.find_by_normalized_name(name)

    # --- writes ----------------------------------------------------------

    def create_school(self, dto, *, actor_id: str) -> School:
        """Create a school. Any signed-in user may create one; duplicates
        (normalized name, case/space-insensitive) are rejected with 409
        ``school_already_exists``. Admin-only operations stay on the
        PATCH path (rename/(de)activate).
        """
        self._reject_duplicate(dto.name)
        city = self._cities.require_city(dto.city_id)
        school = School(id=uuid7(), name=dto.name, city_id=city.id)
        self._repo.add(school)
        self._audit_created(actor_id, school)
        self._commit()
        return school

    def _reject_duplicate(self, name: str) -> None:
        existing = self._repo.find_by_normalized_name(name)
        if existing is not None:
            raise Conflict("school_already_exists")

    def _audit_created(self, actor_id: str, school: School) -> None:
        audit_log(
            "school_created",
            user_id=actor_id,
            resource=f"school/{school.id}",
            details={"name": school.name, "cityId": school.city_id},
        )

    def update_school(self, school_id: str, dto, *, actor_id: str) -> School:
        school = self._repo.get(school_id)
        if school is None:
            raise NotFound("school_not_found")
        if dto.name is not None:
            existing = self._repo.find_by_normalized_name(dto.name)
            if existing is not None and existing.id != school.id:
                raise Conflict("school_already_exists")
            school.name = dto.name
        if dto.city_id is not None:
            self._cities.require_city(dto.city_id)
            school.city_id = dto.city_id
        if dto.is_active is not None:
            school.is_active = dto.is_active
        audit_log(
            "school_updated",
            user_id=actor_id,
            resource=f"school/{school.id}",
            details={"name": school.name, "cityId": school.city_id},
        )
        self._commit()
        return school


__all__ = [
    "CityService",
    "SchoolService",
]
