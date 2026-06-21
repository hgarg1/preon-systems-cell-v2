# Implementation Roadmap — LLM Proteins Architecture

Honest effort, cadence, and source mapping for building out the full architecture.  
Based on gap analysis against current codebase (~20-25% complete) and the LLM Proteins spec.

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
| `LlmProtein` — active executor model, single-use enforced | ✅ Just built |
| `AnswerProtein` — frozen transport payload with routing hint | ✅ Just built |
| `Proteasome` — deconstructs LlmProtein → deposits into CellWorkingState | ✅ Just built |
| `CellWorkingState` — async-safe named-slot cell working memory | ✅ Just built |
| `GolgiApparatus` — pluggable validator / repair / destroy pipeline | ✅ Just built |
| `Lysosome` — destroys misfolded proteins, rolls back slots, retry signal | ✅ Just built |
| `Cytoskeleton` — routes AnswerProtein to cytoplasm slot / cell / membrane | ✅ Just built |

**What is NOT here yet:** wiring organelles into `submit_signal` flow, multi-protein cell coordination, tissue/organ execution, aggregation, consensus, DAG scheduling, layered memory, distributed tracing, resilience modes, most bones.

> **Note on Phase 4:** `CellWorkingState` is the "Shared state buffer" / `CellRunContext` described in Phase 4. The slot names `shared_state_buffer`, `result_registry`, and `execution_context` are already the canonical keys. Phase 4 still needs to wire these into the execution plan DAG.

---

## Effort Key

| Size | Time (solo) | Time (2-dev) | Character |
|---|---|---|---|
| **S** | 3–5 days | 2–3 days | Isolated, clear spec |
| **M** | 1–2 weeks | 4–7 days | Some design decisions, moderate coupling |
| **L** | 3–4 weeks | 2 weeks | Architectural impact, multiple files |
| **XL** | 6–10 weeks | 3–5 weeks | Fundamental system design, high coupling |

---

## Phase 1 — Skeletal Capability Framework
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

### Layer 4 — Bone Cell Lifecycle

Three bone cell roles, each with a concrete responsibility:

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

Osteocyte and Osteoclast are lightweight at this phase — stubbed monitoring hooks that emit events, with full logic deferred to Phase 12 (Observability).

---

### Crystallization (future — not Phase 1)

When a cell repeatedly assembles enzymes dynamically to satisfy a bone contract and succeeds at high rate, the Osteoblast can promote that assembly to a permanent default enzyme binding — the equivalent of stress-induced bone mineralization. The organism gradually earns stronger skeletal structure through use, not through upfront design.

This is intentionally deferred. Phase 1 establishes the substrate for it. Crystallization becomes meaningful once Phase 4 (intra-cell coordination) and Phase 12 (observability) are in place.

---

### Default bone contracts & enzyme bindings shipped in Phase 1

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

### Cadence

- Week 1: `BoneContract` model, `EnzymeGene` model, `EnzymeCompiler` (all three kinds + safe AST), `BoneCortex`, `defaults.yaml` with 8 expression/composition enzymes, wire Ribosome
- Week 2: 4 `python_ref` data modules (periodic table, country codes, HTTP status, morse), remaining 8 default bones, Osteocyte telemetry stub, Osteoclast stub, integration tests

**After this phase:** the skeleton defines what the organism can become. Adding a new capability is a YAML bone contract + enzyme gene definition — no Python required for expression/composition kinds. The Ribosome never names a tool directly. The capability graph is queryable. Crystallization is possible once observability lands.

---

## Phase 2 — Model Interface Layer & Provider Routing
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

At Phase 2, routing is **deterministic policy resolution** — no weighted scoring, no historical telemetry (none exists yet). The weighted scoring formula is deferred to Phase 12 once execution telemetry accumulates and weights can be validated.

---

### Core Objects

**`LlmProteinInstantiationRequest`** — intent object created by the Ribosome before protein instantiation. Contains only fields that are mechanically derivable from the signal, genome module, and runtime context. Fields requiring a prior LLM call to populate (`ambiguity_level`, `creativity_required`, `factuality_required`, `schema_strictness`) are intentionally excluded — if needed in future they will be set by an Evaluation protein in a cell execution plan (Phase 4).

