# Implementation Roadmap — LLM Proteins Architecture

Evidence-based sequencing, maturity gates, and source mapping for building out the full architecture.
Updated after Phase 4.5 implementation against the current Python/FastAPI/PostgreSQL/Next.js codebase and the LLM Proteins spec.

---

## Current Baseline (Already Done)

| What | State |
|---|---|
| Organism runtime (signal → membrane → nucleus → ribosome → protein) | ✅ Working |
| Genome with module config, execution strategies | ✅ Working |
| Cell division, genesis, growth templates | ✅ Working |
| Auth (email + Google OAuth), session management | ✅ Working |
| Calculator bone, contract gateway stub | ✅ Working |
| LLM provider adapters (Anthropic, OpenAI, Grok, Gemini) | ✅ Built |
| Signal classifier (rule-based routing) | ✅ Built |
| Frontend: organisms, cells, genome, events, memory, console | ✅ Working |
| Basic protein validation pipeline (`ProteinPipeline`) | ✅ Working |
| Memory records (organism-level only) | ✅ Working |
| `LlmProtein` — active executor model, single-use enforced | ✅ Functional |
| `AnswerProtein` — frozen transport payload with routing hint | ✅ Functional |
| `Proteasome` — deconstructs LlmProtein → deposits into CellWorkingState | ✅ Functional |
| `CellWorkingState` — async-safe named-slot cell working memory | ✅ Functional |
| `GolgiApparatus` — pluggable validator / repair / destroy pipeline | ✅ Functional |
| `Lysosome` — destroys misfolded proteins, rolls back slots, retry signal | ✅ Functional |
| `Cytoskeleton` — routes AnswerProtein to cytoplasm slot / cell / membrane | ✅ Functional |
| Phase 1 — Bone contracts, enzyme compiler, `BoneCortex`, capability graph | ✅ Functional + integrated |
| Phase 2 — `CellModelRouter`, provider registry, fallback chains, telemetry | ✅ Functional + integrated |
| `ProteinType` enum + per-type prompt templates (`Ribosome._build_prompt`) | ✅ Functional |
| Per-type validation in `ProteinPipeline.validate()` | ✅ Functional |
| `knowledge.reference.lookup` bone + default Retrieval module for `search` | ✅ Functional + integrated |
| Phase 4 — genome-declared cell execution plans, shared state, parallel/conditional/iterative coordination | ✅ Functional + integrated |
| Phase 4 organelle integration — Proteasome, Golgi, Lysosome, Cytoskeleton in the live plan path | ✅ Functional + integrated |
| Phase 4.5 — structured output, shared execution, tracing, durable runs, data policy, resilience | ✅ Functional + integrated |
| Phase 5.5 — modular runtime, skeletal effect outbox, versioned memory policy, inspector | ✅ Functional + integrated |

**What is NOT here yet:** tissue/organ memory activation, semantic/vector retrieval, live cloud resource provisioning, tissue/organ execution, cross-cell aggregation, consensus, organism-level task decomposition, distributed concurrency limits across multiple application replicas, hierarchical checkpoints/recovery modes, and strict database-enforced multi-tenancy.

> **Next phase:** Phase 6A, Tissue Runtime MVP. Phase 5.5 remains only partially
> production-hardened until its opt-in live-provider suites run in the target environment.

---

## Maturity Model

“Shipped” is too coarse for this architecture. Every phase is tracked at three distinct levels:

| Level | Meaning |
|---|---|
| **Functional** | Core behavior exists and has focused automated tests |
| **Integrated** | Behavior is connected to the live runtime/API and relevant operator surface, with regression coverage |
| **Production-hardened** | Live-provider contracts, durable storage, traceability, concurrency/failure behavior, security boundaries, and load/failure tests meet the phase exit gate |

Current maturity:

| Phase | Functional | Integrated | Production-hardened |
|---|---:|---:|---:|
| P1 — Bones | ✅ | ✅ | ⏳ |
| P2 — Model routing | ✅ | ✅ | ⏳ |
| P3 — Protein types | ✅ | ✅ | Partial |
| P4 — Intra-cell coordination | ✅ | ✅ | ⏳ |
| P4.5 — Runtime hardening | ✅ | ✅ | Partial |
| P5A — Living skeleton | ✅ | ✅ | Partial |
| P5B — Durable organism memory | ✅ | ✅ | Partial |
| P5.5 — Runtime boundary hardening | ✅ | ✅ | Partial |

Phase 4.5 closes the P3/P4 integration gaps with provider-native schemas plus canonical normalization, shared bounded execution, trace propagation, typed resilience, owner-scoped run APIs, and PostgreSQL run/step records. Production hardening remains partial until deployment-specific provider credentials, a real PostgreSQL instance, multi-replica limits, and sustained load/failure tests pass in the target environment.

---

## Effort and Forecasting

Estimates are planning ranges, not delivery promises. A phase exits only when its acceptance gate passes; elapsed time does not make incomplete work “shipped.”

| Size | Indicative solo range | Indicative 2-dev range | Character |
|---|---|---|---|
| **S** | 3–7 working days | 2–4 working days | Isolated, clear contract, minimal persistence impact |
| **M** | 2–4 weeks | 1–3 weeks | Moderate coupling, migrations or API work |
| **L** | 4–8 weeks | 3–6 weeks | Cross-layer behavior, failure testing, operator impact |
| **XL** | 8–16+ weeks | 5–10+ weeks | Fundamental runtime design, distributed state, or major operational risk |

---

## Universal Phase Exit Checklist

Every phase-specific gate extends this checklist:

- Domain model and invariants are explicit and versioned.
- Public API/event contracts and backward-compatibility behavior are documented.
- PostgreSQL migration and in-memory/PostgreSQL parity tests exist for durable state.
- Unit, integration, API, restart/reload, negative authorization, and regression tests pass as applicable.
- Deadline, cancellation, retry, idempotency, partial-result, and external-side-effect semantics are defined.
- Trace, metrics, provenance, classification, redaction, and ownership propagate through new boundaries.
- Fan-out/queue/loop/payload limits are explicit and saturation/failure tests pass.
- Minimal operator inspectability exists for the new runtime state.
- Python package build, full backend suite, TypeScript, touched-file lint, and frontend production build pass.
- Known limitations and deferred hardening are recorded; they cannot be hidden behind a “shipped” label.

---

## Phase 1 — Skeletal Capability Framework ✅ FUNCTIONAL + INTEGRATED
**Sources:** `bones-and-llm-routing.md` + §4 (Protein Types)  
**Effort:** M  
**Dependency:** None — fully isolated, can start immediately

### Design principle

Bones are not tools. Bones are structural capability contracts.

A bone defines what the organism *can do* — its input shape, output shape, constraints, and position in the capability graph. A bone never defines *how* to do it. Execution is the responsibility of **Enzymes**: reusable, compiled primitives that satisfy bone contracts at runtime.

This separation means:
- A bone contract is stable even when execution changes (formula today → table lookup tomorrow → LLM protein if inputs fall outside constraints)
- New capabilities can be expressed as bone contracts without writing execution code — the cell assembles existing enzymes dynamically
- The skeleton grows through Osteoblast promotion, not genome edits

---

### Layer 1 — Bone Contracts

Each bone is a pure capability contract stored in `BoneStructureRecord.definition` with a richer schema:

```python
BoneContract(
    bone_id="math.arithmetic.evaluate",
    capability_family="math",                    # top of capability graph
    capability_path=["math", "arithmetic", "evaluate"],
    input_schema={"expression": "string"},
    output_schema={"result": "number"},
    constraints=["expression must be a valid arithmetic expression"],
    default_enzyme="enzyme.expression_eval",     # optional default binding
)
```

Bones form a **capability graph** — a hierarchical tree of what the organism can structurally become:

```
math
├── arithmetic.evaluate
├── statistics.z_table
├── statistics.binomial
└── geometry.haversine

finance
├── loan.calculate
├── investment.compound_interest
└── investment.npv

chemistry
├── periodic_table.lookup
└── molecular_weight.calculate

computing
├── network.ip_subnet
└── encoding.base_convert

health
├── bmi.calculate
└── egfr.calculate

calendar
├── date.diff
└── date.timestamp_convert
```

The Nucleus traverses this graph to find the matching bone contract for an incoming signal. No tool names. No `if/elif`. The signal type IS the path into the graph.

**`structure_type`** on `BoneStructureRecord` gains a new value: `"capability"` (alongside existing `schema`, `adapter`, `contract`).

---

### Layer 2 — Enzymes

Enzymes are compiled execution primitives. They do not appear in the capability graph. They satisfy bone contracts when the cell requests execution.

Three enzyme kinds, in order of emergence:

**`expression`** — a safe math formula compiled from a gene definition in the genome. No Python required for new enzymes of this kind:
```yaml
enzyme_id: enzyme.expression_eval
kind: expression
expression: "{{ payload.expression }}"   # evaluates the input expression itself
output_key: result
```

