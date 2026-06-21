from __future__ import annotations

from preon_systems_cell.models import OrganismDetailResponse


def summarize_runtime(detail: OrganismDetailResponse) -> dict[str, object]:
    blocked = [protein for protein in detail.proteins if protein.status.value == "blocked"]
    return {
        "organism_id": detail.organism.organism_id,
        "status": detail.organism.lifecycle_state.value,
        "approved_proteins": len([protein for protein in detail.proteins if protein.status.value == "approved"]),
        "blocked_proteins": len(blocked),
        "open_structure_requests": len([request for request in detail.structure_requests if request.status == "open"]),
    }