```python
@dataclass(frozen=True)
class LlmProteinInstantiationRequest:
    signal_id: str
    task_id: str           # signal_id until Phase 8 TaskGraph exists
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

**`ModelExecutionTelemetry`** — logged after every provider call. Feeds future weighted routing (Phase 12):

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

**Not implemented yet:** multi-dimensional weighted scoring (`capability_score * 0.25 + ...`). Deferred to Phase 12 when telemetry history exists to validate weights.

---

### Routing Hierarchy

```
LlmProteinInstantiationRequest
  ↓
CellModelRouter            ← Phase 2: full (Day-One deterministic policy)
  ↓ always resolves at this phase (policy is deterministic, never uncertain)
ModelRoutingDecision

TissueModelCouncil         ← Phase 6: stub now, full implementation in Phase 6
OrganModelPolicy           ← Phase 9: stub now, full implementation in Phase 9
OrganismRoutingAuthority   ← Phase 9: stub now, full implementation in Phase 9
```

At Phase 2, `TissueModelCouncil`, `OrganModelPolicy`, and `OrganismRoutingAuthority` are stubs that return `None`. `CellModelRouter` always resolves because Day-One policy is deterministic. Confidence thresholds and escalation rules come online in Phases 6 and 9 when those biological layers have runtime implementations.

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
| `preon_systems_cell/model_routing/tissue_council.py` | `TissueModelCouncil` — stub returning `None` (Phase 6) |
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
| `TissueModelCouncil` full implementation | Phase 6 (tissue runtime) |
| `OrganModelPolicy` full implementation | Phase 9 (organ coordination) |
| `OrganismRoutingAuthority` full implementation | Phase 9 |
| Weighted multi-dimensional scoring formula | Phase 12 (needs telemetry history to validate weights) |
| Confidence thresholds and escalation triggers | Phase 12 |
| Streaming (`adapter.stream()`) | Phase 14 (frontend surfaces) |

---

### Cadence

- Week 1: `types.py` (all core objects + enums), `registry.py` with 4 provider profiles, `CellModelRouter` Day-One policy, stubs for Tissue/Organ/Organism routers, `fallback.py`
- Week 2: Wire Ribosome to routing layer, `GenomeModule` new fields, `ModelExecutionTelemetry` logging, `AnswerProtein` routing trace, update `LlmProtein`, integration tests

**After this phase:** every LLM call has a resolved provider/model identity before invocation, a full routing trace in the protein, a tested fallback chain, and execution telemetry being logged. The routing hierarchy stubs are in place for Phase 6 and Phase 9 to fill in.

---

## Phase 3 — 5 Protein Types
**Sources:** §4 (Protein Architecture — §4.3)  
**Effort:** M  
**Dependency:** Phase 2

### What to build

Add `protein_type` to `GenomeModule` and create distinct execution + validation logic per type:

| Type | Execution | Validation |
|---|---|---|
| **Reasoning** | LLM call with chain-of-thought prompt | structured output, confidence >= threshold |
| **Retrieval** | bone call (web search, DB, file) | result non-empty, source cited |
| **Transformation** | LLM or bone for data reshaping | output schema matches declared output_schema |
| **Aggregation** | combine N input proteins → one result | all inputs present, no contradictions |
| **Evaluation** | score/rank another protein's output | score in [0,1], criteria stated |

Changes:
- `GenomeModule.protein_type: ProteinType | None` (optional — defaults to Reasoning)
- `Ribosome._build_prompt(module, signal)` — type-specific prompt templates
- `ProteinPipeline.validate()` — type-specific validation rules
- Default genome adds Retrieval module for `search` signal type

**Cadence:**
- Week 1: Reasoning + Retrieval (most common)
- Week 2: Transformation + Aggregation + Evaluation

---

## Phase 4 — Intra-Cell Coordination
**Sources:** §8 (Intra-Cell Communication)  
**Effort:** L  
**Dependency:** Phase 3

### What to build

Currently: one signal → one module → one protein. This phase makes a cell able to run a **sequence or parallel set of proteins** to answer one signal.

**Cell execution plan:**
```python
class CellExecutionPlan:
    steps: list[ExecutionStep]  # ordered or parallel groups

