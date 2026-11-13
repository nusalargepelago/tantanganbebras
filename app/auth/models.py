"""User, Role, and user_roles models for the auth domain."""
from __future__ import annotations

from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from framework.extensions import db
from framework.infra.uuid7 import uuid7


def _uuid() -> str:
    return uuid7()


# --- role / association tables ------------------------------------------
user_roles = db.Table(
    "user_roles",
    db.Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    db.Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


MEMBER_ROLE = "Member"


class Role(db.Model):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    last_name: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    app_role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")

    created_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    changed_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    roles: Mapped[list[Role]] = relationship(
        "Role", secondary=user_roles, backref="users", lazy="joined"
    )

    @property
    def is_active(self) -> bool:  # type: ignore[override]
        return bool(self.active)

    def get_id(self) -> str:  # type: ignore[override]
        return str(self.id)

    def has_role(self, name: str) -> bool:
        """Gate untuk tabel ``roles`` — True kalau user punya role ``name``.

        Exact match ``Role.name`` lewat relasi ``user_roles``. Ini pasangan
        ``require_role()`` (``framework.auth``) untuk dimensi peran
        fungsional — sedangkan ``require_role()`` hanya membaca ``app_role``.
        Mengembalikan bool, bukan response tuple: view yang menentukan
        status error (mis. 403).
        """
        return any(r.name == name for r in self.roles)


__all__ = ["MEMBER_ROLE", "Role", "User", "user_roles"]
