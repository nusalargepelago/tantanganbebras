"""Student repositories — query layer for the student discriminator."""
from __future__ import annotations

from app.auth.models import User
from app.student.models import Student
from framework.base import RepositoryBase
from framework.extensions import db


class StudentRepository(RepositoryBase[Student]):
    """Query layer for students."""

    model = Student

    def find_by_user_id(self, user_id: str) -> Student | None:
        return self.get(user_id)

    def find_by_user_ids(self, user_ids: list[str]) -> list[Student]:
        if not user_ids:
            return []
        return db.session.query(Student).filter(Student.user_id.in_(user_ids)).all()

    def list_students(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
        q: str | None = None,
        include_disabled: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Student], int]:
        query = db.session.query(Student).join(User, User.id == Student.user_id)
        if not include_disabled:
            query = query.filter(Student.disabled.is_(False))
        if category:
            query = query.filter(Student.category == category)
        if status:
            query = query.filter(Student.status == status)
        if q:
            like = f"%{q}%"
            query = query.filter(
                db.or_(
                    User.username.ilike(like),
                    User.email.ilike(like),
                    User.first_name.ilike(like),
                    User.last_name.ilike(like),
                    Student.school.ilike(like),
                )
            )
        total = query.count()
        items = (
            query.order_by(Student.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total


__all__ = ["StudentRepository"]