class ExecutionStep:
    module_id: str
    depends_on: list[str]       # previous step IDs
    condition: str | None       # e.g. "step_a.confidence > 0.7"
    input_map: dict             # how to build payload from prior results
```

**Shared state buffer:**
- `CellRunContext` — lives for the duration of a cell's response to one signal
- Holds: `inputs: dict`, `step_results: dict[step_id, Protein]`, `shared_state: dict`

**Synchronisation patterns:**
- Sequential: steps run one after another, each receives prior results
- Parallel: steps with no `depends_on` run concurrently (asyncio gather)
- Conditional: step skipped if condition evaluates false on prior results
- Iterative: step can re-enqueue itself with updated payload up to N times

**Key design decision:** the execution plan for a cell is defined in the genome module or generated at runtime by a Reasoning protein that decomposes the task.

**Cadence:**
- Week 1: CellRunContext, shared state buffer, sequential execution
- Week 2: Parallel execution (asyncio), conditional branching
- Week 3: Iterative loops, integration with existing nucleus/ribosome

---

## Phase 5 — Layered Memory Architecture
**Sources:** §15 (Memory & State Management)  
**Effort:** L  
**Dependency:** Phase 4

### What to build

Currently: one `MemoryRecord` type stored at organism scope. This phase adds a proper 5-layer hierarchy.

**New memory scopes:**
```
protein  → ephemeral, discarded after protein terminates
cell     → lives for duration of CellRunContext, then promoted or discarded
tissue   → persists across cell executions within a tissue
organ    → domain-specific, persists across organism activations
organism → global long-term, persists forever (current implementation)
```

**Memory types to tag each record:**
`short_term | long_term | episodic | semantic | procedural`

**Context construction:**
- Before each protein invocation, `ContextBuilder` assembles context:
  1. Pull from cell shared state (always)
  2. Pull from tissue memory (if `memory_scope=tissue`)
  3. Pull from organ memory (if relevant to domain)
  4. Pull from organism memory (if relevant to objective)
  5. Filter by semantic similarity (simple keyword match in v1; vector search in v2)
  6. Truncate to token budget

**Memory lifecycle:**
- `ttl_seconds: int | None` — auto-expire after TTL
- `access_count: int` — track reuse frequency
- Garbage collection job: evict expired + zero-access memories

**Cadence:**
- Week 1: Memory scope enum, context builder v1 (keyword filter + TTL)
- Week 2: Cell/tissue/organ memory promotion logic
- Week 3: Lifecycle management, context injection into ribosome

---

## Phase 6 — Tissue Aggregation & Inter-Tissue Communication
**Sources:** §9 (Intra-Tissue) + §10 (Inter-Tissue)  
**Effort:** XL  
**Dependency:** Phase 4 (intra-cell must work first)

### What to build

Currently tissues are structural containers. This phase gives them a runtime.

**Tissue runtime (`TissueRuntime`):**
- Receives a task → distributes to N cells → waits for results → aggregates → emits one output
- Owns the topology (hub-and-spoke, mesh, or hierarchical) per genome config

**5 aggregation strategies (on `TissueRecord`):**
```python
class AggregationStrategy(StrEnum):
    SIMPLE = "simple"           # concatenate/merge
    WEIGHTED = "weighted"       # by confidence score
    MAJORITY = "majority"       # most common result
    RANKED = "ranked"           # sort by score, pick top-k
    SYNTHESIS = "synthesis"     # send all results to LLM → synthesise
