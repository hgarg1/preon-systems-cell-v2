from __future__ import annotations

from collections import Counter

from preon_systems_cell.models import RuntimeEvent


def runtime_event_series(events: list[RuntimeEvent]) -> list[dict[str, object]]:
    counts = Counter(event.type.value for event in events)
    return [{"type": event_type, "count": count} for event_type, count in sorted(counts.items())]