**`composition`** — a named pipeline of expression steps, each consuming outputs of prior steps. Derives new enzymes from existing ones:
```yaml
enzyme_id: enzyme.finance.compound_interest
kind: composition
steps:
  - output: rate_per_period
    expression: "annual_rate / periods_per_year"
  - output: result
    expression: "principal * (1 + rate_per_period) ** (periods_per_year * years)"
output_key: result
```

**`python_ref`** — escape hatch for enzymes that cannot be expressed as formulas (lookup tables, formula parsers). Points to a pure function in `preon_systems_cell/bones/data/`:
```yaml
enzyme_id: enzyme.chemistry.periodic_table
kind: python_ref
ref: "preon_systems_cell.bones.data.periodic_table:lookup"
output_key: element_data
```

Only ~4 of the standard enzymes need `python_ref`. Everything else is `expression` or `composition`.

---

### Layer 3 — EnzymeCompiler & BoneCortex

**`EnzymeCompiler`** runs once at organism startup. For each enzyme gene definition:
- `expression` → parses and validates via AST whitelist (arithmetic ops, `math.*`; blocks attribute access, dunder calls, imports); compiles to a bound callable
- `composition` → threads step outputs as local variables; compiles the full pipeline
- `python_ref` → imports and validates the referenced function

Produces a `CompiledEnzyme` — a frozen dataclass wrapping the callable plus its input schema validator.

**`BoneCortex`** holds:
- All bone contracts (the capability graph)
- All compiled enzymes
- The bone → enzyme binding map (default bindings + any runtime overrides)

```python
class BoneCortex:
    def resolve(self, bone_id: str) -> BoneContract | None
    def execute(self, bone_id: str, payload: dict) -> dict        # uses default binding
    def can_satisfy(self, bone_id: str, payload: dict) -> bool    # schema + constraint check
    def bind(self, bone_id: str, enzyme_id: str) -> None          # runtime override
    def graph(self) -> dict                                        # full capability graph
```

The Ribosome replaces its entire `if/elif` block with:
```python
elif module.execution_strategy == ExecutionStrategy.DETERMINISTIC_TOOL:
    payload = self.bone_cortex.execute(module.deterministic_tool, signal.payload)
```

---

### Layer 4 — Capability-Skeleton Maintenance Hooks

Phase 1 introduced three lightweight maintenance roles for the capability registry. These hooks are historical precursors, not organism-owned infrastructure cells. Phase 5A makes the biological roles first-class `CellRecord` instances for structural growth while retaining these hooks for capability telemetry and binding maintenance.

**Osteoblast** (already partially exists) — creates new bone contracts and enzyme bindings:
- Proposes `BoneContract` definitions through the existing proposal API
- Proposes new enzyme gene definitions
- Promotes a successful dynamic assembly to a permanent default enzyme binding (the seed of crystallization)

**Osteocyte** (new) — monitors skeletal health:
- Tracks usage frequency per bone contract
- Detects constraint drift (payloads arriving that fall outside declared constraints)
- Reports bottlenecks (bone contracts with no satisfying enzyme → forced LLM fallback)
- Emits `RuntimeEventType.BONE` telemetry per execution

**Osteoclast** (new) — removes obsolete structure:
- Deprecates bone contracts with zero usage over a configurable window
- Removes enzyme bindings that have been superseded
- Simplifies the capability graph when derivation paths collapse

Osteocyte and Osteoclast are lightweight capability-registry helpers at this phase. Phase 5A supplies the first-class skeletal cells and structural resource lifecycle. Their events join the Phase 4.5 trace/telemetry foundation; advanced skeletal health analytics can mature with Phase 12 operations.

---

### Crystallization (future — not Phase 1)

When a cell repeatedly assembles enzymes dynamically to satisfy a bone contract and succeeds at high rate, the Osteoblast can promote that assembly to a permanent default enzyme binding — the equivalent of stress-induced bone mineralization. The organism gradually earns stronger skeletal structure through use, not through upfront design.

This is intentionally deferred. Phase 1 establishes the substrate for it. Crystallization becomes meaningful only after Phase 4 coordination, Phase 4.5 trustworthy telemetry, and enough reviewed usage history exist.

---

### Default bone contracts & enzyme bindings implemented in Phase 1

These are defined as data (YAML gene definitions), not Python tools:

| Bone ID | Enzyme kind | Note |
|---|---|---|
| `math.arithmetic.evaluate` | `expression` | replaces hardcoded calculator |
| `math.statistics.z_table` | `python_ref` | lookup table |
| `math.geometry.haversine` | `expression` | great-circle distance |
| `math.encoding.base_convert` | `expression` | base N to base M |
| `finance.loan.calculate` | `composition` | monthly payment |
| `finance.investment.compound_interest` | `composition` | FV from PV + rate + time |
| `finance.health.bmi` | `expression` | weight / height² |
| `chemistry.periodic_table.lookup` | `python_ref` | data file |
| `chemistry.molecular_weight.calculate` | `python_ref` | formula parser |
| `computing.network.ip_subnet` | `composition` | CIDR → network/broadcast/range |
| `computing.encoding.base64` | `expression` | pure transform |
| `computing.http_status.lookup` | `python_ref` | lookup table |
| `calendar.date.diff` | `expression` | signed day count |
| `calendar.date.timestamp_convert` | `expression` | epoch ↔ ISO |
| `text.encoding.morse_code` | `python_ref` | character ↔ dots/dashes |
| `text.validation.luhn_check` | `expression` | credit card checksum |

---

### New files

| File | What |
|---|---|
| `preon_systems_cell/bones/__init__.py` | Package |
| `preon_systems_cell/bones/models.py` | `BoneContract`, `EnzymeGene`, `CompiledEnzyme` Pydantic models |
| `preon_systems_cell/bones/compiler.py` | `EnzymeCompiler` with safe AST evaluator |
| `preon_systems_cell/bones/cortex.py` | `BoneCortex` — capability graph + enzyme registry + binding map |
| `preon_systems_cell/bones/defaults.yaml` | Default bone contracts and enzyme gene definitions |
| `preon_systems_cell/bones/data/periodic_table.py` | Lookup data for `python_ref` enzymes |
| `preon_systems_cell/bones/data/country_codes.py` | Same |
| `preon_systems_cell/bones/data/http_status.py` | Same |
| `preon_systems_cell/bones/data/morse_code.py` | Same |

Changes to existing files:
- `models.py` — add `BoneContract`, `EnzymeGene` models; extend `BoneStructureRecord.structure_type` to include `"capability"`
- `engine.py` — add `BoneCortex` to `OrganismRuntime`; wire into `Ribosome`; remove hardcoded `if/elif` tool dispatch; add `Osteocyte` telemetry hooks; add `Osteoclast` stub
- `bones-and-llm-routing.md` — update to reflect this design

---

### Original implementation cadence (historical)

- Week 1: `BoneContract` model, `EnzymeGene` model, `EnzymeCompiler` (all three kinds + safe AST), `BoneCortex`, `defaults.yaml` with 8 expression/composition enzymes, wire Ribosome
- Week 2: 4 `python_ref` data modules (periodic table, country codes, HTTP status, morse), remaining 8 default bones, Osteocyte telemetry stub, Osteoclast stub, integration tests

**After this phase:** the skeleton defines what the organism can become. Adding a new capability is a YAML bone contract + enzyme gene definition — no Python required for expression/composition kinds. The Ribosome never names a tool directly. The capability graph is queryable. Crystallization is possible once observability lands.

---

## Phase 2 — Model Interface Layer & Provider Routing ✅ FUNCTIONAL + INTEGRATED
**Sources:** §5 (Model Interface Layer) + LLM Protein Model Routing Architecture  
**Effort:** M  
**Dependency:** Phase 0 (LLM adapters exist)

### Design principle

Provider and model selection is not a static genome field lookup — it is a routing decision the organism makes locally at the cell level, escalating to tissue → organ → organism only when confidence, policy, or governance requires it.

```
Ribosome decides that an LLM protein should be expressed.
Model routing determines which provider/model gives that protein its execution substrate.
```

The Ribosome does not choose the model. It creates an `LlmProteinInstantiationRequest` and delegates to the routing layer. The protein is born with a provider/model identity already resolved.

At Phase 2, routing is **deterministic policy resolution**. Preliminary telemetry exists, but it is not yet trustworthy enough for weighted scoring because normalization and final validation outcomes are not connected. Phase 4.5 fixes that telemetry contract; Phase 10 may add weighted routing only after sufficient reviewed history exists.

---

### Core Objects

**`LlmProteinInstantiationRequest`** — intent object created by the Ribosome before protein instantiation. Contains only fields that are mechanically derivable from the signal, genome module, and runtime context. Fields requiring a prior LLM call to populate (`ambiguity_level`, `creativity_required`, `factuality_required`, `schema_strictness`) are intentionally excluded — if needed in future they will be set by an Evaluation protein in a cell execution plan (Phase 4).

