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

## Phase 1 — Bones Library
**Sources:** `bones-and-llm-routing.md` + §4 (Protein Types)  
**Effort:** M  
**Dependency:** None — fully isolated, can start immediately

### What to build
A tool registry and ~15-20 deterministic bones implemented as pure functions.

**Tool Registry:**
- `tools/registry.py` — maps tool name → callable, self-documenting (input/output schema)
- `GenomeModule.deterministic_tool` already references by name; registry makes it pluggable
- Each tool: `def execute(payload: dict) -> dict` — no I/O, no network, deterministic

**Priority bones to implement first:**

| Tool | Input | Output | Complexity |
|---|---|---|---|
| `calculator` | `expression: str` | `result: float` | Already done |
| `unit_converter` | `value, from_unit, to_unit` | `result, unit` | S |
| `base_converter` | `value: str, from_base, to_base` | `result: str` | S |
| `date_diff` | `date_a, date_b` | `days: int, business_days: int` | S |
| `timestamp_converter` | `epoch` or `iso_string` | both forms | S |
| `z_table_lookup` | `z_score: float` | `p_value: float` | S (lookup table) |
| `periodic_table` | `element: str or int` | symbol, mass, group, period, etc. | S (data file) |
| `ip_subnet` | `cidr: str` | network, broadcast, host_range, mask | S |
| `haversine` | `lat1, lon1, lat2, lon2` | `distance_km: float` | S |
| `country_lookup` | `code: str` | name, alpha2, alpha3, calling_code | S (data file) |
| `http_status` | `code: int` | meaning, category | S (lookup) |
| `compound_interest` | `pv, rate, n, t` | `fv: float` | S |
| `bmi` | `weight_kg, height_m` | `bmi, category` | S |
| `morse_code` | `text: str, direction` | encoded or decoded | S |
| `luhn_check` | `card_number: str` | `valid: bool` | S |
| `molecular_weight` | `formula: str` | `weight_g_mol: float` | M (formula parser) |

**Cadence:**
- Week 1: registry + 8 simple bones
- Week 2: 6 data-file bones (periodic table, country lookup) + integration tests

**After this phase:** genome can reference any tool by name; adding a new bone is a 30-minute task.

---

## Phase 2 — Model Interface Layer
**Sources:** §5 (Model Interface Layer)  
**Effort:** M  
**Dependency:** Phase 0 (LLM adapters exist)

### What to build

**Token budgeting:**
- `LlmRequest` struct: `prompt, system, max_tokens, budget_tokens, priority`
- `budget_tokens` = protein-level limit; if prompt + expected output > budget → truncate context or defer
- Per-invocation token counter fed back into `Protein.payload["token_usage"]`

**N-tier fallback:**
```
primary: (provider="anthropic", model_class="standard")
  ↓ if timeout or 5xx
fallback_1: (provider="anthropic", model_class="fast")
  ↓ if still failing
fallback_2: (provider="openai", model_class="fast")
  ↓ if no keys or all fail
stub: llm_stub
```
Defined in `GenomeModule.llm_fallback_chain: list[LlmFallbackEntry]`

**Usage tracking:**
- Adapter returns `LlmResponse(content, token_usage, latency_ms, provider, model_id)`
- Ribosome stores these in protein payload
- RuntimeEvent logs usage per invocation

**Streaming (optional in this phase):**
- Add `adapter.stream(prompt) -> AsyncIterator[str]`
- Only wire to API endpoints that want streaming; internals still work buffered

**Cadence:**
- Week 1: LlmRequest struct, token budgeting, usage tracking
- Week 2: N-tier fallback chain, wire streaming to one API endpoint

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
├─P1──────┤  Bones Library                     M   · 2 weeks
├─P2──────┤  Model Interface Layer             M   · 2 weeks
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
| P1 | Bones Library | M | Rich deterministic tools for any genome |
| P2 | Model Interface Layer | M | Token budgets, n-tier fallback, usage tracking |
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
