from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from threading import RLock
import time
from typing import Callable, TypeVar


class FailureType(StrEnum):
    VALIDATION = "validation"
    TRANSIENT_PROVIDER = "transient_provider"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    SATURATION = "saturation"
    POLICY_REJECTION = "policy_rejection"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    INTERNAL = "internal"


class RuntimeFailure(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        failure_type: FailureType,
        retryable: bool = False,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.failure_type = failure_type
        self.retryable = retryable
        self.trace_id = trace_id


class PolicyRejection(RuntimeFailure):
    def __init__(self, message: str, *, trace_id: str | None = None) -> None:
        super().__init__(
            message,
            failure_type=FailureType.POLICY_REJECTION,
            retryable=False,
            trace_id=trace_id,
        )


class CircuitOpen(RuntimeFailure):
    def __init__(self, provider: str) -> None:
        super().__init__(
            f"provider circuit is open: {provider}",
            failure_type=FailureType.TRANSIENT_PROVIDER,
            retryable=True,
        )


@dataclass(frozen=True)
class RetryBudget:
    max_attempts: int = 2
    deadline_monotonic: float | None = None
    base_delay_seconds: float = 0.05

    def permits(self, next_attempt: int) -> bool:
        if next_attempt > self.max_attempts:
            return False
        return self.deadline_monotonic is None or time.monotonic() < self.deadline_monotonic


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_seconds: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = RLock()

    @property
    def state(self) -> str:
        with self._lock:
            if self._opened_at is None:
                return "closed"
            if time.monotonic() - self._opened_at >= self.recovery_seconds:
                return "half_open"
            return "open"

    def allow(self) -> bool:
        return self.state != "open"

    def success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None

    def failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._opened_at = time.monotonic()


class ProviderCircuitRegistry:
    def __init__(self) -> None:
        self._circuits: dict[str, CircuitBreaker] = {}
        self._lock = RLock()

    def for_provider(self, provider: str) -> CircuitBreaker:
        with self._lock:
            return self._circuits.setdefault(provider, CircuitBreaker())

    def states(self) -> dict[str, str]:
        with self._lock:
            return {provider: circuit.state for provider, circuit in self._circuits.items()}


T = TypeVar("T")


def retry_bounded(
    operation: Callable[[], T],
    *,
    budget: RetryBudget,
    is_retryable: Callable[[Exception], bool],
) -> T:
    attempt = 1
    while True:
        try:
            return operation()
        except Exception as exc:
            next_attempt = attempt + 1
            if not is_retryable(exc) or not budget.permits(next_attempt):
                raise
            delay = budget.base_delay_seconds * (2 ** (attempt - 1))
            if budget.deadline_monotonic is not None:
                delay = min(delay, max(0.0, budget.deadline_monotonic - time.monotonic()))
            if delay:
                time.sleep(delay)
            attempt = next_attempt
