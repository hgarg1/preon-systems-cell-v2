"""OrganModelPolicy — stub.  Full implementation in Phase 9 (organ coordination).

Resolves model choice when the decision affects a full domain (coding organ,
planning organ, memory organ, etc.).  Not invoked in Phase 2.
"""
from __future__ import annotations

from preon_systems_cell.model_routing.types import LlmProteinInstantiationRequest, ModelRoutingDecision


class OrganModelPolicy:
    def resolve(
        self,
        request: LlmProteinInstantiationRequest,
        tissue_decisions: list[ModelRoutingDecision],
    ) -> ModelRoutingDecision | None:
        return None
