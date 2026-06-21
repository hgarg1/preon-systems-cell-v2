from __future__ import annotations

import json
from pathlib import Path

from preon_systems_cell.models import RuntimeEvent


def write_runtime_events_jsonl(path: str | Path, events: list[RuntimeEvent]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event.model_dump(mode="json"), sort_keys=True))
            handle.write("\n")