```python
@dataclass(frozen=True)
class LlmProteinInstantiationRequest:
    signal_id: str
    task_id: str           # signal_id until Phase 8A TaskGraph exists
    module_id: str

    protein_type: ProteinType          # from GenomeModule
    capability_required: str           # from GenomeModule signal_types[0]

    reasoning_depth: ReasoningDepth    # from GenomeModule (shallow/moderate/deep)
    cost_tier: CostTier                # from GenomeModule (cheap/balanced/premium)
    data_class: DataClass              # from GenomeModule (public/internal/confidential/restricted)

    latency_budget_ms: int             # from GenomeModule or signal deadline
    token_budget: int                  # from GenomeModule
    context_size_estimate: int         # computed from signal payload byte length

    allowed_providers: list[str]       # from GenomeModule; empty = all registered
    expected_output_schema: dict[str, Any] | None = None  # from GenomeModule

    metadata: dict[str, Any] = field(default_factory=dict)
```

**`ModelRoutingDecision`** — the routing result, carrying full trace for observability:

```python
@dataclass(frozen=True)
class ModelRoutingDecision:
    selected_provider: str
    selected_model_class: str
    selected_model_id: str | None

    confidence: float
    resolved_at: Literal["cell", "tissue", "organ", "organism"]

    candidates: list[ModelCandidate]
    consensus_path: list[str]
    fallback_chain: list[tuple[str, str, str | None]]

    token_budget: int
    latency_budget_ms: int
    data_policy: str

    routing_reason: str
    metadata: dict[str, Any] = field(default_factory=dict)
```

`ModelRoutingDecision` is `frozen=True`. Routing layers that build on a prior decision use `dataclasses.replace()` — there is no `.with_updates()` method.

**`ProviderModelProfile`** — centralizes provider capability metadata, replacing fields scattered across adapter files:

```python
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
    relative_cost: float           # 0.0–1.0 relative scale

    strengths: list[str]
    weaknesses: list[str]
    allowed_data_classes: list[DataClass]
```

A `MODEL_REGISTRY: list[ProviderModelProfile]` ships with default entries for Anthropic, OpenAI, Grok, Gemini. Exact model IDs remain configurable via environment.

**`ModelExecutionTelemetry`** — logged after every provider call. Phase 4.5 connects it to real post-normalization outcomes; validated history may feed Phase 10 weighted routing:

```python
@dataclass
class ModelExecutionTelemetry:
    provider: str
    model_class: str
    model_id: str

    latency_ms: int
    input_tokens: int
    output_tokens: int

    schema_valid: bool
    repair_required: bool
    fallback_used: bool

    evaluation_score: float | None
    cost_estimate: float | None
    failure_type: str | None
```

---

### Day-One Routing Policy

`CellModelRouter` implements **deterministic policy resolution**. No weighted scoring — the system starts with one or two active providers and no validated telemetry weights:

1. If `GenomeModule` specifies an explicit provider + model override → use it directly
2. Else filter `MODEL_REGISTRY` candidates by hard constraints:
   - provider API key is present in environment
   - provider is in `allowed_providers` (or list is empty — all pass)
   - provider's `allowed_data_classes` covers `request.data_class`
   - model's `max_context_tokens` ≥ `request.context_size_estimate`
3. Among passing candidates, prefer: lowest `relative_cost` when `cost_tier=cheap`; lowest `average_latency_ms` when `latency_budget_ms` is tight; else use registry order
4. If no candidate available → walk `fallback_chain` until one succeeds or fall to `llm_stub`
5. Log `ModelExecutionTelemetry` regardless of outcome

**Not implemented yet:** multi-dimensional weighted scoring (`capability_score * 0.25 + ...`). Consider it in Phase 10 only after Phase 4.5 produces trustworthy outcome telemetry.

---

### Routing Hierarchy

```
LlmProteinInstantiationRequest
  ↓
CellModelRouter            ← Phase 2: full (Day-One deterministic policy)
  ↓ always resolves at this phase (policy is deterministic, never uncertain)
ModelRoutingDecision

TissueModelCouncil         ← Phase 6A: stub now, full implementation with tissue runtime
OrganModelPolicy           ← Phase 9: stub now, full implementation in Phase 9
OrganismRoutingAuthority   ← Phase 9: stub now, full implementation in Phase 9
```

At Phase 2, `TissueModelCouncil`, `OrganModelPolicy`, and `OrganismRoutingAuthority` are stubs that return `None`. `CellModelRouter` always resolves because Day-One policy is deterministic. Confidence thresholds and escalation rules come online with Phase 6A and Phase 9 after those layers have real runtime and telemetry contracts.

---

### Integration Points

**Ribosome** — constructs `LlmProteinInstantiationRequest`, delegates to router, instantiates protein with resolved identity:

```python
routing_request = LlmProteinInstantiationRequest(
    signal_id=signal.signal_id,
    task_id=signal.signal_id,
    module_id=module.module_id,
    protein_type=module.protein_type or "reasoning",
    capability_required=module.signal_types[0],
    reasoning_depth=module.min_reasoning_depth or "moderate",
    cost_tier=module.max_cost_tier or "balanced",
    data_class=module.data_class_allowed[0] if module.data_class_allowed else "internal",
    latency_budget_ms=module.latency_budget_ms or 5000,
    token_budget=module.token_budget or 4096,
    context_size_estimate=len(str(signal.payload)),
    allowed_providers=module.allowed_providers or [],
    expected_output_schema=module.output_schema,
)

decision = self.model_router.resolve(routing_request)

protein = LlmProtein(
    provider=decision.selected_provider,
    model_class=decision.selected_model_class,
    model_id=decision.selected_model_id,
    token_budget=decision.token_budget,
    latency_budget_ms=decision.latency_budget_ms,
    fallback_chain=decision.fallback_chain,
    routing_confidence=decision.confidence,
    routing_resolved_at=decision.resolved_at,
    routing_consensus_path=decision.consensus_path,
    routing_reason=decision.routing_reason,
    input_payload=signal.payload,
)
```

**`LlmProtein`** gains routing fields: `provider`, `model_class`, `model_id`, `token_budget`, `latency_budget_ms`, `fallback_chain`, `routing_confidence`, `routing_resolved_at`, `routing_consensus_path`, `routing_reason`. The protein does not select its own model — routing is resolved before instantiation.

**`AnswerProtein`** gains `routing_trace: dict` carrying `selected_provider`, `selected_model_id`, `routing_confidence`, `resolved_at`, `consensus_path`, and `fallback_chain`. Visible in protein payload and RuntimeEvent.

**`GenomeModule`** gains new optional fields:
- `allowed_providers: list[str]` — empty = all registered
- `min_reasoning_depth: ReasoningDepth | None`
- `max_cost_tier: CostTier | None`
- `data_class_allowed: list[DataClass]`
- `model_routing_policy: Literal["emergent_local_first", "explicit_override", "organism_required"]`
- `token_budget: int | None`
- `latency_budget_ms: int | None`
- `llm_fallback_chain: list[tuple[str, str, str | None]]` — explicit override; if absent, built from registry

---

### New Files

| File | What |
|---|---|
| `preon_systems_cell/model_routing/__init__.py` | Package |
| `preon_systems_cell/model_routing/types.py` | `LlmProteinInstantiationRequest`, `ModelRoutingDecision`, `ModelCandidate`, `ModelExecutionTelemetry`, enums |
| `preon_systems_cell/model_routing/registry.py` | `ProviderModelProfile`, `MODEL_REGISTRY` with default entries for 4 providers |
| `preon_systems_cell/model_routing/cell_router.py` | `CellModelRouter` — Day-One deterministic policy |
| `preon_systems_cell/model_routing/tissue_council.py` | `TissueModelCouncil` — stub returning `None` (Phase 6A) |
| `preon_systems_cell/model_routing/organ_policy.py` | `OrganModelPolicy` — stub returning `None` (Phase 9) |
| `preon_systems_cell/model_routing/organism_authority.py` | `OrganismRoutingAuthority` — stub returning `None` (Phase 9) |
| `preon_systems_cell/model_routing/fallback.py` | Fallback chain builder — derives chain from registry by constraint compatibility |
| `preon_systems_cell/model_routing/telemetry.py` | `ModelExecutionTelemetry` logging and future scoring hook |

Changes to existing files:
- `models.py` — add new fields to `GenomeModule`; add `routing_trace` to `AnswerProtein`; add `LlmProtein` routing fields
- `engine.py` — Ribosome delegates to `CellModelRouter`; model interface layer receives full routing decision; telemetry logged after each adapter call

---

### Deferred to Later Phases

