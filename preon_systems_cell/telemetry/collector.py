from __future__ import annotations

from preon_systems_cell.models import RuntimeEvent
from preon_systems_cell.telemetry.sinks import RuntimeTelemetrySink


class RuntimeTelemetryCollector:
    def __init__(self, sinks: list[RuntimeTelemetrySink]) -> None:
        self.sinks = sinks

    def record_events(self, events: list[RuntimeEvent]) -> None:
        for sink in self.sinks:
            sink.on_events(events)
