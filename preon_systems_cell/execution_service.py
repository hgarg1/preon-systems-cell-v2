from __future__ import annotations

import asyncio
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from functools import partial
from contextvars import ContextVar
from threading import BoundedSemaphore, Event, RLock
from typing import Callable, Iterator, TypeVar

from preon_systems_cell.resilience import FailureType, RuntimeFailure


T = TypeVar("T")


class CancellationToken:
    def __init__(self) -> None:
        self._cancelled = Event()

    def cancel(self) -> None:
        self._cancelled.set()

    @property
    def cancelled(self) -> bool:
        return self._cancelled.is_set()

    def checkpoint(self) -> None:
        if self.cancelled:
            raise RuntimeFailure(
                "execution cancelled",
                failure_type=FailureType.CANCELLED,
                retryable=False,
            )


_CURRENT_TOKEN: ContextVar[CancellationToken | None] = ContextVar(
    "preon_execution_cancellation",
    default=None,
)


def cancellation_checkpoint() -> None:
    token = _CURRENT_TOKEN.get()
    if token is not None:
        token.checkpoint()


def current_cancellation_token() -> CancellationToken | None:
    return _CURRENT_TOKEN.get()


def _run_with_token(
    token: CancellationToken,
    operation: Callable[..., T],
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> T:
    context_token = _CURRENT_TOKEN.set(token)
    try:
        token.checkpoint()
        return operation(*args, **kwargs)
    finally:
        _CURRENT_TOKEN.reset(context_token)


class SharedExecutionService:
    def __init__(
        self,
        *,
        max_workers: int = 16,
        global_limit: int = 16,
        per_organism_limit: int = 4,
        per_provider_limit: int = 4,
    ) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="preon-runtime")
        self._step_executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="preon-cell-step",
        )
        self._global = asyncio.Semaphore(global_limit)
        self._per_organism_limit = per_organism_limit
        self._organisms: dict[str, asyncio.Semaphore] = {}
        self._provider_limit = per_provider_limit
        self._providers: dict[str, BoundedSemaphore] = defaultdict(
            lambda: BoundedSemaphore(self._provider_limit)
        )
        self._lock = RLock()
        self._sync_global = BoundedSemaphore(global_limit)
        self._sync_organisms: dict[str, BoundedSemaphore] = {}

    async def run(
        self,
        organism_id: str,
        operation: Callable[..., T],
        *args: object,
        timeout_seconds: float | None = None,
        **kwargs: object,
    ) -> T:
        organism_limit = self._organisms.setdefault(
            organism_id, asyncio.Semaphore(self._per_organism_limit)
        )
        async with self._global, organism_limit:
            loop = asyncio.get_running_loop()
            cancellation = CancellationToken()
            future = loop.run_in_executor(
                self._executor,
                partial(_run_with_token, cancellation, operation, args, kwargs),
            )
            try:
                if timeout_seconds is None:
                    return await future
                return await asyncio.wait_for(future, timeout=timeout_seconds)
            except TimeoutError as exc:
                cancellation.cancel()
                future.cancel()
                raise RuntimeFailure(
                    "execution deadline exceeded",
                    failure_type=FailureType.TIMEOUT,
                    retryable=False,
                ) from exc
            except asyncio.CancelledError:
                cancellation.cancel()
                future.cancel()
                raise

    @contextmanager
    def provider_slot(self, provider: str, timeout_seconds: float) -> Iterator[None]:
        semaphore = self._providers[provider]
        if not semaphore.acquire(timeout=max(0.0, timeout_seconds)):
            raise RuntimeFailure(
                f"provider concurrency saturated: {provider}",
                failure_type=FailureType.SATURATION,
                retryable=True,
            )
        try:
            yield
        finally:
            semaphore.release()

    def run_wave_sync(
        self,
        organism_id: str,
        operations: list[Callable[[], T]],
        *,
        max_parallelism: int,
    ) -> list[T]:
        organism_limit = self._sync_organisms.setdefault(
            organism_id,
            BoundedSemaphore(self._per_organism_limit),
        )
        wave_limit = BoundedSemaphore(max(1, max_parallelism))
        parent_token = current_cancellation_token()

        def bounded(operation: Callable[[], T]) -> T:
            context_token = _CURRENT_TOKEN.set(parent_token)
            try:
                cancellation_checkpoint()
                with self._sync_global, organism_limit, wave_limit:
                    cancellation_checkpoint()
                    return operation()
            finally:
                _CURRENT_TOKEN.reset(context_token)

        futures = [self._step_executor.submit(bounded, operation) for operation in operations]
        return [future.result() for future in futures]

    def close(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=True)
        self._step_executor.shutdown(wait=True, cancel_futures=True)


DEFAULT_EXECUTION_SERVICE = SharedExecutionService()
