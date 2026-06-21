from __future__ import annotations

from collections import Counter

from preon_systems_cell.models import RuntimeEvent


def event_counts(events: list[RuntimeEvent]) -> dict[str, int]:
    return dict(Counter(event.type.value for event in events))
