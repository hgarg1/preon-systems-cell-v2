"""Cell-level model router — Day-One deterministic policy.

Implements the algorithm defined in the roadmap:
  1. Filter MODEL_REGISTRY by hard constraints (key present, provider allowed,
     data policy compatible, context window fits).
  2. Among passing candidates, prefer by cost_tier / latency_budget.
  3. Walk fallback chain if primary unavailable.
  4. Always resolves — never escalates at this phase (Tissue/Organ stubs return None).

Confidence is fixed at 0.9 for all deterministic-policy decisions.  The confidence
threshold and escalation logic activate in Phase 6 once TissueModelCouncil is live.
"""
from __future__ import annotations

import os

from preon_systems_cell.model_routing.fallback import build_fallback_chain
from preon_systems_cell.model_routing.registry import MODEL_REGISTRY, ProviderModelProfile
from preon_systems_cell.model_routing.types import (
    LlmProteinInstantiationRequest,
    ModelCandidate,
    ModelRoutingDecision,
)

_ENV_KEYS: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "grok": "XAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def _key_present(provider: str) -> bool:
    env = _ENV_KEYS.get(provider, "")
    return bool(env and os.environ.get(env))


class CellModelRouter:
    """Day-One deterministic policy router.

    Always resolves locally — TissueModelCouncil / OrganModelPolicy / OrganismRoutingAuthority
    are stubs that return None in Phase 2.
    """

    def resolve(self, request: LlmProteinInstantiationRequest) -> ModelRoutingDecision:
        candidates = self._score_candidates(request)

        if not candidates:
            return ModelRoutingDecision(
                selected_provider="stub",
                selected_model_class="stub",
                selected_model_id=None,
                confidence=0.0,
                resolved_at="cell",
                candidates=[],
                consensus_path=["cell"],
                fallback_chain=[("stub", "stub", None)],
                token_budget=request.token_budget,
                latency_budget_ms=request.latency_budget_ms,
                data_policy=request.data_class,
                routing_reason="No valid provider found after applying hard constraints; using stub",
            )

        best = candidates[0]
        return ModelRoutingDecision(
            selected_provider=best.provider,
            selected_model_class=best.model_class,
            selected_model_id=best.model_id,
            confidence=best.confidence,
            resolved_at="cell",
            candidates=candidates,
            consensus_path=["cell"],
            fallback_chain=build_fallback_chain(candidates[1:]),
            token_budget=request.token_budget,
            latency_budget_ms=request.latency_budget_ms,
            data_policy=request.data_class,
            routing_reason=best.reason,
        )

    def _score_candidates(self, request: LlmProteinInstantiationRequest) -> list[ModelCandidate]:
        results: list[ModelCandidate] = []
        for profile in MODEL_REGISTRY:
            candidate = self._evaluate(profile, request)
            if candidate is not None:
                results.append(candidate)
        return sorted(results, key=lambda c: c.total_score, reverse=True)

    def _evaluate(
        self, profile: ProviderModelProfile, request: LlmProteinInstantiationRequest
    ) -> ModelCandidate | None:
        # Hard constraints — any failure eliminates the candidate
        if not _key_present(profile.provider):
            return None
        if request.allowed_providers and profile.provider not in request.allowed_providers:
            return None
        if request.data_class not in profile.allowed_data_classes:
            return None
        if profile.max_context_tokens < request.context_size_estimate:
            return None
        # min_reasoning_depth is a floor: "deep" requires reasoning class,
        # "moderate" requires at least standard class.
        if request.reasoning_depth == "deep" and profile.model_class in ("fast", "standard"):
            return None
        if request.reasoning_depth == "moderate" and profile.model_class == "fast":
            return None

        # Soft scores — all hard constraints passed
        cost_score = 1.0 - profile.relative_cost
        latency_headroom = max(request.latency_budget_ms - profile.average_latency_ms, 0)
        latency_score = min(latency_headroom / max(request.latency_budget_ms, 1), 1.0)
        policy_score = 1.0
        # Quality preference by model class: tuned per cost_tier so each tier
        # produces the expected model class winner (cheap→fast, balanced→standard,
        # premium→reasoning) without weighted scoring becoming over-complex.
        if request.cost_tier == "cheap":
            total = cost_score * 0.7 + latency_score * 0.2 + policy_score * 0.1
        elif 0 < request.latency_budget_ms <= 1000:
            total = latency_score * 0.6 + cost_score * 0.3 + policy_score * 0.1
        elif request.cost_tier == "premium":
            class_quality = {"fast": 0.0, "standard": 0.5, "reasoning": 1.0}.get(profile.model_class, 0.3)
            total = class_quality * 0.5 + policy_score * 0.3 + latency_score * 0.1 + cost_score * 0.1
        else:  # balanced — standard wins; reasoning penalised for cost
            class_quality = {"fast": 0.0, "standard": 1.0, "reasoning": 0.3}.get(profile.model_class, 0.4)
            total = class_quality * 0.35 + cost_score * 0.25 + latency_score * 0.2 + policy_score * 0.2

        return ModelCandidate(
            provider=profile.provider,
            model_class=profile.model_class,
            model_id=profile.model_id,
            cost_score=cost_score,
            latency_score=latency_score,
            policy_score=policy_score,
            total_score=total,
            confidence=0.9,
            reason=(
                f"{profile.provider}/{profile.model_class} satisfies all constraints "
                f"(cost={cost_score:.2f}, latency={latency_score:.2f})"
            ),
        )
