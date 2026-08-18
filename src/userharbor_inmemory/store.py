from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime

from userharbor.interfaces import CreateUserRequest, UserStore, UserToken


@dataclass(frozen=True, slots=True)
class User:
    username: str
    email: str
    verified: bool


@dataclass(slots=True)
class _StoredUser:
    username: str
    email: str
    password_hash: str
    verified: bool = False
    roles: set[str] = field(default_factory=set)


class InMemoryUserStore(UserStore[User]):
    """Store UserHarbor data in memory for tests and examples."""

    def __init__(self) -> None:
        self._users: dict[str, _StoredUser] = {}
        self._email_verifications: dict[str, UserToken] = {}
        self._sessions: dict[str, UserToken] = {}
        self._password_resets: dict[str, UserToken] = {}
        self._roles: set[str] = set()
        self._permissions: set[str] = set()
        self._role_permissions: dict[str, set[str]] = {}
        self._transaction_depth = 0

    @contextmanager
    def transaction(self) -> Iterator[None]:
        snapshot = None
        if self._transaction_depth == 0:
            snapshot = deepcopy(
                (
                    self._users,
                    self._email_verifications,
                    self._sessions,
                    self._password_resets,
                    self._roles,
                    self._permissions,
                    self._role_permissions,
                )
            )

        self._transaction_depth += 1
        try:
            yield
        except Exception:
            if snapshot is not None:
                (
                    self._users,
                    self._email_verifications,
                    self._sessions,
                    self._password_resets,
                    self._roles,
                    self._permissions,
                    self._role_permissions,
                ) = snapshot
            raise
        finally:
            self._transaction_depth -= 1

    def create_user(self, user: CreateUserRequest) -> None:
        username_key = user.username.casefold()
        if username_key in self._users or any(
            stored_user.email == user.email for stored_user in self._users.values()
        ):
            raise ValueError("Username or email already exists")

        self._users[username_key] = _StoredUser(
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
        )
        self._email_verifications[user.verification_token_hash] = UserToken(
            username=user.username,
            token_hash=user.verification_token_hash,
            expires_at=user.expires_at,
        )

    def set_user_verified(self, username: str) -> None:
        user = self._users.get(username.casefold())
        if user is not None:
            user.verified = True

    def delete_user(self, username: str) -> None:
        user = self._users.pop(username.casefold(), None)
        if user is None:
            return

        self._remove_user_tokens(self._email_verifications, user.username)
        self._remove_user_tokens(self._sessions, user.username)
        self._remove_user_tokens(self._password_resets, user.username)

    def get_user_by_username(self, username: str) -> User | None:
        user = self._users.get(username.casefold())
        return self._to_public_user(user) if user is not None else None

    def get_user_by_email(self, email: str) -> User | None:
        for user in self._users.values():
            if user.email == email:
                return self._to_public_user(user)
        return None

    def get_password_hash(self, username: str) -> str:
        return self._users[username.casefold()].password_hash

    def set_password_hash(self, username: str, password_hash: str) -> None:
        self._users[username.casefold()].password_hash = password_hash

    def get_email_verification(self, token_hash: str) -> UserToken | None:
        return self._email_verifications.get(token_hash)

    def set_email_verification(self, verification: UserToken) -> None:
        self._users[verification.username.casefold()]
        self._remove_user_tokens(
            self._email_verifications,
            verification.username,
        )
        self._email_verifications[verification.token_hash] = verification

    def remove_email_verification(self, token_hash: str) -> None:
        self._email_verifications.pop(token_hash, None)

    def get_session(self, token_hash: str) -> UserToken | None:
        return self._sessions.get(token_hash)

    def add_session(self, session: UserToken) -> None:
        self._users[session.username.casefold()]
        self._sessions[session.token_hash] = session

    def remove_session(self, token_hash: str) -> None:
        self._sessions.pop(token_hash, None)

    def remove_all_sessions(self, username: str) -> None:
        self._remove_user_tokens(self._sessions, username)

    def refresh_session(self, token_hash: str, new_expires_at: datetime) -> None:
        session = self._sessions.get(token_hash)
        if session is not None:
            session.expires_at = new_expires_at

    def get_password_reset(self, token_hash: str) -> UserToken | None:
        return self._password_resets.get(token_hash)

    def set_password_reset(self, reset: UserToken) -> None:
        self._users[reset.username.casefold()]
        self._remove_user_tokens(self._password_resets, reset.username)
        self._password_resets[reset.token_hash] = reset

    def remove_password_reset(self, token_hash: str) -> None:
        self._password_resets.pop(token_hash, None)

    def create_role(self, role: str) -> None:
        self._roles.add(role)
        self._role_permissions.setdefault(role, set())

    def delete_role(self, role: str) -> None:
        self._roles.discard(role)
        self._role_permissions.pop(role, None)
        for user in self._users.values():
            user.roles.discard(role)

    def list_roles(self) -> set[str]:
        return self._roles.copy()

    def role_exists(self, role: str) -> bool:
        return role in self._roles

    def grant_role_to_user(self, username: str, role: str) -> None:
        self._users[username.casefold()].roles.add(role)

    def revoke_role_from_user(self, username: str, role: str) -> None:
        self._users[username.casefold()].roles.discard(role)

    def get_user_roles(self, username: str) -> set[str]:
        user = self._users.get(username.casefold())
        return user.roles.copy() if user is not None else set()

    def create_permission(self, permission: str) -> None:
        self._permissions.add(permission)

    def delete_permission(self, permission: str) -> None:
        self._permissions.discard(permission)
        for permissions in self._role_permissions.values():
            permissions.discard(permission)

    def list_permissions(self) -> set[str]:
        return self._permissions.copy()

    def permission_exists(self, permission: str) -> bool:
        return permission in self._permissions

    def grant_permission_to_role(self, role: str, permission: str) -> None:
        self._role_permissions[role].add(permission)

    def revoke_permission_from_role(self, role: str, permission: str) -> None:
        self._role_permissions[role].discard(permission)

    def get_role_permissions(self, role: str) -> set[str]:
        return self._role_permissions.get(role, set()).copy()

    def get_user_permissions(self, username: str) -> set[str]:
        user = self._users.get(username.casefold())
        if user is None:
            return set()

        permissions = set()
        for role in user.roles:
            permissions.update(self._role_permissions.get(role, set()))
        return permissions

    @staticmethod
    def _to_public_user(user: _StoredUser) -> User:
        return User(
            username=user.username,
            email=user.email,
            verified=user.verified,
        )

    @staticmethod
    def _remove_user_tokens(tokens: dict[str, UserToken], username: str) -> None:
        token_hashes = [
            token_hash
            for token_hash, token in tokens.items()
            if token.username == username
        ]
        for token_hash in token_hashes:
            del tokens[token_hash]
