from __future__ import annotations

from typing import Protocol

from preon_systems_cell.models import RuntimeEvent


class RuntimeTelemetrySink(Protocol):
    def on_events(self, events: list[RuntimeEvent]) -> None: ...


class InMemoryRuntimeTelemetrySink:
    def __init__(self) -> None:
        self.events: list[RuntimeEvent] = []

    def on_events(self, events: list[RuntimeEvent]) -> None:
        self.events.extend(events)
