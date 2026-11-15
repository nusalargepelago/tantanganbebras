"""Account repositories — database access for users, API keys, and preferences."""
from __future__ import annotations

from sqlalchemy import func, or_, select

from app.account.models import ApiKey, UserPreference
from app.auth.models import User
from framework.base import RepositoryBase
from framework.extensions import db


class AccountRepository(RepositoryBase[User]):
    """Database access layer for admin user management."""

    model = User

    def get_user(self, user_id: str) -> User | None:
        return self.get(user_id)

    def find_user_by_username(self, username: str) -> User | None:
        return self.find_one(username=username)

    def find_user_by_email(self, email: str) -> User | None:
        return self.find_one(email=email)

    def list_users(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[User], int]:
        condition = None
        if search:
            like = f"%{search}%"
            condition = or_(
                User.email.ilike(like),
                User.username.ilike(like),
                User.full_name.ilike(like),
            )
        # Page over bare ids first: limit on the entity select would
        # paginate the joinedload fan-out instead of distinct users.
        count_stmt = select(func.count(func.distinct(User.id)))
        page_stmt = (
            select(User.id)
            .order_by(User.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        if condition is not None:
            count_stmt = count_stmt.where(condition)
            page_stmt = page_stmt.where(condition)
        total = db.session.execute(count_stmt).scalar() or 0
        items = list(
            db.session.execute(
                select(User).where(User.id.in_(page_stmt)).order_by(User.id)
            ).scalars().unique().all()
        )
        return items, total


class ApiKeyRepository(RepositoryBase[ApiKey]):
    """Database access layer for API keys."""

    model = ApiKey

    def list_for_user(self, user_id: str) -> list[ApiKey]:
        return list(
            db.session.scalars(
                select(ApiKey)
                .where(ApiKey.user_id == user_id)
                .order_by(ApiKey.created_on.desc())
            )
        )

    def find_by_prefix(self, prefix: str) -> ApiKey | None:
        return db.session.scalars(
            select(ApiKey).where(ApiKey.prefix == prefix, ApiKey.is_active.is_(True))
        ).first()


class UserPreferenceRepository(RepositoryBase[UserPreference]):
    """Database access layer for per-user preferences."""

    model = UserPreference

    def find_for_user(self, user_id: str, key: str) -> UserPreference | None:
        return self.find_one(user_id=user_id, key=key)


__all__ = ["AccountRepository", "ApiKeyRepository", "UserPreferenceRepository"]
