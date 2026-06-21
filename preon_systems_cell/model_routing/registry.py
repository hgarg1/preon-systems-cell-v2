"""Provider capability registry.

MODEL_REGISTRY is the single source of truth for what each provider/model can do.
The CellModelRouter reads this to score candidates against a routing request.

Model IDs listed here match those in llm_providers._MODEL_MAP.  Exact IDs can be
overridden at invocation time via GenomeModule.llm_model_id.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from preon_systems_cell.model_routing.types import DataClass


@dataclass(frozen=True)
class ProviderModelProfile:
    provider: str
    model_class: str
    model_id: str

    max_context_tokens: int
    supports_json_schema: bool
    supports_tools: bool
    supports_vision: bool
    supports_streaming: bool

    average_latency_ms: int
    relative_cost: float       # 0.0 (cheapest) to 1.0 (most expensive) — relative scale

    strengths: list[str]
    weaknesses: list[str]
    allowed_data_classes: list[DataClass]


MODEL_REGISTRY: list[ProviderModelProfile] = [
    # ── Anthropic ────────────────────────────────────────────────────────────
    ProviderModelProfile(
        provider="anthropic", model_class="fast", model_id="claude-haiku-4-5-20251001",
        max_context_tokens=200_000,
        supports_json_schema=True, supports_tools=True, supports_vision=True, supports_streaming=True,
        average_latency_ms=600, relative_cost=0.1,
        strengths=["speed", "summarization", "classification"],
        weaknesses=["deep_reasoning"],
        allowed_data_classes=["public", "internal", "confidential"],
    ),
    ProviderModelProfile(
        provider="anthropic", model_class="standard", model_id="claude-sonnet-4-6",
        max_context_tokens=200_000,
        supports_json_schema=True, supports_tools=True, supports_vision=True, supports_streaming=True,
        average_latency_ms=1800, relative_cost=0.6,
        strengths=["reasoning", "writing", "instruction_following"],
        weaknesses=["strict_tooling_variance"],
        allowed_data_classes=["public", "internal", "confidential"],
    ),
    ProviderModelProfile(
        provider="anthropic", model_class="reasoning", model_id="claude-opus-4-8",
        max_context_tokens=200_000,
        supports_json_schema=True, supports_tools=True, supports_vision=True, supports_streaming=True,
        average_latency_ms=4000, relative_cost=0.95,
        strengths=["deep_reasoning", "complex_analysis", "long_context"],
        weaknesses=["latency", "cost"],
        allowed_data_classes=["public", "internal", "confidential"],
    ),
    # ── OpenAI ───────────────────────────────────────────────────────────────
    ProviderModelProfile(
        provider="openai", model_class="fast", model_id="gpt-4o-mini",
        max_context_tokens=128_000,
        supports_json_schema=True, supports_tools=True, supports_vision=True, supports_streaming=True,
        average_latency_ms=500, relative_cost=0.05,
        strengths=["speed", "cost_efficiency"],
        weaknesses=["reasoning_depth"],
        allowed_data_classes=["public", "internal", "confidential"],
    ),
    ProviderModelProfile(
        provider="openai", model_class="standard", model_id="gpt-4o",
        max_context_tokens=128_000,
        supports_json_schema=True, supports_tools=True, supports_vision=True, supports_streaming=True,
        average_latency_ms=1500, relative_cost=0.55,
        strengths=["structured_outputs", "tool_use", "coding"],
        weaknesses=["cost_at_scale"],
        allowed_data_classes=["public", "internal", "confidential"],
    ),
    ProviderModelProfile(
        provider="openai", model_class="reasoning", model_id="o3",
        max_context_tokens=128_000,
        supports_json_schema=True, supports_tools=True, supports_vision=True, supports_streaming=True,
        average_latency_ms=2500, relative_cost=0.8,
        strengths=["reasoning", "coding", "structured_outputs"],
        weaknesses=["higher_cost"],
        allowed_data_classes=["public", "internal", "confidential", "restricted"],
    ),
    # ── Grok (xAI via OpenAI-compatible REST) ────────────────────────────────
    ProviderModelProfile(
        provider="grok", model_class="fast", model_id="grok-3-mini-fast",
        max_context_tokens=131_072,
        supports_json_schema=True, supports_tools=True, supports_vision=False, supports_streaming=True,
        average_latency_ms=700, relative_cost=0.15,
        strengths=["speed", "instruction_following"],
        weaknesses=["vision", "confidential_data"],
        allowed_data_classes=["public", "internal"],
    ),
    ProviderModelProfile(
        provider="grok", model_class="standard", model_id="grok-3",
        max_context_tokens=131_072,
        supports_json_schema=True, supports_tools=True, supports_vision=False, supports_streaming=True,
        average_latency_ms=2000, relative_cost=0.5,
        strengths=["real_time_knowledge", "coding"],
        weaknesses=["vision", "confidential_data"],
        allowed_data_classes=["public", "internal"],
    ),
    # ── Gemini ───────────────────────────────────────────────────────────────
    ProviderModelProfile(
        provider="gemini", model_class="fast", model_id="gemini-2.0-flash",
        max_context_tokens=1_000_000,
        supports_json_schema=True, supports_tools=True, supports_vision=True, supports_streaming=True,
        average_latency_ms=800, relative_cost=0.1,
        strengths=["long_context", "multimodal", "speed"],
        weaknesses=["strict_instruction_following"],
        allowed_data_classes=["public", "internal"],
    ),
    ProviderModelProfile(
        provider="gemini", model_class="standard", model_id="gemini-2.5-pro",
        max_context_tokens=1_000_000,
        supports_json_schema=True, supports_tools=True, supports_vision=True, supports_streaming=True,
        average_latency_ms=3000, relative_cost=0.7,
        strengths=["long_context", "reasoning", "multimodal"],
        weaknesses=["latency"],
        allowed_data_classes=["public", "internal"],
    ),
]