| What | When |
|---|---|
| `TissueModelCouncil` full implementation | Phase 6A (tissue runtime) |
| `OrganModelPolicy` full implementation | Phase 9 (organ coordination) |
| `OrganismRoutingAuthority` full implementation | Phase 9 |
| Weighted multi-dimensional scoring formula | Phase 10, only after validated Phase 4.5 telemetry |
| Confidence thresholds and escalation triggers | Phase 6A/9 with the owning runtime |
| Streaming (`adapter.stream()`) | Separate provider/runtime feature with Track D surface |

---

### Original implementation cadence (historical)

- Week 1: `types.py` (all core objects + enums), `registry.py` with 4 provider profiles, `CellModelRouter` Day-One policy, stubs for Tissue/Organ/Organism routers, `fallback.py`
- Week 2: Wire Ribosome to routing layer, `GenomeModule` new fields, `ModelExecutionTelemetry` logging, `AnswerProtein` routing trace, update `LlmProtein`, integration tests

**After Phase 4.5 hardening:** every LLM call has a resolved provider/model identity before invocation, a tested fallback chain, invocation-time data policy, trace context, and post-normalization schema/repair telemetry. The routing hierarchy stubs remain in place for Phase 6A and Phase 9 to fill in.

---

## Phase 3 — 5 Protein Types ✅ FUNCTIONAL + INTEGRATED
**Sources:** §4 (Protein Architecture — §4.3)  
**Effort:** M  
**Dependency:** Phase 2

### What was built

`ProteinType` StrEnum in `models.py`, with distinct execution + validation logic per type:

| Type | Execution | Validation |
|---|---|---|
| **Reasoning** | chain-of-thought prompt | confidence ≥ `module.min_confidence` (default `DEFAULT_MIN_CONFIDENCE` = 0.5) |
| **Retrieval** | bone call (local reference corpus) | `result` non-empty, `source`/`sources` cited |
| **Transformation** | prompt injects declared schema | every `output_schema` key present and type-correct |
| **Aggregation** | prompt lists and counts inputs | all `inputs` present and non-empty, no boolean contradiction |
| **Evaluation** | prompt states criteria | `score` numeric in [0,1], `criteria` stated |

Changes landed:
- `GenomeModule.protein_type: ProteinType | None`, plus `output_schema`, `min_confidence`, `evaluation_criteria`
- `Ribosome._build_prompt(module, signal)` — one template per type; untagged modules are prompted as Reasoning
- `ProteinPipeline.validate(protein, signal, module=None)` — `module` is optional, so pre-Phase-3 genomes validate exactly as before
- `knowledge.reference.lookup` bone + `bones/data/reference.py` local corpus (every entry cites a source document)
- Default genome gains a Retrieval module for `search`; `PolicySet.allowed_signal_types` gains `search`; membrane requires a `query` field on search signals
- `SignalClassifier` reclassifies a `query` carrying an explicit `query` key to `search`

### Deliberate scope calls

**Tagging is opt-in for validation.** An untagged module is *prompted* as Reasoning but gets *no* per-type validation. Defaulting validation to Reasoning would have made every existing deterministic module subject to a confidence floor it never declared. Tag a module to opt into the stricter rules.

**Aggregation contradiction detection is boolean-only.** N sources disagreeing on a yes/no question is unambiguous; free-text divergence is not contradiction and needs a real `ConflictDetector`. That is Phase 7's job — see `ProteinPipeline._validate_protein_type`.

**Aggregation input history changed in Phase 4.** The direct single-module path still reads caller-supplied `inputs`; execution plans now map real prior step results into the aggregation payload through `input_map`.

**Phase 4.5 integration is complete.** Provider adapters request native JSON schemas, `ProteinOutputNormalizer` validates all five protein contracts, bounded repair handles recoverable wrappers, and telemetry records the real post-normalization outcome.

---

## Phase 4 — Intra-Cell Coordination ✅ FUNCTIONAL + INTEGRATED
**Sources:** §8 (Intra-Cell Communication)  
**Effort:** L  
**Dependency:** Phase 3

### What was built

Cells can now run a **sequence or parallel dependency wave of proteins** to answer one signal. Modules without a plan retain the original one-signal/one-protein behavior.

**Cell execution plan:**
```python
class CellExecutionPlan:
    plan_id: str
    steps: list[ExecutionStep]
    final_step_id: str | None
    fail_fast: bool
    max_parallelism: int

class ExecutionStep:
    step_id: str
    module_id: str
    depends_on: list[str]
    condition: str | None
    input_map: dict
    max_iterations: int
    iterate_while: str | None
```

Delivered behavior:
- Plans are validated for unique step IDs, known dependencies, a valid final step, and acyclic topology.
- The runtime additionally validates that every step references a module present in the same genome.
- `CellWorkingState` supplies the canonical `execution_context`, `shared_state_buffer`, and `result_registry` slots.
- `$signal`, `$steps`, `$shared`, `$result`, and `$iteration` references feed prior results into later step payloads.
- Dependency-ready steps run concurrently with a bounded worker pool. The Ribosome/provider interface is synchronous, so Phase 4 uses worker threads instead of pretending blocking provider calls are async.
- Conditions use a call-free AST evaluator. Function calls, imports, and arbitrary attribute access are not allowed.
- Iteration is bounded to 10 attempts per step and records whether the hard limit was reached.
- Fail-fast and independent-branch continuation modes are supported.
- Aggregation steps receive actual prior protein results through `input_map`, not caller-manufactured placeholder inputs.
- Each step reserves ATP independently; resource exhaustion is a recorded step result and blocks dependants.
- LLM proteins pass through Proteasome deconstruction, all outputs pass through Golgi, failed outputs are rolled back by Lysosome, and approved answer proteins are routed by Cytoskeleton.
- `CellExecutionRun` captures ordered step outcomes, iteration counts, final protein identity, and the final cell working-state snapshot.
- `SubmitSignalResponse.execution_run` exposes the run without breaking the existing final `protein` response.
- `cell_execution` runtime events provide plan start/completion and per-step summaries.
- Legacy genomes without `execution_plan` use the unchanged single-protein path.

### Deliberate scope calls

**Plans are genome-declared in Phase 4.** Generating new DAGs with a Reasoning protein belongs to Phase 8A (validated task decomposition). Keeping that boundary prevents Phase 4 from silently implementing half of Phase 8.

**Execution-run state is cell-local but now durable.** Phase 4.5 added PostgreSQL run/step storage and owner-scoped retrieval. Cross-activation memory promotion belongs to Phase 5B; tissue and organ memory activate only when those runtimes exist.

**Tests:** Phase 4 adds coverage for graph validation, safe conditions, input mapping, sequential and parallel execution, conditional skips, fail-fast and independent branches, executor failures, bounded iteration, resource exhaustion, real retrieval-to-aggregation flow, organelle routing/rollback, genome validation, and API response exposure.

---

## Phase 4.5 — Runtime Hardening & Integration ✅ FUNCTIONAL + INTEGRATED
**Sources:** §4 (Protein Architecture) + §5 (Model Interface) + §16–§18
**Effort:** L
**Dependency:** Phases 2–4
**Status:** COMPLETE
**Decision checkpoint:** ADR-008 through ADR-013 are accepted. Phase 4.5 implementation follows those decisions.

### Why this phase exists

Phase 4 exposed platform requirements that cannot safely wait until after tissues and organs. The runtime can coordinate multiple proteins, but live-provider output contracts, durability, trace propagation, global concurrency, and minimum security boundaries are not yet strong enough to support fan-out.

### 4.5A — Structured live-provider output

**Decision record:** [ADR-008 — Normalize Provider Output at a Canonical Protein Boundary](architecture/decisions/ADR-008-structured-provider-output-boundary.md) (Accepted)

- Add a `ProteinOutputNormalizer` between provider completion and `ProteinPipeline`.
- Prefer provider-native structured output/JSON schema where supported.
- Parse and normalize each protein type:
  - Reasoning → final answer + optional reasoning summary + confidence evidence
  - Retrieval → result + normalized source records
  - Transformation → declared output-schema fields
  - Aggregation → inputs + synthesized result + disagreement metadata
  - Evaluation → numeric score + criteria + rationale
- Add bounded repair for recoverable JSON/schema failures; never silently invent required evidence.
- Move `schema_valid`, `repair_required`, and failure telemetry after real normalization/validation.
- Add mocked adapter contract tests for every protein type and provider capability class.

### 4.5B — Execution service and concurrency boundary

**Decision record:** [ADR-009 — Use a Shared Bounded Execution Service](architecture/decisions/ADR-009-shared-execution-service.md) (Accepted)

- Offload the full synchronous organism execution from FastAPI's event loop.
- Introduce a shared execution service instead of creating an uncoordinated worker pool per request wave.
- Add global, per-organism, and per-provider concurrency limits.
- Propagate deadlines and cancellation from HTTP request → cell run → step → provider call.
- Define deterministic timeout, cancellation, and partial-result semantics.
- Add concurrent-request, cancellation, timeout, and saturation tests.

### 4.5C — Trace and telemetry foundation

