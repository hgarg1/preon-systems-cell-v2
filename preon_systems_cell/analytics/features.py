from __future__ import annotations

from preon_systems_cell.models import OrganismDetailResponse


def extract_runtime_features(detail: OrganismDetailResponse) -> dict[str, object]:
    return {
        "organism_id": detail.organism.organism_id,
        "lifecycle_state": detail.organism.lifecycle_state.value,
        "cell_count": len(detail.cells),
        "protein_count": len(detail.proteins),
        "event_count": len(detail.events),
        "structure_request_count": len(detail.structure_requests),
    }
