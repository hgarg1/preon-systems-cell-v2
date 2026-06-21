"""Execution telemetry sink for model routing decisions.

Phase 2: in-memory append-only log.
Phase 12: replace _log with a structured sink (time-series DB, event stream, etc.)
          and add the weighted scoring feedback loop that reads from it.
"""
from __future__ import annotations

import dataclasses

from preon_systems_cell.model_routing.types import ModelExecutionTelemetry

_log: list[dict] = []


def log_execution(telemetry: ModelExecutionTelemetry) -> None:
    _log.append(dataclasses.asdict(telemetry))


def get_log() -> list[dict]:
    """Return a snapshot of all logged telemetry records."""
    return list(_log)


def clear_log() -> None:
    """Clear the in-memory log.  Used in tests and maintenance resets."""
    _log.clear()