**Decision record:** [ADR-010 — Propagate an Explicit Hierarchical Trace Context](architecture/decisions/ADR-010-hierarchical-trace-context.md) (Accepted)

- Add `TraceContext` now: `{request_id, organism_id, cell_run_id, step_id, protein_id, provider_call_id}`.
- Propagate it through signals, runs, runtime events, routing decisions, provider telemetry, and memory provenance.
- Connect `RuntimeTelemetryCollector` to the live runtime rather than leaving it as an unused abstraction.
- Unify execution and provider telemetry behind one sink contract.
- Never log raw confidential/restricted payloads by default.

### 4.5D — Durable cell runs and retrieval

**Decision record:** [ADR-011 — Persist Cell Runs as a Durable Execution Ledger](architecture/decisions/ADR-011-durable-execution-run-ledger.md) (Accepted)

- Persist `CellExecutionRun` and ordered `ExecutionStepResult` records in PostgreSQL.
- Preserve in-memory/PostgreSQL behavior parity.
- Add:
  - `GET /api/organisms/{id}/cell-runs`
  - `GET /api/organisms/{id}/cell-runs/{run_id}`
- Store bounded snapshots or references, not unlimited duplicate protein payloads.
- Add migrations, round-trip persistence tests, restart/reload tests, and owner-boundary API tests.

### 4.5E — Minimum security baseline

**Decision record:** [ADR-012 — Enforce Canonical Data Classification at Provider Invocation](architecture/decisions/ADR-012-data-classification-and-provider-enforcement.md) (Accepted)

- Replace free-form data-class strings with one canonical `DataClass` enum.
- Propagate classification through Signal → step payload → Protein → RuntimeEvent → MemoryRecord.
- Enforce provider/data-class compatibility immediately before model invocation.
- Add redaction policy for events, debug bundles, and execution snapshots.
- Describe current tenancy honestly as owner scoping; process-global stores are not a strict isolation boundary.

### 4.5F — Resilience foundation

**Decision record:** [ADR-013 — Use Typed Failures and Bounded Resilience Semantics](architecture/decisions/ADR-013-bounded-resilience-semantics.md) (Accepted)

- Add canonical provider/protein/cell failure classes and retryability rules.
- Retry only transient, idempotent work within explicit attempt/deadline budgets.
- Add provider circuit breakers with static safe limits and operator-visible state.
- Define fail-fast, partial-result, degraded-result, and cancellation semantics consistently.
- Record fallback/circuit/timeout decisions in the trace.
- Defer hierarchical checkpoints and recovery modes to Phase 11.

### Exit gate

- Live mocked adapters satisfy all five protein contracts.
- Full request execution does not block the FastAPI event loop.
- Global/provider concurrency and cancellation tests pass.
- Failure classification, bounded retry, and provider circuit-breaker tests pass.
- Every run/provider event carries a trace context.
- Cell runs survive PostgreSQL reload and are owner-scoped.
- Restricted data is rejected or redacted at every implemented boundary.
- Existing backend, frontend type, package, and production-build regression gates pass.

---

## Phase 5A — Living Skeleton & Resource Growth ✅ FUNCTIONAL + INTEGRATED
**Sources:** Cell Survival Requirements skeletal layer + V3 Feature 10
**Effort:** M
**Dependency:** Phase 4.5

### Design principle

The biological metaphor is authoritative. Osteoblasts, osteoclasts, and osteocytes are organism-owned cells; infrastructure records are the structural material those cells create and maintain.

Capability bones remain stable `BoneContract` interfaces satisfied by enzymes. Structural bones are desired-state infrastructure resources such as database schemas, tables, indexes, blob/object namespaces, queues, topics, service contracts, and adapters.

### Implemented minimum

- Every newly created organism contains a skeletal tissue with first-class osteoblast, osteoclast, and osteocyte `CellRecord` instances.
- Structural proposals are organism-scoped and record the skeletal cell responsible for growth or remodeling.
- Planning is deterministic and side-effect-free; the exact plan is persisted with a canonical digest.
- Approval can bind to the reviewed digest before an idempotent provider apply.
- Applied resources record provider identity, opaque provider reference, desired definition, observed state, generation, health, and cellular provenance.
- Scoped `ResourceGrant` records let ordinary cells use a resource without routing all data-plane traffic through skeletal cells.
- PostgreSQL persists structural resources, proposals, plans, and grants with in-memory parity.
- Existing unscoped proposal clients remain backward compatible.

The initial provider is deliberately in-memory. A provider label such as `postgres`, `s3`, or `azure_blob` expresses intended substrate but does not silently provision live infrastructure. Live provider adapters must implement the same plan/apply/inspect boundary and pass failure/reconciliation tests before production use.

### Exit gate

- Genesis creates exactly one cell for each skeletal role and persists their ordinary cell lifecycle.
- Growth is owned by an osteoblast; remodel/retire work is owned by an osteoclast.
- Duplicate idempotency keys cannot create duplicate resources.
- Approval of a stale or changed plan digest is rejected.
- Cross-organism proposal and grant access is rejected.
- Approved growth produces an inspectable resource and optional cell-scoped grant.
- Grant revocation is durable and auditable.
- In-memory and PostgreSQL control-plane records behave equivalently.
- Live PostgreSQL/object-store provisioning remains a documented production-hardening item.

---

## Phase 5B — Durable Organism Memory & Context Construction ✅ FUNCTIONAL + INTEGRATED
**Sources:** §15 (Memory & State Management)  
**Effort:** L  
**Dependency:** Phases 4.5 and 5A

### What to build

Before Phase 5B, the runtime persisted nearly every approved final protein as an organism-scoped `MemoryRecord`. Phase 5B replaces that behavior with explicit memory admission and context construction. Its database schema and access grant are requested through Phase 5A skeletal growth rather than assumed as process-global infrastructure.

### Implemented minimum

- Routine approved proteins are no longer automatically retained.
- Automatic admission requires an explicit candidate marker, confidence, importance, novelty, and valid source state.
- Operator creation remains an explicit admission path.
- Memory records carry episodic/semantic/procedural type, trace/run/protein provenance, classification, importance, content hash, TTL, access, supersession, and skeletal storage identity.
- The first memory operation grows an organism-owned `organism-memory` structural resource and scoped grant through Phase 5A.
- `ContextBuilder` performs deterministic keyword retrieval, owner/class filtering, lifecycle checks, stable scoring, content deduplication, and bounded selection.
- Selected memory is injected into LLM execution context; access metadata changes only for injected records.
- TTL expiration, explicit supersession, duplicate consolidation, and conservative low-value aging retain auditable records rather than deleting them.
- PostgreSQL stores and reloads the full model. The Memory inspector exposes admission, provenance, lifecycle, and access metadata.

Production hardening remains partial until a live PostgreSQL deployment passes restart/concurrency/load tests and provider-specific token estimators replace the conservative character-based approximation where necessary.

**State versus memory:**
```
protein/cell-run state → remains ephemeral in CellWorkingState
organism memory        → durable, admitted by policy, provenance-linked
tissue memory          → deferred until Phase 6B
organ memory           → deferred until Phase 9
```

**Memory model:**
- `MemoryType`: `episodic | semantic | procedural`
- `source_signal_id`, `source_run_id`, `source_protein_ids`, and `trace_context`
- `data_class`, `confidence`, `importance`, `created_at`, `last_accessed_at`
- `ttl_seconds | None`, `access_count`, `content_hash`, and version
- explicit admission status and promotion reason

**Context construction:**
- Before each protein invocation, `ContextBuilder` assembles context:
  1. Pull from cell shared state (always)
  2. Retrieve admitted organism memories by keyword relevance, type, recency, importance, and confidence
  3. Enforce owner and data-class policy
  4. Deduplicate by content/provenance
  5. Truncate with a provider-aware token budget

The first retrieval implementation is **keyword relevance**, not semantic similarity. Vector/embedding similarity is a later, separately evaluated retrieval mode.

**Memory admission and promotion:**
- Stop automatically persisting every approved protein.
- Admit only outputs that satisfy configured importance, confidence, novelty, and policy rules.
- Support explicit operator admission and deprecation.
- Preserve source provenance; never promote an output after its source is redacted or invalidated without review.

**Memory lifecycle:**
- Expire records after TTL where configured.
- Do not evict solely because `access_count == 0`; every new memory starts unused.
- Garbage collection considers age, last access, importance, duplication, supersession, and policy.
- Record access only when a memory is actually injected into context.

### Exit gate

- Memory admission prevents routine low-value protein output from becoming durable memory.
- Context construction is deterministic, token-bounded, owner-scoped, and data-class aware.
- Provenance links memory back to trace/run/protein sources.
- TTL, access tracking, deduplication, supersession, and garbage collection have persistence tests.
- Retrieval quality has a small labeled relevance test set.
- In-memory and PostgreSQL stores behave equivalently.

---

## Phase 5C — Hierarchical Memory Activation
**Sources:** §15 (Memory & State Management)
**Effort:** M per layer
**Dependency:** Phase 5B plus the owning runtime

