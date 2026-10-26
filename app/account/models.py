"""Account domain models — ApiKey, UserPreference."""
from __future__ import annotations

import secrets

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from framework.extensions import db
from framework.infra.uuid7 import uuid7


def _uuid() -> str:
    return uuid7()


# --- API Keys -----------------------------------------------------------
def _hash_key(key: str) -> str:
    import bcrypt
    return bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode("ascii")


def generate_api_key() -> str:
    return "sk-" + secrets.token_urlsafe(32)


class ApiKey(db.Model):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    # verify() looks rows up by prefix; key_hash is never queried by equality
    # (bcrypt salts it), so indexing it would not help that lookup.
    prefix: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_on: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationship to User
    user = relationship("User", backref="api_keys")

    @classmethod
    def verify_key(cls, stored_hash: str, candidate: str) -> bool:
        import bcrypt
        try:
            return bcrypt.checkpw(candidate.encode("ascii"), stored_hash.encode("ascii"))
        except (ValueError, TypeError):
            return False

    @classmethod
    def hash_key(cls, key: str) -> str:
        return _hash_key(key)

    @property
    def masked_name(self) -> str:
        if len(self.name) <= 4:
            return "****"
        return self.name[:2] + "****" + self.name[-2:]


class UserPreference(db.Model):
    __tablename__ = "user_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_user_preferences_user_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[str] = mapped_column(
        Text, nullable=False, default="", server_default=""
    )

    user = relationship("User", backref="user_preferences")


__all__ = ["ApiKey", "UserPreference", "generate_api_key"]
