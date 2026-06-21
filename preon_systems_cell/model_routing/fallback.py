"""Build fallback chains from scored candidate lists."""
from __future__ import annotations

from preon_systems_cell.model_routing.types import ModelCandidate


def build_fallback_chain(
    remaining_candidates: list[ModelCandidate],
) -> list[tuple[str, str, str | None]]:
    """Ordered fallback chain derived from candidates that didn't win primary selection.

    The stub is appended as the final unconditional fallback so the chain always
    terminates without raising.
    """
    chain: list[tuple[str, str, str | None]] = [
        (c.provider, c.model_class, c.model_id) for c in remaining_candidates
    ]
    if not any(p == "stub" for p, _, _ in chain):
        chain.append(("stub", "stub", None))
    return chain
