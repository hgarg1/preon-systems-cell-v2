"""Unit tests for Phase 2: CellModelRouter deterministic Day-One policy."""
import os

import pytest

from preon_systems_cell.model_routing.cell_router import CellModelRouter
from preon_systems_cell.model_routing.types import LlmProteinInstantiationRequest


def _request(**overrides) -> LlmProteinInstantiationRequest:
    defaults = dict(
        signal_id="sig-test",
        task_id="sig-test",
        module_id="module-test",
        protein_type="reasoning",
        capability_required="query",
        reasoning_depth="moderate",
        cost_tier="balanced",
        data_class="internal",
        latency_budget_ms=5000,
        token_budget=4096,
        context_size_estimate=500,
        allowed_providers=[],
    )
    defaults.update(overrides)
    return LlmProteinInstantiationRequest(**defaults)


@pytest.fixture
def all_keys(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")


@pytest.fixture
def anthropic_only(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


@pytest.fixture
def no_keys(monkeypatch):
    for var in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(var, raising=False)


class TestTierSelection:
    def test_balanced_selects_standard_class(self, all_keys):
        decision = CellModelRouter().resolve(_request(cost_tier="balanced"))
        assert decision.selected_model_class == "standard"

    def test_premium_selects_reasoning_class(self, all_keys):
        decision = CellModelRouter().resolve(_request(cost_tier="premium"))
        assert decision.selected_model_class == "reasoning"

    def test_cheap_selects_fast_class(self, all_keys):
        # reasoning_depth="shallow" lets fast models pass the depth floor
        decision = CellModelRouter().resolve(_request(cost_tier="cheap", reasoning_depth="shallow"))
        assert decision.selected_model_class == "fast"

    def test_tight_latency_prioritises_fast(self, all_keys):
        # reasoning_depth="shallow" lets fast models pass the depth floor
        decision = CellModelRouter().resolve(_request(latency_budget_ms=800, reasoning_depth="shallow"))
        assert decision.selected_model_class == "fast"


class TestReasoningDepthConstraint:
    def test_deep_eliminates_fast_and_standard(self, all_keys):
        decision = CellModelRouter().resolve(
            _request(cost_tier="balanced", reasoning_depth="deep")
        )
        assert decision.selected_model_class == "reasoning"

    def test_moderate_eliminates_fast(self, all_keys):
        decision = CellModelRouter().resolve(
            _request(cost_tier="cheap", reasoning_depth="moderate")
        )
        # cheap wants fast, but moderate depth floors to standard
        assert decision.selected_model_class in ("standard", "reasoning")
        assert decision.selected_model_class != "fast"

    def test_shallow_allows_fast(self, all_keys):
        decision = CellModelRouter().resolve(
            _request(cost_tier="cheap", reasoning_depth="shallow")
        )
        assert decision.selected_model_class == "fast"


class TestProviderConstraints:
    def test_allowed_providers_respected(self, all_keys):
        decision = CellModelRouter().resolve(
            _request(allowed_providers=["openai"])
        )
        assert decision.selected_provider == "openai"

    def test_single_provider_available(self, anthropic_only):
        decision = CellModelRouter().resolve(_request(cost_tier="balanced"))
        assert decision.selected_provider == "anthropic"
        assert decision.selected_model_class == "standard"

    def test_data_class_restricted_routes_to_openai(self, all_keys):
        # Only openai/o3 supports "restricted" data class
        decision = CellModelRouter().resolve(
            _request(data_class="restricted", cost_tier="premium")
        )
        assert decision.selected_provider == "openai"
        assert decision.selected_model_id == "o3"

    def test_grok_excluded_for_confidential_data(self, all_keys):
        # grok only allows public/internal — confidential should exclude it
        decision = CellModelRouter().resolve(
            _request(data_class="confidential", allowed_providers=["grok", "anthropic"])
        )
        assert decision.selected_provider == "anthropic"


class TestFallback:
    def test_no_keys_returns_stub(self, no_keys):
        decision = CellModelRouter().resolve(_request())
        assert decision.selected_provider == "stub"
        assert decision.confidence == 0.0

    def test_fallback_chain_excludes_winner(self, all_keys):
        decision = CellModelRouter().resolve(_request(cost_tier="balanced"))
        winner = (decision.selected_provider, decision.selected_model_class, decision.selected_model_id)
        for entry in decision.fallback_chain:
            assert entry != winner

    def test_fallback_chain_ends_with_stub(self, all_keys):
        decision = CellModelRouter().resolve(_request())
        assert decision.fallback_chain[-1] == ("stub", "stub", None)

    def test_resolved_at_is_cell(self, all_keys):
        decision = CellModelRouter().resolve(_request())
        assert decision.resolved_at == "cell"

    def test_confidence_is_0_9_for_deterministic_policy(self, all_keys):
        decision = CellModelRouter().resolve(_request())
        assert decision.confidence == 0.9
