"""TissueModelCouncil — stub.  Full implementation in Phase 6 (tissue runtime).

Resolves model choice when multiple cells disagree or domain-level coherence
is required.  Not invoked in Phase 2 — CellModelRouter always resolves locally.
"""
from __future__ import annotations

from preon_systems_cell.model_routing.types import LlmProteinInstantiationRequest, ModelRoutingDecision


class TissueModelCouncil:
    def resolve(
        self,
        request: LlmProteinInstantiationRequest,
        cell_decisions: list[ModelRoutingDecision],
    ) -> ModelRoutingDecision | None:
        return None
