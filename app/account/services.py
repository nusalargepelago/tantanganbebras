"""Account services — user/role management and API keys."""
from __future__ import annotations

from app.account.dto import RoleUpdateIn, UserCreateIn, UserUpdateIn
from app.account.models import ApiKey, generate_api_key
from app.account.repositories import AccountRepository, ApiKeyRepository
from app.auth.models import MEMBER_ROLE, Role, User
from app.auth.repositories import RoleRepository, UserRepository
from app.infra.audit import log as audit_log
from app.infra.passwords import hash_password
from framework.base import ServiceBase
from framework.exceptions import Conflict, InvalidOperation, NotFound

BUILTIN_ROLES = {MEMBER_ROLE}


class AccountService(ServiceBase[AccountRepository]):
    """Business logic layer for admin user and role management."""

    repository_class = AccountRepository

    def __init__(
        self,
        repo: AccountRepository | None = None,
        roles: RoleRepository | None = None,
    ):
        super().__init__(repo)
        self._roles = roles or RoleRepository()

    # --- users --------------------------------------------------------
    def list_users(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[User], int]:
        return self._repo.list_users(search=search, page=page, per_page=per_page)

    def list_all_users(self) -> list[User]:
        return self._repo.list(order_by=User.id)

    def get_user(self, user_id: str) -> User:
        user = self._repo.get_user(user_id)
        if user is None:
            raise NotFound("user_not_found")
        return user

    def create_user(self, dto: UserCreateIn, *, actor_id: str) -> User:
        if self._repo.find_user_by_email(dto.email) is not None:
            raise Conflict("email_already_registered")
        if dto.username and self._repo.find_user_by_username(dto.username) is not None:
            raise Conflict("username_taken")

        user = User(
            username=dto.username or dto.email,
            email=dto.email,
            full_name=dto.full_name,
            password=hash_password(dto.password),
            active=True,
            app_role=dto.app_role,
        )
        if dto.role_names:
            roles = []
            for name in dto.role_names:
                role = self._roles.find_by_name(name)
                if role is None:
                    raise InvalidOperation("role_not_found")
                roles.append(role)
            user.roles = roles

        self._repo.add(user)
        self._flush()
        audit_log(
            "user_admin_created",
            user_id=actor_id,
            resource=f"users/{user.id}",
            details={"email": user.email, "role": dto.app_role},
        )
        self._commit()
        return user

    def delete_user(self, user_id: str, *, actor_id: str) -> None:
        user = self.get_user(user_id)
        self._repo.delete(user)
        audit_log("user_admin_deleted", user_id=actor_id, resource=f"users/{user_id}")
        self._commit()

    def update_user(self, user_id: str, dto: UserUpdateIn, *, actor_id: str) -> User:
        user = self._repo.get_user(user_id)
        if user is None:
            raise NotFound("user_not_found")

        data = dto.model_dump(exclude_unset=True, exclude_none=True)
        if "username" in data:
            new_username = data["username"]
            existing = self._repo.find_user_by_username(new_username)
            if existing is not None and existing.id != user.id:
                raise Conflict("username_taken")
            user.username = new_username
        if "full_name" in data:
            user.full_name = data["full_name"]
        if "active" in data:
            user.active = bool(data["active"])
        if "app_role" in data:
            user.app_role = data["app_role"]
        if "role_names" in data:
            roles = []
            for name in data["role_names"]:
                role = self._roles.find_by_name(name)
                if role is None:
                    raise InvalidOperation("role_not_found")
                roles.append(role)
            user.roles = roles

        audit_log(
            "user_updated",
            user_id=actor_id,
            resource=f"users/{user_id}",
            details={"changed": sorted(data.keys())},
        )
        self._commit()
        return user

    # --- roles --------------------------------------------------------
    def list_roles(self) -> list[Role]:
        return self._roles.list_all()

    def create_role(self, name: str, *, actor_id: str) -> Role:
        if self._roles.find_by_name(name) is not None:
            raise Conflict("role_already_exists")

        role = Role(name=name)
        self._roles.add(role)
        self._flush()
        audit_log(
            "role_created",
            user_id=actor_id,
            resource=f"roles/{role.id}",
            details={"name": role.name},
        )
        self._commit()
        return role

    def update_role(self, role_id: str, dto: RoleUpdateIn, *, actor_id: str) -> Role:
        role = self._roles.get(role_id)
        if role is None:
            raise NotFound("role_not_found")

        data = dto.model_dump(exclude_unset=True, exclude_none=True)
        if "name" in data:
            new_name = data["name"]
            existing = self._roles.find_by_name(new_name)
            if existing is not None and existing.id != role.id:
                raise Conflict("role_already_exists")
            role.name = new_name

        audit_log(
            "role_updated",
            user_id=actor_id,
            resource=f"roles/{role_id}",
            details={"changed": sorted(data.keys())},
        )
        self._commit()
        return role

    def delete_role(self, role_id: str, *, actor_id: str) -> Role:
        role = self._roles.get(role_id)
        if role is None:
            raise NotFound("role_not_found")
        if role.name in BUILTIN_ROLES:
            raise InvalidOperation("cannot_delete_builtin_role")

        self._roles.delete(role)
        audit_log(
            "role_deleted",
            user_id=actor_id,
            resource=f"roles/{role_id}",
            details={"name": role.name},
        )
        self._commit()
        return role


class ApiKeyService(ServiceBase[ApiKeyRepository]):
    """Business logic layer for API key issuance and verification."""

    repository_class = ApiKeyRepository

    def __init__(
        self,
        repo: ApiKeyRepository | None = None,
        users: UserRepository | None = None,
    ):
        super().__init__(repo)
        self._users = users or UserRepository()

    def create(self, user_id: str, name: str) -> tuple[str, str]:
        if self._users.get(user_id) is None:
            raise NotFound("user_not_found")

        raw_key = generate_api_key()
        api_key = ApiKey(
            key_hash=ApiKey.hash_key(raw_key),
            prefix=raw_key[:10],
            name=name,
            user_id=user_id,
        )
        self._repo.add(api_key)
        self._flush()
        audit_log(
            "api_key_created",
            user_id=user_id,
            resource=f"api_keys/{api_key.id}",
            details={"name": api_key.name},
        )
        self._commit()
        return raw_key, api_key.masked_name

    def revoke(self, key_id: str, *, user_id: str) -> None:
        api_key = self._repo.get(key_id)
        if api_key is None or api_key.user_id != user_id:
            raise NotFound("api_key_not_found")
        self._repo.delete(api_key)
        audit_log(
            "api_key_revoked",
            user_id=user_id,
            resource=f"api_keys/{key_id}",
            details={"name": api_key.name},
        )
        self._commit()

    def list(self, user_id: str) -> list[ApiKey]:
        return self._repo.list_for_user(user_id)

    def verify(self, raw_key: str) -> ApiKey | None:
        api_key = self._repo.find_by_prefix(raw_key[:10])
        if api_key and ApiKey.verify_key(api_key.key_hash, raw_key):
            return api_key
        return None


__all__ = ["BUILTIN_ROLES", "AccountService", "ApiKeyService"]
