from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import os
import secrets
import time
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
except ImportError:  # pragma: no cover - dependency is declared, fallback keeps local tests usable
    PasswordHasher = None  # type: ignore[assignment]


SESSION_COOKIE_NAME = "preon_session"
SESSION_TTL = timedelta(days=14)
TOKEN_TTL = timedelta(hours=2)
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

_password_hasher = PasswordHasher() if PasswordHasher is not None else None

from preon_systems_cell.rate_limit import auth_rate_limiter  # noqa: E402


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)
    confirm_password: str | None = Field(default=None, max_length=256)
    name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=24)
    password: str = Field(min_length=8, max_length=256)


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=24)


class AuthUserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str | None = None
    email_verified: bool
    created_at: datetime


class AuthSessionResponse(BaseModel):
    user: AuthUserResponse
    email_verification_url: str | None = None


class ForgotPasswordResponse(BaseModel):
    ok: bool = True
    reset_url: str | None = None


class OAuthProviderResponse(BaseModel):
    provider: str
    configured: bool
    authorization_url: str | None = None


class PasswordPolicy(BaseModel):
    min_length: int = Field(default=12, ge=8, le=128)
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = True


class PasswordPolicyResponse(BaseModel):
    policy: PasswordPolicy


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: str
    password_hash: str
    name: str | None
    email_verified_at: datetime | None
    created_at: datetime

    def public(self) -> AuthUserResponse:
        return AuthUserResponse(
            id=self.id,
            email=self.email,
            name=self.name,
            email_verified=self.email_verified_at is not None,
            created_at=self.created_at,
        )


class InMemoryAuthRepository:
    def __init__(self) -> None:
        self._users: dict[str, AuthUser] = {}
        self._users_by_email: dict[str, str] = {}
        self._sessions: dict[str, tuple[str, datetime]] = {}
        self._verification_tokens: dict[str, tuple[str, datetime]] = {}
        self._reset_tokens: dict[str, tuple[str, datetime]] = {}
        self._password_policy = PasswordPolicy()

    async def create_user(self, email: str, password_hash: str, name: str | None = None) -> AuthUser:
        normalized = normalize_email(email)
        if normalized in self._users_by_email:
            raise ValueError("email already registered")
        now = datetime.now(UTC)
        user = AuthUser(
            id=f"user-{uuid4().hex[:16]}",
            email=normalized,
            password_hash=password_hash,
            name=name,
            email_verified_at=None,
            created_at=now,
        )
        self._users[user.id] = user
        self._users_by_email[normalized] = user.id
        return user

    async def get_user_by_email(self, email: str) -> AuthUser | None:
        user_id = self._users_by_email.get(normalize_email(email))
        return self._users.get(user_id) if user_id else None

    async def get_user(self, user_id: str) -> AuthUser | None:
        return self._users.get(user_id)

    async def mark_email_verified(self, user_id: str) -> AuthUser | None:
        user = self._users.get(user_id)
        if user is None:
            return None
        verified = AuthUser(**{**user.__dict__, "email_verified_at": datetime.now(UTC)})
        self._users[user_id] = verified
        return verified

    async def update_password(self, user_id: str, password_hash: str) -> None:
        user = self._users.get(user_id)
        if user is not None:
            self._users[user_id] = AuthUser(**{**user.__dict__, "password_hash": password_hash})

    async def create_session(self, user_id: str, expires_at: datetime) -> str:
        token = secrets.token_urlsafe(32)
        self._sessions[hash_token(token)] = (user_id, expires_at)
        return token

    async def get_session_user(self, token: str) -> AuthUser | None:
        session = self._sessions.get(hash_token(token))
        if session is None:
            return None
        user_id, expires_at = session
        if expires_at <= datetime.now(UTC):
            self._sessions.pop(hash_token(token), None)
            return None
        return await self.get_user(user_id)

    async def delete_session(self, token: str) -> None:
        self._sessions.pop(hash_token(token), None)

    async def delete_sessions_for_user(self, user_id: str) -> None:
        expired = [session_hash for session_hash, (session_user_id, _) in self._sessions.items() if session_user_id == user_id]
        for session_hash in expired:
            self._sessions.pop(session_hash, None)

    async def refresh_session(self, token: str) -> bool:
        hashed = hash_token(token)
        session = self._sessions.get(hashed)
        if session is None:
            return False
        user_id, expires_at = session
        if expires_at <= datetime.now(UTC):
            return False
        # Slide the window when less than half the TTL remains.
        if expires_at - datetime.now(UTC) < SESSION_TTL / 2:
            self._sessions[hashed] = (user_id, session_expires_at())
            return True
        return False

    async def create_email_verification_token(self, user_id: str, expires_at: datetime) -> str:
        token = secrets.token_urlsafe(32)
        self._verification_tokens[hash_token(token)] = (user_id, expires_at)
        return token

    async def consume_email_verification_token(self, token: str) -> AuthUser | None:
        hashed = hash_token(token)
        record = self._verification_tokens.pop(hashed, None)
        if record is None:
            return None
        user_id, expires_at = record
        if expires_at <= datetime.now(UTC):
            return None
        return await self.mark_email_verified(user_id)

    async def create_password_reset_token(self, user_id: str, expires_at: datetime) -> str:
        token = secrets.token_urlsafe(32)
        self._reset_tokens[hash_token(token)] = (user_id, expires_at)
        return token

    async def consume_password_reset_token(self, token: str) -> AuthUser | None:
        hashed = hash_token(token)
        record = self._reset_tokens.pop(hashed, None)
        if record is None:
            return None
        user_id, expires_at = record
        if expires_at <= datetime.now(UTC):
            return None
        return await self.get_user(user_id)

    async def get_password_policy(self) -> PasswordPolicy:
        return self._password_policy

    async def update_password_policy(self, policy: PasswordPolicy) -> None:
        self._password_policy = policy


