"""Rate-limit stores: in-memory default, Postgres-backed for multi-instance production.

Usage:
  from preon_systems_cell.rate_limit import auth_rate_limiter

The module-level `auth_rate_limiter` is InMemoryRateLimitStore by default.
For production multi-instance deployments, replace it at startup:

  from preon_systems_cell.rate_limit import PostgresRateLimitStore
  import preon_systems_cell.rate_limit as rl
  rl.auth_rate_limiter = PostgresRateLimitStore(dsn=os.environ["DATABASE_URL"])

PostgresRateLimitStore requires a rate_limit_log table — see schema below.
"""
from __future__ import annotations

import time
from typing import Protocol, runtime_checkable


@runtime_checkable
class RateLimitStore(Protocol):
    def check_and_record(self, key: str, limit: int, window_seconds: int) -> bool: ...
    def clear(self) -> None: ...


class InMemoryRateLimitStore:
    """Sliding-window rate limiter backed by an in-process dict.

    Correct for single-process deployments. Does not survive process restarts or
    multi-replica scaling; use PostgresRateLimitStore in those environments.
    """

    def __init__(self) -> None:
        self._log: dict[str, list[float]] = {}

    def check_and_record(self, key: str, limit: int, window_seconds: int) -> bool:
        """Return True if the request is within the limit and record the attempt."""
        now = time.time()
        window = [t for t in self._log.get(key, []) if now - t < window_seconds]
        if len(window) >= limit:
            return False
        window.append(now)
        self._log[key] = window
        return True

    def clear(self) -> None:
        self._log.clear()


class PostgresRateLimitStore:
    """Sliding-window rate limiter backed by Postgres.

    Safe across multiple replicas: uses a single transaction with conditional INSERT
    to prevent race-condition over-admission.

    Required schema (run once, idempotent):
        CREATE TABLE IF NOT EXISTS rate_limit_log (
            key TEXT        NOT NULL,
            ts  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_rl_key_ts ON rate_limit_log (key, ts);
    """

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def check_and_record(self, key: str, limit: int, window_seconds: int) -> bool:
        try:
            import psycopg2  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError("psycopg2 is required for PostgresRateLimitStore") from exc

        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                # Purge expired entries first, then conditionally insert in one round-trip.
                cur.execute(
                    "DELETE FROM rate_limit_log WHERE key = %s"
                    " AND ts < NOW() - make_interval(secs => %s::float);",
                    (key, float(window_seconds)),
                )
                cur.execute(
                    "INSERT INTO rate_limit_log (key)"
                    " SELECT %s FROM (SELECT COUNT(*) AS cnt FROM rate_limit_log WHERE key = %s) sub"
                    " WHERE sub.cnt < %s RETURNING 1;",
                    (key, key, limit),
                )
                admitted = cur.fetchone() is not None
            conn.commit()
        return admitted

    def clear(self) -> None:
        try:
            import psycopg2
        except ImportError:
            return
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM rate_limit_log;")
            conn.commit()


# Default instance.  Replace at startup with PostgresRateLimitStore for multi-instance deployments.
auth_rate_limiter: InMemoryRateLimitStore = InMemoryRateLimitStore()