This is not a blocking phase immediately after 5A:

- Activate tissue memory with Phase 6B, after tissue ownership and contracts exist.
- Activate organ memory with Phase 9, after organ authority and domain boundaries exist.
- Reuse the Phase 5B admission, provenance, lifecycle, and context interfaces.
- Never model ephemeral protein/cell working state as durable `MemoryRecord` rows.

---

## Phase 5.5 — Runtime Boundary Hardening ✅ FUNCTIONAL + INTEGRATED
**Dependency:** Phases 4.5, 5A, and 5B

Phase 5.5 makes the Phase 5 substrate safe to extend before tissue fan-out:

- `engine.py` is a compatibility shim over modular runtime services.
- Memory policy is immutable and versioned.
- Recalled memory is bounded, untrusted provider context.
- Structural work produces real skeletal-cell run/protein provenance.
- Approval queues an idempotent structural effect and returns `202`.
- PostgreSQL and S3-compatible adapters accept structured definitions.
- The operator console includes a Skeleton inspector.

### Exit gate

- Backend and frontend regression gates pass.
- Effect duplicate, failure, lease, and reconciliation tests pass.
- Adversarial context tests prove memory cannot mutate authority fields.
- PostgreSQL/S3 integration suites are opt-in through test endpoint variables.
  Production readiness remains partial until they run against the target.

---

## Continuous Platform Tracks

Observability, security, resilience/concurrency, and operator UX are not late sequential features. They begin in Phase 4.5 and become mandatory exit gates for every new runtime layer.

### Platform Gate A — Traceability & provenance

- New records/events carry trace context and stable ownership.
- Runtime/provider telemetry is emitted after real outcomes are known.
- Durable reconstruction is possible without exposing raw restricted payloads.
- New metrics define retry, fallback, cache, and partial-result counting semantics.

### Platform Gate B — Security & data governance

- New boundaries propagate and enforce `DataClass`.
- Owner scoping has positive and negative authorization tests.
- Logs, caches, snapshots, exports, and debug paths apply redaction/retention policy.
- New external effects have an explicit invocation-time authorization point.

### Platform Gate C — Resilience & concurrency

- New fan-out uses shared global/provider limits, deadlines, and cancellation.
- Failure classes, retryability, idempotency, and partial-result behavior are explicit.
- No unbounded queues, loops, retries, worker creation, or payload snapshots.
- Failure injection and saturation tests pass before the layer is considered integrated.

### Platform Track D — Operator experience

- Each backend phase ships the smallest useful inspectability surface with its API/event contract.
- Rich visualizations follow real data contracts; the UI does not invent unavailable state.
- TypeScript contracts, touched-file lint, and production build are part of each phase gate.

---

## Phase 6A — Tissue Runtime MVP
**Sources:** §9 (Intra-Tissue)
**Effort:** L
**Dependency:** Phases 4.5 and 5B

### What to build

Currently tissues are structural containers. Phase 6A gives one tissue a bounded runtime without also attempting inter-tissue protocols and full consensus.

**Tissue runtime (`TissueRuntime`):**
- Receives a task → distributes to N cells → waits for results → aggregates → emits one output
- Uses one explicit topology per genome config; begin with hub-and-spoke
- Propagates trace, deadline, cancellation, data class, and resource budget
- Reuses the Phase 4 execution service and shared graph primitives

**MVP aggregation strategies:**
```python
class AggregationStrategy(StrEnum):
    SIMPLE = "simple"           # concatenate/merge
    WEIGHTED = "weighted"       # by confidence score
```

**Cell roles within tissue (dynamic, not fixed):**
- `producer` — generate primary output
- `evaluator` — assess quality
- `aggregator` — merge results
- `coordinator` — manage flow

Roles are execution assignments, not permanent cell types.

### Exit gate

- One tissue can fan out to multiple cells and produce a deterministic simple/weighted result.
- Per-cell failures, timeouts, cancellation, and partial results are explicit.
- Global/provider concurrency limits hold under tissue fan-out.
- Tissue runs are durable, traced, owner-scoped, and replayable from stored inputs/results.
- PostgreSQL/in-memory parity and concurrent fan-out tests pass.

---

## Phase 6B — Inter-Tissue Contracts & Tissue Memory
**Sources:** §10 (Inter-Tissue) + §15 (Tissue Memory)
**Effort:** L
**Dependency:** Phases 5B and 6A plus a reviewed organ coordination-policy interface. A bounded interface stub is completed before Phase 6B; the full runtime arrives in Phase 9.

### What to build

- `TissueSignal` with structured input/output schemas, capability declaration, trace context, deadline, and data class.
- Request-response first; pub-sub only after a concrete event-driven use case exists.
- Tissue-to-tissue calls pass through an explicit organ coordination policy; no direct ungoverned mesh.
- Activate tissue memory by reusing Phase 5B admission, provenance, and lifecycle interfaces.
- Add contract versioning and compatibility checks.
- Add redaction and policy enforcement at the tissue boundary.

### Exit gate

- Versioned tissue contracts reject incompatible or disallowed messages.
- Cross-tissue calls remain traced, bounded, cancellable, owner-scoped, and data-class safe.
- Tissue memory cannot be read or written outside its owning tissue without an authorized promotion path.
- Failure and contract-evolution tests cover both in-memory and PostgreSQL modes.

---

## Phase 7 — Consensus & Conflict Resolution
**Sources:** §14 (Consensus & Conflict Resolution)  
**Effort:** L  
**Dependency:** Phase 6A

### What to build

**Conflict detection:**
- `ConflictDetector` runs after aggregation if multiple outputs exist
- Deterministically detects schema mismatch, incompatible categorical/boolean claims, confidence gap, missing evidence, and scope mismatch
- LLM-assisted semantic contradiction detection is advisory and must cite the claims it compares

**5 consensus modes (selectable per GenomeModule):**
```python
class ConsensusMode(StrEnum):
    MAJORITY = "majority"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    EVIDENCE_WEIGHTED = "evidence_weighted"
    HIERARCHICAL = "hierarchical"
    DELIBERATIVE = "deliberative"
```

Majority, ranked selection, evidence weighting, synthesis, and iterative refinement live here—not in the tissue transport phase.

**Severity classification → response:**
- Low: normalise locally, continue
- Medium: run evaluation pass, trigger refinement
- High: suspend output and emit an escalation record; route to an organ adjudicator only after Phase 9 exists

**Adjudication:**
- `Adjudicator` invoked for high-severity conflicts
- Scores candidates against objective criteria
- Produces single output with `adjudication_trace: list[AdjudicationStep]`

**Bounded iteration:**
- Max rounds configurable per tissue
- Timeout failsafe: if no convergence by deadline → partial output with `confidence=low`

### Exit gate

- Consensus never hides unresolved disagreement; output contains dissent/evidence metadata.
- Deterministic modes are reproducible from stored inputs.
- Deliberative mode is bounded by rounds, deadline, ATP, and provider concurrency.
- High-severity conflicts suspend unsafe final emission.
- Consensus traces are durable and replayable.
- Labeled conflict fixtures measure false-positive/false-negative behavior.

---

## Phase 8 — Organism Task Decomposition
**Sources:** §13 (Task Decomposition & Orchestration) + §6 (Concurrency)  
**Effort:** XL  
**Dependency:** Phases 4.5, 6A, 7, plus Platform Gates A–C

### What to build

Phase 4 already provides a bounded cell-local DAG scheduler. Phase 8 must extract/reuse its graph validation, dependency-state, condition, cancellation, and bounded-execution primitives rather than creating a second unrelated scheduler.

**Task graph:**
```python
class TaskNode:
    task_id: str
    parent_task_id: str | None
    owner_layer: Literal["organism","organ","tissue","cell","protein"]
    owner_id: str
    dependencies: list[str]         # task_ids that must complete first
    priority: int
    state: TaskState                # queued/ready/running/waiting/done/failed
    payload: dict

class TaskGraph:
    nodes: dict[str, TaskNode]
    def ready_nodes(self) -> list[TaskNode]   # deps satisfied
    def mark_done(self, task_id, result) -> None
    def mark_failed(self, task_id, error) -> None
```

**Decomposition strategies:**
- Functional: one sub-task per tissue/organ specialty
- Temporal: sequential phases
- Structural: follow the problem's own structure
- Granularity: recursively decompose until protein-executable

**Scheduler:**
- `TaskScheduler` is a hierarchical adapter over the shared graph executor
- `tick()` — called on each runtime cycle
- Dispatches all `ready` nodes in parallel up to concurrency limit
- Handles priority queues, domain queues, retry queues, deferred queues

### Phase 8A — Static validated decomposition

- Accept operator/genome-declared task graphs.
- Allow an LLM decomposer to propose a graph, but validate topology, owner capability, budgets, data class, and policy before activation.
- Persist graph versions and every state transition.
- Begin with functional and temporal strategies.
- Require deterministic replay from the accepted graph.