class PostgresAuthRepository:
    def __init__(self, pool: Any) -> None:
        self._pool = pool

    async def create_user(self, email: str, password_hash: str, name: str | None = None) -> AuthUser:
        normalized = normalize_email(email)
        async with self._pool.acquire() as connection:
            try:
                row = await connection.fetchrow(
                    """
                    INSERT INTO users (user_id, email, password_hash, name)
                    VALUES ($1, $2, $3, $4)
                    RETURNING user_id, email, password_hash, name, email_verified_at, created_at
                    """,
                    f"user-{uuid4().hex[:16]}",
                    normalized,
                    password_hash,
                    name,
                )
            except Exception as exc:
                if "users_email_key" in str(exc):
                    raise ValueError("email already registered") from exc
                raise
        return _user_from_row(row)

    async def get_user_by_email(self, email: str) -> AuthUser | None:
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                SELECT user_id, email, password_hash, name, email_verified_at, created_at
                FROM users
                WHERE email = $1
                """,
                normalize_email(email),
            )
        return _user_from_row(row) if row else None

    async def get_user(self, user_id: str) -> AuthUser | None:
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                SELECT user_id, email, password_hash, name, email_verified_at, created_at
                FROM users
                WHERE user_id = $1
                """,
                user_id,
            )
        return _user_from_row(row) if row else None

    async def mark_email_verified(self, user_id: str) -> AuthUser | None:
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                UPDATE users
                SET email_verified_at = COALESCE(email_verified_at, now()), updated_at = now()
                WHERE user_id = $1
                RETURNING user_id, email, password_hash, name, email_verified_at, created_at
                """,
                user_id,
            )
        return _user_from_row(row) if row else None

    async def update_password(self, user_id: str, password_hash: str) -> None:
        async with self._pool.acquire() as connection:
            await connection.execute(
                "UPDATE users SET password_hash = $2, updated_at = now() WHERE user_id = $1",
                user_id,
                password_hash,
            )

    async def create_session(self, user_id: str, expires_at: datetime) -> str:
        token = secrets.token_urlsafe(32)
        async with self._pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO sessions (session_id, user_id, token_hash, expires_at)
                VALUES ($1, $2, $3, $4)
                """,
                f"sess-{uuid4().hex[:16]}",
                user_id,
                hash_token(token),
                expires_at,
            )
        return token

    async def get_session_user(self, token: str) -> AuthUser | None:
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                SELECT u.user_id, u.email, u.password_hash, u.name, u.email_verified_at, u.created_at
                FROM sessions s
                JOIN users u ON u.user_id = s.user_id
                WHERE s.token_hash = $1 AND s.expires_at > now()
                """,
                hash_token(token),
            )
        return _user_from_row(row) if row else None

    async def delete_session(self, token: str) -> None:
        async with self._pool.acquire() as connection:
            await connection.execute("DELETE FROM sessions WHERE token_hash = $1", hash_token(token))

    async def delete_sessions_for_user(self, user_id: str) -> None:
        async with self._pool.acquire() as connection:
            await connection.execute("DELETE FROM sessions WHERE user_id = $1", user_id)

    async def refresh_session(self, token: str) -> bool:
        async with self._pool.acquire() as connection:
            result = await connection.execute(
                """
                UPDATE sessions
                SET expires_at = $2
                WHERE token_hash = $1
                  AND expires_at > now()
                  AND (expires_at - now()) < ($3 * interval '1 second')
                """,
                hash_token(token),
                session_expires_at(),
                SESSION_TTL.total_seconds() / 2,
            )
        return result != "UPDATE 0"

    async def create_email_verification_token(self, user_id: str, expires_at: datetime) -> str:
        token = secrets.token_urlsafe(32)
        async with self._pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO email_verification_tokens (token_hash, user_id, expires_at)
                VALUES ($1, $2, $3)
                """,
                hash_token(token),
                user_id,
                expires_at,
            )
        return token

    async def consume_email_verification_token(self, token: str) -> AuthUser | None:
        hashed = hash_token(token)
        async with self._pool.acquire() as connection:
            async with connection.transaction():
                row = await connection.fetchrow(
                    """
                    DELETE FROM email_verification_tokens
                    WHERE token_hash = $1 AND expires_at > now()
                    RETURNING user_id
                    """,
                    hashed,
                )
                if row is None:
                    return None
        return await self.mark_email_verified(row["user_id"])

    async def create_password_reset_token(self, user_id: str, expires_at: datetime) -> str:
        token = secrets.token_urlsafe(32)
        async with self._pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO password_reset_tokens (token_hash, user_id, expires_at)
                VALUES ($1, $2, $3)
                """,
                hash_token(token),
                user_id,
                expires_at,
            )
        return token

    async def consume_password_reset_token(self, token: str) -> AuthUser | None:
        hashed = hash_token(token)
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                DELETE FROM password_reset_tokens
                WHERE token_hash = $1 AND expires_at > now()
                RETURNING user_id
                """,
                hashed,
            )
        return await self.get_user(row["user_id"]) if row else None

    async def get_password_policy(self) -> PasswordPolicy:
        async with self._pool.acquire() as connection:
            row = await connection.fetchrow(
                """
                SELECT min_length, require_uppercase, require_lowercase, require_digit, require_special
                FROM password_policy
                WHERE policy_id = 'default'
                """
            )
        if row is None:
            return PasswordPolicy()
        return PasswordPolicy(
            min_length=row["min_length"],
            require_uppercase=row["require_uppercase"],
            require_lowercase=row["require_lowercase"],
            require_digit=row["require_digit"],
            require_special=row["require_special"],
        )


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    if _password_hasher is not None:
        return "argon2$" + _password_hasher.hash(password)
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 210_000).hex()
    return f"pbkdf2${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("argon2$") and _password_hasher is not None:
        try:
            return _password_hasher.verify(password_hash.removeprefix("argon2$"), password)
        except VerifyMismatchError:
            return False
    if password_hash.startswith("pbkdf2$"):
        _, salt, expected = password_hash.split("$", 2)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 210_000).hex()
        return hmac.compare_digest(digest, expected)
    return False