```

**Iterative refinement loop:**
- Tissue emits draft → evaluation cells score it → if score < threshold → re-invoke producer cells with critique → max N rounds

**Cell roles within tissue (dynamic, not fixed):**
- `producer` — generate primary output
- `evaluator` — assess quality
- `aggregator` — merge results
- `coordinator` — manage flow

**Inter-tissue communication:**
- Tissues communicate via `TissueSignal` (structured, typed)
- Each tissue exposes: input schema, output schema, capability declaration
- Request-response and pub-sub patterns
- Tissue-to-tissue calls go through the organ's coordination layer

**Cadence:**
- Week 1–2: TissueRuntime, simple + weighted aggregation
- Week 3: Majority voting, ranked selection
- Week 4: Synthesis aggregation (LLM-based)
- Week 5: Iterative refinement loop
- Week 6: Inter-tissue communication and data contracts

---

## Phase 7 — Consensus & Conflict Resolution
**Sources:** §14 (Consensus & Conflict Resolution)  
**Effort:** L  
**Dependency:** Phase 6

### What to build

**Conflict detection:**
- `ConflictDetector` runs after aggregation if multiple outputs exist
- Detects: schema mismatch, semantic contradiction, confidence gap > threshold, scope mismatch

**5 consensus modes (selectable per GenomeModule):**
```python
class ConsensusMode(StrEnum):
    MAJORITY = "majority"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    EVIDENCE_WEIGHTED = "evidence_weighted"
    HIERARCHICAL = "hierarchical"
    DELIBERATIVE = "deliberative"
