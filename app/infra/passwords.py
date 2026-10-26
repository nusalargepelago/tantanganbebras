"""Password hashing — the single source for hashing and verifying user passwords."""
from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash

_BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def is_legacy_hash(stored: str) -> bool:
    return stored.startswith(_BCRYPT_PREFIXES)


def verify_password(stored: str, candidate: str) -> bool:
    if is_legacy_hash(stored):
        try:
            import bcrypt

            return bcrypt.checkpw(candidate.encode("utf-8"), stored.encode("ascii"))
        except (ValueError, TypeError):
            return False
    try:
        return check_password_hash(stored, candidate)
    except (ValueError, TypeError):
        return False


__all__ = ["hash_password", "is_legacy_hash", "verify_password"]