def password_policy_errors(password: str, policy: PasswordPolicy) -> list[str]:
    errors = []
    if len(password) < policy.min_length:
        errors.append(f"password must be at least {policy.min_length} characters")
    if policy.require_uppercase and not any(char.isupper() for char in password):
        errors.append("password must include an uppercase letter")
    if policy.require_lowercase and not any(char.islower() for char in password):
        errors.append("password must include a lowercase letter")
    if policy.require_digit and not any(char.isdigit() for char in password):
        errors.append("password must include a number")
    if policy.require_special and not any(not char.isalnum() for char in password):
        errors.append("password must include a symbol")
    return errors


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_expires_at() -> datetime:
    return datetime.now(UTC) + SESSION_TTL


def token_expires_at() -> datetime:
    return datetime.now(UTC) + TOKEN_TTL


def _cookie_domain() -> str | None:
    # Set PREON_COOKIE_DOMAIN=localhost in dev so the cookie works on both :3000 and :8000.
    # Set it to your root domain in production (e.g. "preon.example.com").
    domain = os.getenv("PREON_COOKIE_DOMAIN", "").strip()
    return domain or None


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        secure=os.getenv("PREON_COOKIE_SECURE", "").lower() in {"1", "true", "yes"},
        samesite="lax",
        max_age=int(SESSION_TTL.total_seconds()),
        path="/",
        domain=_cookie_domain(),
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/", domain=_cookie_domain())