### Phase 8B — Adaptive replanning (deferred)

Adaptive graph mutation starts only after failure classification, checkpoints, traceability, and governance enforcement are active:

- When a node fails or produces surprising output, `Replanner` may:
  - Alter the graph (add/remove nodes)
  - Reroute tasks to different owners
  - Inject new validation steps
  - Terminate low-value subpaths
- Every mutation creates a new graph version with reason, actor, policy decision, and rollback reference.

### Exit gate for 8A

- Shared graph primitives power both Phase 4 and Phase 8 without semantic drift.
- Invalid/cyclic/over-budget/unauthorized proposed graphs cannot activate.
- Scheduler honors global/provider concurrency, deadline, cancellation, priority, and data policy.
- Graph and node state survive restart and can be replayed.
- Load tests cover queue fairness and fan-out limits.

### Exit gate for 8B

- Every adaptive mutation is versioned, policy-checked, traced, and reversible to a checkpoint.
- Replanning cannot expand ATP, provider, tool, or data authority.
- Failure-injection tests prove bounded recovery and no infinite mutation loops.

---

## Phase 9 — Organ Coordination & Collective Intelligence
**Sources:** §11 (Organ-Level) + §12 (Collective Intelligence)  
**Effort:** XL  
**Dependency:** Phases 5A, 6A, 7, 8A, plus Platform Gates A–C

### What to build

**Organ coordination layer:**
- `OrganCoordinator` owns a `TaskGraph` scoped to the organ's domain
- Decomposes domain objective into tissue-level tasks
- Manages: sequential phases, parallel phases, conditional branching, iterative loops
- Produces one unified organ-level output (structured result + confidence + reasoning summary)

**Hierarchical control:**
- A genome policy designates which organ roles may issue directives; “brain” is a default profile, not hard-coded authority
- Authorized coordinator organs can issue directives via `OrganDirective`
- Organs report back to the designated coordinator via `OrganReport`
- The designated organism coordinator synthesises across organs → organism decision

**Voice unification:**
- Each layer (tissue, organ, organism) produces one output even when many contributors exist
- `VoiceUnifier` at each level applies configured consensus mode → single structured output
- A unified voice must retain unresolved dissent, evidence gaps, and adjudication provenance

**Organism-level synthesis:**
- Final output assembled from organ reports
- Cross-organ conflict resolution (same mechanisms as Phase 7 but at organ scope)
- Output includes: structured result, contributing organs, confidence, decision provenance

**Organ memory activation:**
- Activate organ-scoped memory using Phase 5B interfaces only after organ ownership/domain boundaries exist.
- Promotion to organism memory requires explicit policy and provenance.

### Exit gate

- Organ authority is genome-configured, validated, and policy-bounded.
- Organ directives cannot expand task/data/provider authority.
- Cross-organ conflict remains visible in the final provenance report.
- Organ task state, decisions, and memory survive restart.
- Directive loops are deadline/ATP/iteration bounded and failure-tested.

---

## Phase 10 — Advanced Concurrency & Network Optimisation
**Sources:** §6 (Concurrency) + §7 (Network Efficiency)  
**Effort:** L–XL by optimization
**Dependency:** Phase 4.5 concurrency/telemetry foundation plus measured demand from Phases 6–9

### What to build

Basic global/provider limits, deadlines, cancellation, and event-loop safety ship in Phase 4.5. Phase 10 contains optimizations justified by production telemetry—not prerequisites deferred until after organs.

**Backpressure propagation:**
- Each layer exposes a `pressure: float` signal (0.0 = relaxed, 1.0 = saturated)
- Upstream dispatchers throttle when downstream pressure exceeds threshold
- Implemented as async feedback channel between layers

**Provider-aware throttling:**
- Track per-provider: request rate, token rate, error rate, latency p95
- `ProviderHealthMonitor` adjusts concurrency limits dynamically
- High latency → reduce parallel calls; shift simple tasks only when a configured, policy-approved local runtime exists, otherwise throttle or use an allowed fallback

**Caching:**
- `ResultCache`: hash(prompt + model + constraints) → cached response (TTL configurable)
- `TemplateCache`: shared prompt fragments stored once, referenced by ID
- `RetrievalCache`: bone call results (periodic table, country codes, etc.) cached indefinitely

**Request deduplication:**
- Before dispatch, check if identical in-flight request exists → subscribe to its result
- Eliminates duplicate LLM calls in fan-out scenarios

**Batching:**
- `BatchCollector` groups compatible tasks within a 50ms dispatch window
- Compatible = same model, same prompt template, different data payloads
- Use only where a provider exposes a real batch API or where offline batching preserves per-task validation
- Do not concatenate unrelated prompts into one request and call it provider batching
- Local SLLM offloading remains optional until a supported local runtime and security model exist

### Exit gate per optimization

- A benchmark demonstrates a material latency/cost/throughput improvement without >10% regression in output quality or reliability.
- Cache keys include model/version, prompt/template version, policy, data class, and relevant context.
- Restricted data never enters a cache with broader visibility or retention.
- Deduplication preserves caller cancellation and authorization independently.
- Adaptive throttling is driven by validated telemetry and has safe static limits.
- Every optimization can be disabled independently.

---

## Phase 11 — Advanced Hierarchical Resilience
**Sources:** §16 (Failure Handling & Resilience)  
**Effort:** L  
**Dependency:** Platform Gate C plus Phases 6A, 7, and 8A

### What to build

Provider timeout/retry classification, cancellation, circuit breakers, and bounded step failure are foundation work and must pass before Phase 6A. Phase 11 extends that substrate across tissue/organ/organism state.

**Failure classification:**
- `FailureClassifier` tags every error: execution / dependency / coordination / state / network / policy
- Determines: scope (protein/cell/tissue/organ/organism) and severity (low/medium/high)

**N-tier fallback paths:**
- Horizontal: try equivalent provider or tissue
- Vertical: step down model class
- Structural: use alternative DAG subgraph
- Partial: emit incomplete result with `status=degraded`

**Resilience modes:**
```python
class ResilienceMode(StrEnum):
    NORMAL = "normal"
    DEGRADED = "degraded"        # some providers/tissues impaired
    RECOVERY = "recovery"        # clearing backlog, replaying checkpoints
    CONTAINMENT = "containment"  # fault isolated, reduce interaction
```

**Checkpointing:**
- At tissue synthesis boundaries + organ decision milestones: snapshot `CheckpointRecord`
- On failure: restore from most recent checkpoint → replay only failed segment
- `CheckpointRecord` stores: task graph state, all intermediate protein results, active memory

**Failure budgets:**
- Per-layer configurable: tolerated retry rate, acceptable partial-output rate, max latency inflation
- If budget exceeded → auto-escalate resilience mode

### Exit gate

- Failure classes and severity are consistent across provider, protein, cell, tissue, and task-graph layers.
- Checkpoints are bounded, durable, encrypted/classified appropriately, and restore deterministically.
- Recovery never expands authority or repeats acknowledged external side effects.
- Circuit breakers and resilience modes have transition hysteresis and operator override.
- Failure-injection tests cover provider loss, partial tissue loss, corrupt checkpoint, restart during recovery, and policy failure.

---

## Phase 12 — Advanced Observability, Provenance & Operations
**Sources:** §17 (Observability & Telemetry)  
**Effort:** L  
**Dependency:** Phase 4.5 trace foundation plus the layers being observed

### What to build

Trace context and connected telemetry are prerequisites in Phase 4.5. Every later phase must extend them as part of its own exit gate. Phase 12 adds advanced cross-layer operations; it is not the first point where the system becomes observable.

**Hierarchical trace IDs:**
- Extend the Phase 4.5 `TraceContext` with organ/tissue/task spans as those layers land
- Inject into every adapter call, tissue message, organ directive, checkpoint, and memory provenance record

**Structured event model:**
- Typed events beyond current generic RuntimeEvent:
  `TaskQueued, TaskActivated, ModelSelected, OutputNormalised, ConsensusFailed, FallbackTriggered, CheckpointRestored, PolicyViolationBlocked`
- Each event links to trace context

**Multi-layer metrics:**
- `MetricsCollector` aggregates: latency by layer, token usage by provider, success/failure rates, consensus convergence rate, queue depths
- Exposed via `/api/metrics` endpoint + WebSocket push to frontend

**Replayability:**
- Given an `organism_request_id`, reconstruct full execution: trace, all proteins, routing decisions, consensus outcomes
- API: `GET /api/traces/{request_id}/replay`

**Decision provenance:**
- Every organism-level output includes `ProvenanceReport`: contributing organs, evidence sources, consensus paths, policy checks, confidence

### Exit gate

- Trace completeness is measured; orphaned spans/events are detectable.
- Metrics derive from reviewed event contracts and do not double-count retries/cache hits.
- Replay distinguishes deterministic re-execution from historical reconstruction.
- Provenance reports preserve evidence, dissent, policy decisions, model identity, and transformations.
- Operational dashboards expose saturation, queue depth, error budget, and degraded mode without raw sensitive payloads.

