"""User repository — database access for the User domain."""
from __future__ import annotations

from sqlalchemy import func, or_

from app.auth.models import Role, User
from framework.base import RepositoryBase
from framework.extensions import db


class UserRepository(RepositoryBase[User]):
    """Database access layer for User domain."""

    model = User

    def find_by_email(self, email: str) -> User | None:
        return db.session.query(User).filter(func.lower(User.email) == email.lower()).first()

    def find_by_username(self, username: str) -> User | None:
        return (
            db.session.query(User)
            .filter(func.lower(User.username) == username.lower())
            .first()
        )

    def find_by_identifier(self, identifier: str) -> User | None:
        needle = identifier.lower()
        return (
            db.session.query(User)
            .filter(
                or_(
                    func.lower(User.email) == needle,
                    func.lower(User.username) == needle,
                )
            )
            .first()
        )


class RoleRepository(RepositoryBase[Role]):
    """Database access layer for the Role model."""

    model = Role

    def find_by_name(self, name: str) -> Role | None:
        return self.find_one(name=name)

    def list_all(self) -> list[Role]:
        return self.list(order_by=Role.id)


__all__ = ["RoleRepository", "UserRepository"]
