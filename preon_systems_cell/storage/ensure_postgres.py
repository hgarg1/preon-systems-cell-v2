from __future__ import annotations

import asyncio
import os
from pathlib import Path
import shutil
import subprocess
import sys

try:
    import asyncpg
except ImportError:  # pragma: no cover - command-line guard
    asyncpg = None  # type: ignore[assignment]


DEFAULT_WINDOWS_PGDATA = Path("C:/Program Files/PostgreSQL/18/data")
DEFAULT_WINDOWS_PGCTL = Path("C:/Program Files/PostgreSQL/18/bin/pg_ctl.exe")


async def _can_connect(database_url: str) -> bool:
    if asyncpg is None:
        print('asyncpg is not installed; run python -m pip install -e ".[postgres]"', file=sys.stderr)
        return False
    try:
        connection = await asyncpg.connect(database_url, timeout=5)
        try:
            await connection.fetchval("select 1")
        finally:
            await connection.close()
        return True
    except Exception as exc:
        print(f"Postgres connection check failed: {type(exc).__name__}", file=sys.stderr)
        return False


def _pg_ctl_path() -> str | None:
    configured = os.getenv("PREON_PG_CTL")
    if configured:
        return configured
    discovered = shutil.which("pg_ctl")
    if discovered:
        return discovered
    if DEFAULT_WINDOWS_PGCTL.exists():
        return str(DEFAULT_WINDOWS_PGCTL)
    return None


def _pgdata_path() -> str | None:
    configured = os.getenv("PREON_PGDATA")
    if configured:
        return configured
    if DEFAULT_WINDOWS_PGDATA.exists():
        return str(DEFAULT_WINDOWS_PGDATA)
    return None


def _try_start_local_postgres() -> bool:
    pg_ctl = _pg_ctl_path()
    pgdata = _pgdata_path()
    if not pg_ctl or not pgdata:
        return False

    log_path = os.getenv("PREON_PG_START_LOG") or str(Path.cwd() / "postgres-local.log")
    result = subprocess.run(
        [pg_ctl, "-D", pgdata, "-l", log_path, "start"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=25,
        check=False,
    )
    return result.returncode == 0


async def main() -> int:
    database_url = os.getenv("PREON_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not database_url:
        print("PREON_DATABASE_URL or DATABASE_URL must be set before running the web app.", file=sys.stderr)
        return 2

    if await _can_connect(database_url):
        return 0

    if _try_start_local_postgres():
        await asyncio.sleep(2)
        if await _can_connect(database_url):
            return 0

    print("Postgres is not reachable. Start Postgres or fix PREON_DATABASE_URL before launching.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
