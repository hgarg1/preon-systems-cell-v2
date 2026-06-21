from __future__ import annotations

from dataclasses import dataclass
import logging
import os

from preon_systems_cell.auth import InMemoryAuthRepository, PostgresAuthRepository
from preon_systems_cell.storage.postgres import PostgresRuntimeStore, PostgresSettings, PostgresUnavailableError


logger = logging.getLogger("preon_systems_cell.storage")


@dataclass(frozen=True)
class StorageStatus:
    mode: str
    primary: str
    fallback: str
    degraded: bool
    reason: str | None = None

    def model_dump(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "primary": self.primary,
            "fallback": self.fallback,
            "degraded": self.degraded,
            "reason": self.reason,
        }


class StorageManager:
    def __init__(
        self,
        *,
        postgres: PostgresRuntimeStore | None,
        status: StorageStatus,
        auth: InMemoryAuthRepository | PostgresAuthRepository,
    ) -> None:
        self.postgres = postgres
        self.status = status
        self.auth = auth

    @classmethod
    async def create(cls, settings: PostgresSettings | None = None) -> "StorageManager":
        forced_mode = os.getenv("PREON_STORAGE_MODE", "postgres").strip().lower()
        if forced_mode == "memory":
            status = StorageStatus(
                mode="memory",
                primary="postgres",
                fallback="memory",
                degraded=True,
                reason="PREON_STORAGE_MODE=memory",
            )
            logger.warning("storage_mode_selected", extra=status.model_dump())
            return cls(postgres=None, status=status, auth=InMemoryAuthRepository())

        try:
            postgres = await PostgresRuntimeStore.create(settings or PostgresSettings.from_env())
        except Exception as exc:
            if os.getenv("PREON_REQUIRE_POSTGRES", "").strip().lower() in {"1", "true", "yes"}:
                logger.error("postgres_required_unavailable", extra={"reason": _public_fallback_reason(exc)})
                raise
            status = StorageStatus(
                mode="memory",
                primary="postgres",
                fallback="memory",
                degraded=True,
                reason=_public_fallback_reason(exc),
            )
            logger.warning("storage_fallback_activated", extra=status.model_dump())
            return cls(postgres=None, status=status, auth=InMemoryAuthRepository())

        status = StorageStatus(mode="postgres", primary="postgres", fallback="memory", degraded=False)
        logger.info("storage_mode_selected", extra=status.model_dump())
        return cls(postgres=postgres, status=status, auth=PostgresAuthRepository(postgres._pool))

    async def close(self) -> None:
        if self.postgres is not None:
            await self.postgres.close()


def _public_fallback_reason(exc: Exception) -> str:
    if isinstance(exc, PostgresUnavailableError):
        return str(exc)
    return "Postgres connection failed; using in-memory fallback"