---

## Phase 13 — Advanced Security & Governance
**Sources:** §18 (Security & Governance)  
**Effort:** M  
**Dependency:** Phase 4.5 security/trace foundation plus the layers being governed

### What to build

**Data classification:**
- Extend the canonical Phase 4.5 `DataClass`: `public | internal | confidential | restricted`
- Tagged on: signals, step payloads, memories, protein outputs, events, caches, checkpoints, and exports
- Drives: which provider can process it, how it's logged, who can see it

**Policy enforcement points (6 lifecycle stages):**
1. Before task execution
2. Before model invocation (prompt validation + provider allowlist)
3. After output generation (content filter, schema check)
4. Before inter-tissue communication (redact restricted fields)
5. Before inter-organ communication
6. Before final organism output

**Provider allowlist:**
- `OrganismRecord.allowed_providers: list[str]`
- Enforce provider/data-class policy immediately before provider invocation, after actual routing is known
- The membrane may reject obviously disallowed requests, but cannot replace the invocation-time enforcement point
- Sensitive signals may use a configured, policy-approved local model runtime; otherwise reject rather than silently reroute

**Full audit log:**
- `AuditRecord`: who, what component, what data touched, what decision made, what policy checked, outcome
- Separate append-only store from RuntimeEvents
- API: `GET /api/audit` (restricted to admin roles)

**Multi-tenant isolation:**
- Current state is owner scoping, not strict multi-tenant isolation
- Add strict repository/query partitioning, owner-scoped execution contexts and caches, negative authorization tests, and database-level controls where practical
- Evaluate PostgreSQL row-level security before claiming a database-enforced tenant boundary
- Never use process-global in-memory dictionaries as a security boundary

### Exit gate

- All external/model/tool calls have invocation-time authorization and data-class enforcement.
- Audit records are append-only, owner/admin scoped, trace-linked, redacted, and retention-controlled.
- Negative cross-tenant tests cover every repository and API family.
- Debug/export/cache/checkpoint paths cannot bypass normal classification policy.
- Threat model and incident-response procedures are reviewed before production-hardening is claimed.

---

## Phase 14 — Frontend Visualization (Parallel Track)
**Sources:** §17 (Dashboards) + §19 (Example Flows as UX inspiration)  
**Effort:** S–L per surface (runs continuously with backend phases)
**Dependency:** Data from each backend phase as it lands

Phase 14 is the detailed form of Platform Track D. Each runtime phase ships a minimal inspectability surface; richer operator workflows follow stable durable APIs.

| Surface | Depends on | Status / scope |
|---|---|---|
| **Cell coordination summary** | Phase 4 | ✅ Initial execution-run stage shipped in the pipeline trace |
| **Cell-run browser/deep-dive** | Phase 4.5 | Durable run list/detail, step inputs/results, iterations, failure and organelle path |
| **Trace deep-dive** | Phase 4.5 foundation; extended per layer | Protein→cell→tissue→organ→organism trace tree |
| **Token & cost dashboard** | Phase 4.5 real usage telemetry + Phase 12 operations | Tokens/cost by provider, model, layer, objective, retry/cache outcome |
| **Skeleton inspector** | Phase 5A | Skeletal cells, desired/observed resources, plan digest, health, grants |
| **Memory inspector** | Phase 5B | Admission reason, provenance, relevance, access, TTL, supersession |
| **Tissue aggregation view** | Phases 6A and 7 | Cell outputs, aggregation, dissent, evidence, consensus path |
| **DAG visualizer** | Phase 8A | Accepted graph/version, dependency state, queues, budgets |
| **Organ health dashboard** | Phase 9 | Organ authority, active tasks, output confidence, memory/health |
| **Resilience / failure view** | Platform Gate C + Phase 11 | Fallbacks, circuit breakers, degraded modes, checkpoints |
| **Governance audit log** | Platform Gate B + Phase 13 | Classification, enforcement, redaction, access decisions |

### Frontend exit gate per surface

- Uses durable documented API/event contracts.
- Represents partial, failed, redacted, unavailable, and loading states honestly.
- Does not display raw restricted payloads without an authorized endpoint.
- TypeScript, touched-file lint, accessibility checks, and production build pass.

---

## Phase 15 — Future Extensions
**Sources:** §21 (Future Extensions)  
**Effort:** Research / TBD  
**Dependency:** All prior phases

| Extension | Min viable version | Full version |
|---|---|---|
| **Multimodal proteins** | Accept image URLs in payload → pass to vision LLM | Cross-modal synthesis proteins |
| **Self-healing systems** | Alert on degraded tissue → human intervention | Auto-replace + rebalance without human |
| **Learning & self-optimisation** | Log which routing choices worked → tune weights | Full RL loop on routing policy |
| **Autonomous goal formation** | Organism proposes sub-goals based on prior history | Full autonomous objective setting |
| **Marketplace of components** | Import tissue/organ config from JSON URL | Versioned component registry |
| **Real-time continuous systems** | WebSocket streaming of organism state | Always-on organism with event subscriptions |

---

## Full Roadmap Summary

```
FUNCTIONAL / INTEGRATED                    NEXT                         LATER
│ P1 · P2 · P3 · P4 · P4.5 · P5A · P5B    │                            │
├─P6A Tissue runtime MVP ────────────────────────────────┤              │
├─P7 Consensus ──────────────────────────────────────────┤              │
├─P8A Static task decomposition ───────────────────────────────────┤    │
├─P6B Inter-tissue contracts ──────────────────────────────────────┤    │
├─P9 Organ coordination ────────────────────────────────────────────────┤
├─P8B Adaptive replanning ──────────────────────────────────────────────┤
├─P10 Advanced optimization ────────────────────────────────────────────┤
├─P11 Advanced resilience ──────────────────────────────────────────────┤
├─P12 Advanced operations/provenance ───────────────────────────────────┤
├─P13 Advanced governance ──────────────────────────────────────────────┤
└─P14 + Platform Tracks A–D run continuously as each layer lands
```

| Phase/track | Scope | Dependency | Exit emphasis |
|---|---|---|---|
| P1–P4 | Existing functional capabilities | — | Hardened through P4.5/platform gates |
| **P4.5** | Structured live outputs, execution service, tracing, durable runs, baseline security | P2–P4 | Complete; production deployment validation remains |
| **P5A** | First-class skeletal cells, governed structural resources, scoped grants | P4.5 | Complete at control-plane level; live providers remain |
| **P5B** | Admitted durable organism memory + context builder | P5A | Complete; live-load hardening remains |
| **P5C** | Tissue/organ memory activation | Owning runtime | Reuse P5B; no premature scopes |
| **P6A** | Tissue runtime with simple/weighted aggregation | P4.5, P5B | Bounded traced fan-out |
| **P6B** | Inter-tissue contracts + tissue memory | P6A, P5B, reviewed organ coordination-policy interface | Versioned governed boundaries |
| **P7** | Conflict detection, consensus, refinement | P6A | Dissent/evidence preserved |
| **P8A** | Static validated organism task graphs | P4.5, P6A, P7, Gates A–C | Shared scheduler, durable/replayable state |
| **P8B** | Adaptive replanning | Checkpoints + governance foundation | Versioned bounded graph mutation |
| **P9** | Organ coordination + organ memory | P5B, P6A, P7, P8A, Gates A–C | Policy-configured authority and provenance |
| **P10** | Measured concurrency/network optimization | P4.5 telemetry + demonstrated need | Benchmark-backed optional optimizations |
| **P11** | Hierarchical resilience/checkpoint recovery | Gate C + P6A/P7/P8A | Failure-injection proof |
| **P12** | Advanced cross-layer operations/provenance | Gate A + implemented layers | Trace completeness and correct metrics |
| **P13** | Advanced governance/audit/isolation | Gate B + implemented layers | Threat-model and negative-auth proof |
| **P14 / Track D** | Operator UX | Each backend contract | Honest, secure inspectability |
| **P15** | Research extensions | Production-hardened foundations | Separate evidence and safety review |

### Forecast policy

- Do not publish a single “months to production” number for this research architecture.
- Estimate only the next one or two phases after their design/acceptance contracts are reviewed.
- Track forecast range, confidence, unknowns, and actual elapsed effort.
- Re-estimate after each phase because tissue/task/organ discoveries will change downstream scope.
- A demo milestone and a production-hardening milestone are separate forecasts.

---

## What Gives the Most Value Soonest

The next value sequence is:

1. **P6A** — create the first bounded collective result from multiple cells.
2. **P7 deterministic modes** — preserve and resolve disagreement without hiding dissent.
3. **P8A** — accept and execute validated organism-level task graphs.

Phase 4.5 is complete; do not weaken its normalization, execution, telemetry, durability, resilience, or security gates when adding fan-out.
