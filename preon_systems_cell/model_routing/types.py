"""Core types for the model routing layer.

LlmProteinInstantiationRequest  — intent object the Ribosome creates before calling
                                    a provider; contains only mechanically-derivable fields.
ModelRoutingDecision            — resolved routing result with full observability trace.
ModelCandidate                  — a scored provider/model option produced during routing.
ModelExecutionTelemetry         — per-call execution record logged for future learning.

All are frozen dataclasses.  To "update" a decision as it passes through routing layers
use dataclasses.replace(), not mutation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Literal type aliases — kept as strings so they don't require an extra import at
# call sites and serialise cleanly to JSON.
ProteinType = str    # reasoning | retrieval | transformation | aggregation | evaluation
ReasoningDepth = str  # shallow | moderate | deep
CostTier = str       # cheap | balanced | premium
DataClass = str      # public | internal | confidential | restricted
EscalationLevel = str  # cell | tissue | organ | organism


@dataclass(frozen=True)
class LlmProteinInstantiationRequest:
    """What the Ribosome needs; all values are derivable without a prior LLM call."""

    signal_id: str
    task_id: str        # == signal_id until Phase 8 TaskGraph exists
    module_id: str

    protein_type: ProteinType           # from GenomeModule
    capability_required: str            # from GenomeModule.signal_types[0]

    reasoning_depth: ReasoningDepth     # from GenomeModule.min_reasoning_depth
    cost_tier: CostTier                 # from GenomeModule.max_cost_tier
    data_class: DataClass               # from GenomeModule.data_class_allowed[0]

    latency_budget_ms: int              # from GenomeModule or signal deadline
    token_budget: int                   # from GenomeModule
    context_size_estimate: int          # len(str(signal.payload))

    allowed_providers: list[str]        # from GenomeModule; empty = all registered
    expected_output_schema: dict[str, Any] | None = None

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelCandidate:
    """A scored provider/model option evaluated during cell-level routing."""

    provider: str
    model_class: str
    model_id: str | None

    cost_score: float
    latency_score: float
    policy_score: float
    total_score: float
    confidence: float

    reason: str


@dataclass(frozen=True)
class ModelRoutingDecision:
    """Resolved routing result.  To derive from a prior decision use dataclasses.replace()."""

    selected_provider: str
    selected_model_class: str
    selected_model_id: str | None

    confidence: float
    resolved_at: EscalationLevel

    candidates: list[ModelCandidate]
    consensus_path: list[str]
    fallback_chain: list[tuple[str, str, str | None]]

    token_budget: int
    latency_budget_ms: int
    data_policy: DataClass

    routing_reason: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelExecutionTelemetry:
    """Per-call execution record.  Logged immediately; feeds weighted routing in Phase 12."""

    provider: str
    model_class: str
    model_id: str | None

    latency_ms: int
    input_tokens: int
    output_tokens: int

    schema_valid: bool
    repair_required: bool
    fallback_used: bool

    evaluation_score: float | None = None
    cost_estimate: float | None = None
    failure_type: str | None = None