```

**Severity classification → response:**
- Low: normalise locally, continue
- Medium: run evaluation pass, trigger refinement
- High: escalate to organ layer, suspend output

**Adjudication:**
- `Adjudicator` invoked for high-severity conflicts
- Scores candidates against objective criteria
- Produces single output with `adjudication_trace: list[AdjudicationStep]`

**Bounded iteration:**
- Max rounds configurable per tissue
- Timeout failsafe: if no convergence by deadline → partial output with `confidence=low`

**Cadence:**
- Week 1: Conflict detection, severity classification, majority + confidence-weighted
- Week 2: Evidence-weighted, hierarchical override
- Week 3: Deliberative consensus, adjudication, bounded iteration

---

## Phase 8 — Task Decomposition & DAG Scheduling
**Sources:** §13 (Task Decomposition & Orchestration) + §6 (Concurrency)  
**Effort:** XL  
**Dependency:** Phases 4, 6

### What to build

Currently: one signal → one module. This phase makes the organism able to decompose a task into a dependency graph and execute it.

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
- `TaskScheduler.tick()` — called on each runtime cycle
- Dispatches all `ready` nodes in parallel up to concurrency limit
- Handles priority queues, domain queues, retry queues, deferred queues

**Adaptive replanning:**
- When a node fails or produces surprising output, `Replanner` may:
  - Alter the graph (add/remove nodes)
  - Reroute tasks to different owners
  - Inject new validation steps
  - Terminate low-value subpaths

**Cadence:**
- Week 1–2: TaskNode, TaskGraph, topological sort, basic scheduler
- Week 3: Priority + domain queues
- Week 4: Functional + temporal decomposition strategies
- Week 5: Adaptive replanning
- Week 6: Integration with cell execution plans (Phase 4) and tissue runtime (Phase 6)

---

## Phase 9 — Organ Coordination & Collective Intelligence
**Sources:** §11 (Organ-Level) + §12 (Collective Intelligence)  
**Effort:** XL  
**Dependency:** Phases 6, 7, 8

### What to build

**Organ coordination layer:**
- `OrganCoordinator` owns a `TaskGraph` scoped to the organ's domain
- Decomposes domain objective into tissue-level tasks
- Manages: sequential phases, parallel phases, conditional branching, iterative loops
- Produces one unified organ-level output (structured result + confidence + reasoning summary)

**Hierarchical control:**
- Brain organ can issue directives to other organs via `OrganDirective`
- Organs report back to brain via `OrganReport`
- Brain synthesises across organs → organism decision

**Voice unification:**
- Each layer (tissue, organ, organism) produces one output even when many contributors exist
- `VoiceUnifier` at each level: applies configured consensus mode → single structured output

**Organism-level synthesis:**
- Final output assembled from organ reports
- Cross-organ conflict resolution (same mechanisms as Phase 7 but at organ scope)
- Output includes: structured result, contributing organs, confidence, decision provenance

**Cadence:**
- Week 1–2: OrganCoordinator, tissue task distribution
- Week 3: Sequential + parallel flow control
- Week 4: Conditional branching + iterative organ loops
- Week 5: Brain organ → directive loop
- Week 6: Organism-level synthesis and voice unification

---

## Phase 10 — Concurrency & Network Optimisation
**Sources:** §6 (Concurrency) + §7 (Network Efficiency)  
**Effort:** XL  
**Dependency:** Phases 8, 9

### What to build

**Backpressure propagation:**
- Each layer exposes a `pressure: float` signal (0.0 = relaxed, 1.0 = saturated)
- Upstream dispatchers throttle when downstream pressure exceeds threshold
- Implemented as async feedback channel between layers

**Provider-aware throttling:**
- Track per-provider: request rate, token rate, error rate, latency p95
- `ProviderHealthMonitor` adjusts concurrency limits dynamically
- High latency → reduce parallel calls → shift simple tasks to local SLLMs

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
- Sends as one request, splits response back to individual proteins

**Cadence:**
- Week 1–2: ResultCache, TemplateCache, deduplication
- Week 3: Backpressure signals between layers
- Week 4: ProviderHealthMonitor, adaptive throttling
- Week 5–6: BatchCollector, local SLLM offloading preference

---

## Phase 11 — Failure Resilience
**Sources:** §16 (Failure Handling & Resilience)  
**Effort:** L  
**Dependency:** Phase 9

### What to build

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

**Cadence:**
- Week 1: Failure classification, fallback path framework
- Week 2: Resilience modes, circuit breaker per provider
- Week 3: Checkpointing and replay

---

## Phase 12 — Observability & Telemetry
**Sources:** §17 (Observability & Telemetry)  
**Effort:** L  
**Dependency:** Phase 10

### What to build

**Hierarchical trace IDs:**
- `TraceContext` propagated through every layer: `{organism_request_id, organ_span_id, tissue_span_id, cell_run_id, protein_call_id}`
- Injected into every adapter call, every tissue message, every organ directive
- All existing RuntimeEvents gain `trace_context: TraceContext`

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

**Cadence:**
- Week 1: TraceContext propagation through all layers
- Week 2: Typed event model, structured metrics
- Week 3: Replayability API, decision provenance

---

## Phase 13 — Security & Governance
**Sources:** §18 (Security & Governance)  
**Effort:** M  
**Dependency:** Phase 12

### What to build

**Data classification:**
- `DataClass` enum: `public | internal | confidential | restricted`
- Tagged on: Signal payloads, MemoryRecords, protein outputs
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
- Membrane rejects signals that would require a disallowed provider
- Sensitive signals → force local SLLM

**Full audit log:**
- `AuditRecord`: who, what component, what data touched, what decision made, what policy checked, outcome
- Separate append-only store from RuntimeEvents
- API: `GET /api/audit` (restricted to admin roles)

**Multi-tenant isolation:**
- Already partially done (organisms are isolated)
- Add: strict data partitioning, separate memory spaces per organism, scoped execution contexts

**Cadence:**
- Week 1: DataClass tagging, provider allowlist enforcement
- Week 2: 6 policy enforcement points, full audit log

---

## Phase 14 — Frontend Visualization (Parallel Track)
**Sources:** §17 (Dashboards) + §19 (Example Flows as UX inspiration)  
**Effort:** L per surface (runs in parallel with backend phases)  
**Dependency:** Data from each backend phase as it lands

### Surfaces to build (in priority order)

| Surface | Depends on | What it shows |
|---|---|---|
| **Pipeline trace deep-dive** | Phase 12 (trace IDs) | Full protein→cell→tissue→organ→organism trace tree for one request |
| **Token & cost dashboard** | Phase 2 (usage tracking) | Token usage by provider, model class, organ; cost per objective |
| **Cell coordination view** | Phase 4 | Proteins within a cell, their execution order, shared state |
| **Tissue aggregation view** | Phase 6 | Cell outputs side-by-side, aggregation result, consensus path |
| **DAG visualizer** | Phase 8 | Task graph for a decomposed objective |
| **Organ health dashboard** | Phase 9 | Organ status, active tasks, output confidence |
| **Resilience / failure view** | Phase 11 | Fallback activations, degraded modes, checkpoint history |
| **Governance audit log** | Phase 13 | Policy enforcement events, access control decisions |

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
NOW                                                                    18 MONTHS+
│                                                                              │
├─P1──────┤  Skeletal Capability Framework      M   · 2 weeks
├─P2──────┤  Model Interface Layer & Provider Routing  M   · 2 weeks
├─P3────────┤  5 Protein Types                 M   · 2 weeks
├─P4──────────────┤  Intra-Cell Coordination   L   · 3 weeks
├─P5────────────────────┤  Layered Memory       L   · 3 weeks
├─P6──────────────────────────────┤  Tissue Aggregation  XL · 6 weeks
├─P7────────────────────────────────────┤  Consensus      L   · 3 weeks
├─P8───────────────────────────────────────────┤  Task DAG XL · 6 weeks
├─P9──────────────────────────────────────────────────┤  Organs XL · 6 weeks
├─P10─────────────────────────────────────────────────────┤  Concurrency XL · 6 weeks
├─P11───────────────────────────────────────────────────────────┤  Resilience L · 3 weeks
├─P12─────────────────────────────────────────────────────────────┤  Observability L · 3 weeks
├─P13───────────────────────────────────────────────────────────────┤  Governance M · 2 weeks
└─P14  (frontend, parallel track, surfaces ship as backend phases land)
```