async def require_current_user(request: Request) -> AuthUser:
    user = await optional_current_user(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required")
    return user


async def optional_current_user(request: Request) -> AuthUser | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    return await request.app.state.auth.get_session_user(token)


def require_csrf(request: Request) -> None:
    if request.method in SAFE_METHODS or SESSION_COOKIE_NAME not in request.cookies:
        return
    origin = request.headers.get("origin") or request.headers.get("referer")
    if not origin:
        if request.headers.get("host") == "testserver":
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="missing request origin")
    allowed = {
        f"{request.url.scheme}://{request.url.netloc}",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    }
    configured_frontend = os.getenv("PREON_FRONTEND_URL") or os.getenv("NEXT_PUBLIC_APP_URL")
    if configured_frontend:
        allowed.add(configured_frontend.rstrip("/"))
    if not any(origin.startswith(candidate) for candidate in allowed):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid request origin")


def check_rate_limit(key: str, limit: int = 8, window_seconds: int = 300) -> None:
    if not auth_rate_limiter.check_and_record(key, limit, window_seconds):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too many attempts")


def auth_url(request: Request, path: str, token: str) -> str:
    base = frontend_base_url(request)
    return f"{base}{path}?token={token}"


def frontend_base_url(request: Request) -> str:
    configured = os.getenv("PREON_FRONTEND_URL") or os.getenv("NEXT_PUBLIC_APP_URL")
    if configured:
        return configured.rstrip("/")
    base = str(request.base_url).rstrip("/")
    if base in {"http://127.0.0.1:8000", "http://localhost:8000"}:
        host = "localhost" if "localhost" in base else "127.0.0.1"
        return f"http://{host}:3000"
    return base


def oauth_authorization_url(provider: str) -> str | None:
    prefix = f"PREON_{provider.upper()}_OAUTH"
    client_id = os.getenv(f"{prefix}_CLIENT_ID")
    authorize_url = os.getenv(f"{prefix}_AUTHORIZE_URL")
    redirect_uri = os.getenv(f"{prefix}_REDIRECT_URI")
    if not client_id or not authorize_url or not redirect_uri:
        return None
    state = secrets.token_urlsafe(18)
    return (
        f"{authorize_url}?client_id={client_id}&redirect_uri={redirect_uri}"
        f"&response_type=code&scope=openid%20email%20profile&state={state}"
    )


def _user_from_row(row: Any) -> AuthUser:
    return AuthUser(
        id=row["user_id"],
        email=row["email"],
        password_hash=row["password_hash"],
        name=row["name"],
        email_verified_at=row["email_verified_at"],
        created_at=row["created_at"],
    )
