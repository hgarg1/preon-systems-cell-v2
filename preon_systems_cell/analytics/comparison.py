from __future__ import annotations

from preon_systems_cell.models import OrganismDetailResponse


def compare_organisms(details: list[OrganismDetailResponse]) -> list[dict[str, object]]:
    return [
        {
            "organism_id": detail.organism.organism_id,
            "cell_count": len(detail.cells),
            "protein_count": len(detail.proteins),
            "event_count": len(detail.events),
        }
        for detail in details
    ]