| Phase | What | Effort | Unlock |
|---|---|---|---|
| P1 | Skeletal Capability Framework | M | Bone contracts + enzyme compilation + BoneCortex; capability graph; Ribosome no longer names tools directly |
| P2 | Model Interface Layer & Provider Routing | M | `LlmProteinInstantiationRequest`, `ModelRoutingDecision`, `ProviderModelProfile` registry, `CellModelRouter` (Day-One deterministic policy), routing trace in `AnswerProtein`, `ModelExecutionTelemetry`; Tissue/Organ/Organism router stubs |
| P3 | 5 Protein Types | M | Distinct execution + validation per protein category |
| P4 | Intra-Cell Coordination | L | Cells run multi-protein plans, not just one module |
| P5 | Layered Memory | L | Context builds on prior work; organism has continuity |
| P6 | Tissue Aggregation | XL | Tissues do real work; first true collective intelligence |
| P7 | Consensus & Conflict Resolution | L | Divergent results become coherent decisions |
| P8 | Task Decomposition & DAG | XL | Complex objectives decompose into executable graphs |
| P9 | Organ Coordination | XL | Strategic reasoning, brain-to-body directive loop |
| P10 | Concurrency & Network Optimisation | XL | Scale without provider/bandwidth collapse |
| P11 | Failure Resilience | L | Weaken intelligently instead of breaking |
| P12 | Observability & Telemetry | L | Full trace provenance, replayability, metrics |
| P13 | Security & Governance | M | Production-grade audit, data classification, policy |
| P14 | Frontend (parallel) | L per surface | Operators can see and reason about the organism |
| P15 | Future Extensions | Research | Self-healing, multimodal, autonomous goals |

**Total to full production system:**
- Solo/part-time: ~24–36 months
- Dedicated 2-person team: ~12–18 months
- Phases 1–5 alone give you a meaningfully smarter organism in ~3 months (solo) or ~6 weeks (2-dev)

---

## What Gives the Most Value Soonest

If you want to demo the system doing real work as fast as possible:

1. **P1 (Bones)** — immediately makes the genome much more expressive
2. **P2 (Model Interface)** — makes LLM calls production-quality
3. **P5 (Memory)** — gives the organism actual continuity; this is the most "organism-like" feeling unlock
4. **P4 (Intra-Cell)** — multi-protein cells start to feel alive
5. **P6 partial (Tissue Aggregation, simple + weighted only)** — first emergent result from multiple sources
