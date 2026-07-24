from __future__ import annotations

from contextlib import AbstractContextManager
from copy import deepcopy
from threading import RLock
from typing import Protocol, Self

from preon_systems_cell.runtime.stores import RuntimeStores


class RuntimeUnitOfWork(Protocol):
    stores: RuntimeStores

    def __enter__(self) -> Self: ...

    def __exit__(self, exc_type, exc, traceback) -> bool | None: ...

    def commit(self) -> None: ...


class InMemoryRuntimeUnitOfWork(AbstractContextManager):
    """Atomic copy-on-write boundary for multi-record in-memory commands."""

    def __init__(self, stores: RuntimeStores, lock: RLock | None = None) -> None:
        self.stores = stores
        self._lock = lock or RLock()
        self._snapshot: RuntimeStores | None = None
        self._committed = False

    def __enter__(self) -> Self:
        self._lock.acquire()
        self._snapshot = deepcopy(self.stores)
        self._committed = False
        return self

    def commit(self) -> None:
        self._committed = True

    def __exit__(self, exc_type, exc, traceback) -> bool | None:
        try:
            if (exc_type is not None or not self._committed) and self._snapshot is not None:
                self.stores.__dict__.clear()
                self.stores.__dict__.update(self._snapshot.__dict__)
        finally:
            self._snapshot = None
            self._lock.release()
        return None
