from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class BaseConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, serialize_by_alias=True)


class LifecycleState(StrEnum):
    HIBERNATED = "hibernated"
    ACTIVE = "active"
    DEGRADED = "degraded"
    TERMINATED = "terminated"


class ProteinStatus(StrEnum):
    GENERATED = "generated"
    APPROVED = "approved"
    REPAIRED = "repaired"
    DROPPED = "dropped"
    BLOCKED = "blocked"


class DataClass(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


_DATA_CLASS_RANK = {
    DataClass.PUBLIC: 0,
    DataClass.INTERNAL: 1,
    DataClass.CONFIDENTIAL: 2,
    DataClass.RESTRICTED: 3,
}


def highest_data_class(*values: DataClass | str) -> DataClass:
    normalized = [DataClass(value) for value in values]
    return max(normalized, key=_DATA_CLASS_RANK.get, default=DataClass.INTERNAL)


class TraceContext(BaseConfigModel):
    request_id: str = Field(default_factory=lambda: f"request-{uuid4().hex}")
    organism_id: str
    cell_run_id: str | None = None
    step_id: str | None = None
    protein_id: str | None = None
    provider_call_id: str | None = None

    def child(self, **updates: str | None) -> "TraceContext":
        return self.model_copy(update=updates)


class MisfoldingType(StrEnum):
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    EXECUTION = "execution"
    CONTEXT = "context"
    TOXIC = "toxic"


class GolgiDecision(StrEnum):
    PASS = "pass"
    REPAIR = "repair"
    DESTROY = "destroy"


class ContractStatus(StrEnum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class RecordStatus(StrEnum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class StructuralResourceKind(StrEnum):
    DATABASE_SCHEMA = "database_schema"
    TABLE = "table"
    INDEX = "index"
    BLOB_STORE = "blob_store"
    OBJECT_PREFIX = "object_prefix"
    QUEUE = "queue"
    TOPIC = "topic"
    SERVICE_CONTRACT = "service_contract"
    ADAPTER = "adapter"


class StructuralOperation(StrEnum):
    GROW = "grow"
    REMODEL = "remodel"
    RETIRE = "retire"


class MemoryType(StrEnum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class MemoryAdmissionStatus(StrEnum):
    ADMITTED = "admitted"
    REJECTED = "rejected"


class ResourceHealth(StrEnum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class StructuralEffectStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class MemoryPolicyStatus(StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"


class DevelopmentStage(StrEnum):
    ZYGOTE = "zygote"
    EMBRYO = "embryo"
    FETUS = "fetus"
    BORN = "born"
    JUVENILE = "juvenile"
    ADULT = "adult"
    DEGRADED = "degraded"
    DEAD = "dead"


class CellHealthState(StrEnum):
    ALIVE = "alive"
    STRESSED = "stressed"
    DEGRADED = "degraded"
    HIBERNATING = "hibernating"
    SELF_CONSUMING = "self_consuming"
    DEAD = "dead"


class DivisionMode(StrEnum):
    SYMMETRIC = "symmetric"
    ASYMMETRIC = "asymmetric"
    FOUNDER = "founder"
    REPAIR = "repair"


class RuntimeEventType(StrEnum):
    ORGANISM_CREATED = "organism_created"
    LIFECYCLE = "lifecycle"
    MEMBRANE = "membrane"
    CYTOPLASM = "cytoplasm"
    NUCLEUS = "nucleus"
    RIBOSOME = "ribosome"
    GOLGI = "golgi"
    LYSOSOME = "lysosome"
    PEROXISOME = "peroxisome"
    MITOCHONDRIA = "mitochondria"
    VACUOLE = "vacuole"
    SKELETON = "skeleton"
    PROTEIN = "protein"
    STRUCTURE_REQUEST = "structure_request"
    MEMORY = "memory"
    POLICY = "policy"
    GENOME = "genome"
    MAINTENANCE = "maintenance"
    METRIC = "metric"
    ALERT = "alert"
    REPLAY = "replay"
    REVIEW = "review"
    GROWTH = "growth"
    CELL_DIVISION = "cell_division"
    FOOD = "food"
    OXYGEN = "oxygen"
    SOUL = "soul"
    BONE = "bone"
    REPRODUCTION = "reproduction"
    ER = "er"
    VESICLE = "vesicle"
    CYTOSKELETON = "cytoskeleton"
    HEALTH = "health"
    CELL_EXECUTION = "cell_execution"


class MembraneDecisionAction(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"


class ExecutionStrategy(StrEnum):
    PRECOMPUTED = "precomputed"
    DETERMINISTIC_TOOL = "deterministic_tool"
    LLM_STUB = "llm_stub"   # always mock, never calls a provider
    LLM = "llm"              # live provider call; falls back to stub if no key


class LlmProvider(StrEnum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GROK = "grok"
    GEMINI = "gemini"


class ModelClass(StrEnum):
    FAST = "fast"            # haiku / gpt-4o-mini / gemini-flash
    STANDARD = "standard"    # sonnet / gpt-4o / gemini-pro
    REASONING = "reasoning"  # opus / o3 / gemini-thinking


class ProteinType(StrEnum):
    """The five protein categories. Drives prompt construction and validation rules.

    A module that leaves protein_type unset is prompted as REASONING but gets no
    type-specific validation — tagging a module is an explicit opt-in to the
    stricter per-type rules.
    """
    REASONING = "reasoning"              # LLM chain-of-thought; validated on confidence
    RETRIEVAL = "retrieval"              # bone/DB/file lookup; validated on non-empty + cited source
    TRANSFORMATION = "transformation"    # reshape data; validated against declared output_schema
    AGGREGATION = "aggregation"          # combine N inputs; validated on presence + non-contradiction
    EVALUATION = "evaluation"            # score another protein; validated on score in [0,1] + criteria


class ExecutionStepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class ExecutionStep(BaseConfigModel):
    """One genome-declared unit in a cell-local execution plan."""

    step_id: str = Field(min_length=1, pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
    module_id: str = Field(min_length=1)
    depends_on: list[str] = Field(default_factory=list)
    condition: str | None = Field(default=None, min_length=1, max_length=1_000)
    input_map: dict[str, Any] = Field(default_factory=dict)
    max_iterations: int = Field(default=1, ge=1, le=10)
    iterate_while: str | None = Field(default=None, min_length=1, max_length=1_000)

    @model_validator(mode="after")
    def validate_iteration_contract(self) -> "ExecutionStep":
        if self.max_iterations > 1 and self.iterate_while is None:
            raise ValueError("max_iterations > 1 requires iterate_while")
        if self.iterate_while is not None and self.max_iterations == 1:
            raise ValueError("iterate_while requires max_iterations > 1")
        return self


class CellExecutionPlan(BaseConfigModel):
    """A bounded DAG of proteins executed inside one selected cell."""

    plan_id: str = Field(min_length=1)
    steps: list[ExecutionStep] = Field(min_length=1, max_length=100)
    final_step_id: str | None = None
    fail_fast: bool = True
    max_parallelism: int = Field(default=4, ge=1, le=16)

    @model_validator(mode="after")
    def validate_graph(self) -> "CellExecutionPlan":
        step_ids = [step.step_id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("execution plan step ids must be unique")
        known = set(step_ids)
        for step in self.steps:
            unknown = sorted(set(step.depends_on) - known)
            if unknown:
                raise ValueError(
                    f"execution step {step.step_id!r} has unknown dependencies: {', '.join(unknown)}"
                )
            if step.step_id in step.depends_on:
                raise ValueError(f"execution step {step.step_id!r} cannot depend on itself")
        if self.final_step_id is not None and self.final_step_id not in known:
            raise ValueError("final_step_id must identify a step in the execution plan")

        visiting: set[str] = set()
        visited: set[str] = set()
        dependencies = {step.step_id: step.depends_on for step in self.steps}

        def visit(step_id: str) -> None:
            if step_id in visiting:
                raise ValueError("execution plan dependencies must be acyclic")
            if step_id in visited:
                return
            visiting.add(step_id)
            for dependency in dependencies[step_id]:
                visit(dependency)
            visiting.remove(step_id)
            visited.add(step_id)

        for step_id in step_ids:
            visit(step_id)
        return self


class Actor(BaseConfigModel):
    actor_id: str = Field(min_length=1)
    roles: list[str] = Field(default_factory=lambda: ["operator"])


class IdentityProfile(BaseConfigModel):
    name: str = Field(default="Preon Organism", min_length=1)
    purpose: str = "Deterministic organism runtime"


class PolicySet(BaseConfigModel):
    allowed_signal_types: list[str] = Field(default_factory=lambda: ["query", "calculate", "contract.call", "search"])
    forbidden_terms: list[str] = Field(default_factory=lambda: ["delete all", "exfiltrate", "bypass policy"])
    required_roles: list[str] = Field(default_factory=lambda: ["operator"])
    rate_limit_per_actor: int = Field(default=8, ge=1)


class ResourceBudget(BaseConfigModel):
    compute_units: int = Field(default=10, ge=0)
    memory_units: int = Field(default=10, ge=0)
    tool_calls: int = Field(default=4, ge=0)


class GenomeModule(BaseConfigModel):
    module_id: str = Field(min_length=1)
    signal_types: list[str] = Field(default_factory=list)
    execution_strategy: ExecutionStrategy = ExecutionStrategy.LLM_STUB
    deterministic_tool: str | None = None
    # LLM routing — static override fields (used when model_routing_policy="explicit_override"
    # or as a provider hint when model_routing_policy="emergent_local_first")
    llm_provider: LlmProvider | None = None
    llm_model_class: ModelClass | None = ModelClass.STANDARD
    llm_model_id: str | None = None   # overrides model_class when set
    # Phase 2: model routing constraints exposed to CellModelRouter
    protein_type: ProteinType | None = None   # unset = prompted as reasoning, no per-type validation
    allowed_providers: list[str] = Field(default_factory=list)    # empty = all registered
    min_reasoning_depth: str | None = None  # shallow|moderate|deep
    max_cost_tier: str | None = None        # cheap|balanced|premium
    data_class_allowed: list[DataClass] = Field(default_factory=list)
    model_routing_policy: str = "emergent_local_first"  # emergent_local_first|explicit_override|organism_required
    token_budget: int | None = None
    latency_budget_ms: int | None = None
    llm_fallback_chain: list[tuple[str, str, str | None]] = Field(default_factory=list)
    # Phase 3: per-protein-type execution and validation inputs
    output_schema: dict[str, str] | None = None   # field -> declared type; drives transformation validation
    min_confidence: float | None = Field(default=None, ge=0, le=1)  # reasoning floor; None = DEFAULT_MIN_CONFIDENCE
    evaluation_criteria: list[str] = Field(default_factory=list)    # criteria an evaluation protein scores against
    # Phase 4: optional cell-local multi-protein plan triggered when this module is selected.
    execution_plan: CellExecutionPlan | None = None


class DivisionLoadGate(BaseConfigModel):
    # Minimum organism-level protein throughput before division is productive.
    # Prevents splitting an idle/immature cell into two idle cells.
    min_protein_throughput: int = Field(default=10, ge=1)


class DivisionCapabilityGate(BaseConfigModel):
    min_successful_proteins: int = Field(default=50, ge=1)
    min_distinct_signal_types: int = Field(default=3, ge=1)
    min_avg_confidence: float = Field(default=0.70, ge=0, le=1)


class DivisionLifecycleGate(BaseConfigModel):
    max_generation: int = Field(default=10, ge=0)
    required_lifecycle_state: str = Field(default="active")


class DivisionGates(BaseConfigModel):
    load: DivisionLoadGate = Field(default_factory=DivisionLoadGate)
    capability: DivisionCapabilityGate = Field(default_factory=DivisionCapabilityGate)
    lifecycle: DivisionLifecycleGate = Field(default_factory=DivisionLifecycleGate)


class DivisionPolicy(BaseConfigModel):
    can_divide: bool = True
    gates: DivisionGates = Field(default_factory=DivisionGates)
    allowed_modes: list[DivisionMode] = Field(
        default_factory=lambda: [DivisionMode.SYMMETRIC, DivisionMode.ASYMMETRIC]
    )
    preferred_mode: DivisionMode = DivisionMode.ASYMMETRIC
    cooldown_ms: int = Field(default=30_000, ge=0)
    max_daughters_per_division: int = Field(default=2, ge=2, le=4)


class GateResult(BaseConfigModel):
    passed: bool
    reason: str
    measured: dict[str, Any] = Field(default_factory=dict)


class DivisionReadinessResult(BaseConfigModel):
    cell_id: str
    organism_id: str
    eligible: bool
    blocked_by: str | None = None
    load_gate: GateResult
    capability_gate: GateResult
    lifecycle_gate: GateResult
    recommended_mode: DivisionMode
    policy_applied: bool


class Genome(BaseConfigModel):
    genome_id: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    core_instruction_set: list[str] = Field(
        default_factory=lambda: [
            "read_input",
            "load_context",
            "select_module",
            "execute",
            "validate_protein",
            "emit_signal",
            "update_memory",
        ]
    )
    modules: list[GenomeModule] = Field(
        default_factory=lambda: [
            GenomeModule(
                module_id="arithmetic",
                signal_types=["calculate"],
                execution_strategy=ExecutionStrategy.DETERMINISTIC_TOOL,
                deterministic_tool="calculator",
            ),
            GenomeModule(
                module_id="reasoning",
                signal_types=["query", "task.plan"],
                execution_strategy=ExecutionStrategy.LLM,
                llm_provider=LlmProvider.ANTHROPIC,
                llm_model_class=ModelClass.STANDARD,
                protein_type=ProteinType.REASONING,
            ),
            GenomeModule(
                module_id="retrieval",
                signal_types=["search"],
                execution_strategy=ExecutionStrategy.DETERMINISTIC_TOOL,
                deterministic_tool="knowledge.reference.lookup",
                protein_type=ProteinType.RETRIEVAL,
            ),
            GenomeModule(
                module_id="contract_call",
                signal_types=["contract.call"],
                execution_strategy=ExecutionStrategy.DETERMINISTIC_TOOL,
                deterministic_tool="contract_gateway",
            ),
        ]
    )
    regulatory_rules: list[dict[str, Any]] = Field(default_factory=list)
    capability_registry: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=lambda: {"external_side_effects": False})
    division_policy: DivisionPolicy | None = None


class CellRecord(BaseConfigModel):
    cell_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    organ_id: str = Field(default="core", min_length=1)
    tissue_id: str = Field(default="executive")
    cell_type: str = Field(default="worker", min_length=1)
    cell_genome_id: str | None = None
    expression_profile: dict[str, float] = Field(default_factory=lambda: {"reasoning": 0.7, "io": 0.5})
    local_state: dict[str, Any] = Field(default_factory=dict)
    lifecycle_state: LifecycleState = LifecycleState.HIBERNATED
    health_state: CellHealthState = CellHealthState.ALIVE
    health_score: float = Field(default=1.0, ge=0, le=1)
    parent_cell_id: str | None = None
    generation: int = Field(default=0, ge=0)
    resource_budget: ResourceBudget = Field(default_factory=ResourceBudget)
    created_at: datetime = Field(default_factory=utc_now)
    last_active_at: datetime | None = None


class OrganismRecord(BaseConfigModel):
    organism_id: str = Field(min_length=1)
    owner_user_id: str | None = None
    identity_profile: IdentityProfile = Field(default_factory=IdentityProfile)
    lifecycle_state: LifecycleState = LifecycleState.HIBERNATED
    long_term_memory: dict[str, Any] = Field(default_factory=dict)
    goals: list[str] = Field(default_factory=list)
    policies: PolicySet = Field(default_factory=PolicySet)
    organ_registry: dict[str, Any] = Field(default_factory=lambda: {"executive": {"status": "available"}})
    tissue_templates: dict[str, Any] = Field(default_factory=lambda: {"executive": {"cell_type": "worker"}})
    cell_blueprints: dict[str, Any] = Field(default_factory=lambda: {"worker": {"runtime": "deterministic"}})
    genome_id: str = "genome-default"
    development_stage: DevelopmentStage = DevelopmentStage.BORN
    growth_state: dict[str, Any] = Field(default_factory=dict)
    lineage_log: list[dict[str, Any]] = Field(default_factory=list)
    last_state_snapshot: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Signal(BaseConfigModel):
    signal_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    actor: Actor = Field(default_factory=lambda: Actor(actor_id="operator"))
    type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    context_refs: list[str] = Field(default_factory=list)
    priority: int = Field(default=5, ge=0, le=10)
    data_class: DataClass = DataClass.INTERNAL
    trace_context: TraceContext | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ValidationReport(BaseConfigModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    repaired: bool = False
    misfolding_types: list[MisfoldingType] = Field(default_factory=list)


class MembraneDecision(BaseConfigModel):
    action: MembraneDecisionAction
    reason: str
    code: str


class Protein(BaseConfigModel):
    protein_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    source_signal_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0, le=1)
    status: ProteinStatus = ProteinStatus.GENERATED
    data_class: DataClass = DataClass.INTERNAL
    trace_context: TraceContext | None = None
    validation_report: ValidationReport = Field(default_factory=lambda: ValidationReport(valid=True))
    created_at: datetime = Field(default_factory=utc_now)


class ExecutionStepResult(BaseConfigModel):
    step_id: str
    module_id: str
    status: ExecutionStepStatus
    protein: Protein | None = None
    iterations: int = Field(default=0, ge=0)
    input_payload: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    iteration_limit_reached: bool = False
    trace_context: TraceContext | None = None
    failure_type: str | None = None


class CellExecutionRun(BaseConfigModel):
    run_id: str
    plan_id: str
    organism_id: str
    cell_id: str
    signal_id: str
    owner_user_id: str | None = None
    status: Literal["completed", "failed", "partial", "degraded", "cancelled", "timed_out"]
    step_results: list[ExecutionStepResult] = Field(default_factory=list)
    final_step_id: str
    final_protein_id: str | None = None
    shared_state: dict[str, Any] = Field(default_factory=dict)
    data_class: DataClass = DataClass.INTERNAL
    trace_context: TraceContext | None = None
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime = Field(default_factory=utc_now)


class LlmProtein(BaseConfigModel):
    """Active execution unit — makes exactly one LLM call, then deconstructed by Proteasome."""
    protein_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    source_signal_id: str = Field(min_length=1)
    gene_id: str = Field(min_length=1)
    # Routing fields — resolved by CellModelRouter before instantiation
    provider: str = Field(min_length=1)
    model_class: str = Field(min_length=1)
    model_id: str | None = None
    token_budget: int = 4096
    latency_budget_ms: int = 5000
    fallback_chain: list[tuple[str, str, str | None]] = Field(default_factory=list)
    routing_confidence: float = 0.0
    routing_resolved_at: str = "cell"
    routing_consensus_path: list[str] = Field(default_factory=list)
    routing_reason: str = ""
    raw_answer: Any | None = None
    consumed: bool = False
    data_class: DataClass = DataClass.INTERNAL
    trace_context: TraceContext | None = None
    created_at: datetime = Field(default_factory=utc_now)


class ProteasomeReceipt(BaseConfigModel):
    protein_id: str
    cytoplasm_slot: str
    raw_answer: Any
    source_gene_id: str
    provider: str


class CytoplasmEntry(BaseConfigModel):
    value: Any
    metadata: dict[str, Any] = Field(default_factory=dict)
    written_at: datetime = Field(default_factory=utc_now)


class CytoplasmSnapshot(BaseConfigModel):
    slots: dict[str, CytoplasmEntry]


class ProteinDestination(BaseConfigModel):
    kind: Literal["cytoplasm", "cell", "membrane"]
    slot: str | None = None
    cell_id: str | None = None


class AnswerProtein(BaseModel):
    """Immutable transport payload produced after Proteasome deconstructs an LlmProtein."""
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True, serialize_by_alias=True)

    answer_protein_id: str = Field(min_length=1)
    answer: Any
    source_gene_id: str
    source_provider: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    destination: ProteinDestination
    routing_trace: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def route_key(self) -> str:
        if self.destination.kind == "cytoplasm":
            return f"cytoplasm:{self.destination.slot}"
        if self.destination.kind == "cell":
            return f"cell:{self.destination.cell_id}"
        return "membrane"


class GolgiReport(BaseConfigModel):
    decision: GolgiDecision
    reasons: list[str] = Field(default_factory=list)
    protein: AnswerProtein | None = None


class RetrySignal(BaseConfigModel):
    signal_type: str = "retry"
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DestructionRecord(BaseConfigModel):
    protein_id: str
    reason: str
    rolled_back_slots: list[str] = Field(default_factory=list)
    destroyed_at: datetime = Field(default_factory=utc_now)
    retry_signal: RetrySignal | None = None


class Contract(BaseConfigModel):
    contract_id: str = Field(min_length=1)
    owner_user_id: str | None = None
    name: str = Field(min_length=1)
    contract_schema: dict[str, Any] = Field(default_factory=dict, alias="schema", serialization_alias="schema")
    allowed_actions: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=lambda: ["operator"])
    rate_limits: dict[str, int] = Field(default_factory=lambda: {"per_minute": 60})
    dependencies: list[str] = Field(default_factory=list)
    adapter_id: str | None = None
    input_mapping: dict[str, str] = Field(default_factory=dict)
    output_mapping: dict[str, str] = Field(default_factory=dict)
    capability_ids: list[str] = Field(default_factory=list)
    test_vectors: list[dict[str, Any]] = Field(default_factory=list)
    created_by: str | None = None
    deprecated_reason: str | None = None
    status: ContractStatus = ContractStatus.ACTIVE
    usage_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class RuntimeEvent(BaseConfigModel):
    event_id: str = Field(min_length=1)
    organism_id: str | None = None
    cell_id: str | None = None
    signal_id: str | None = None
    protein_id: str | None = None
    contract_id: str | None = None
    type: RuntimeEventType
    message: str
    data_class: DataClass = DataClass.INTERNAL
    trace_context: TraceContext | None = None
    values: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class StructureRequest(BaseConfigModel):
    request_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    signal_id: str | None = None
    requested_contract: str
    reason: str
    status: Literal["open", "resolved", "blocked"] = "open"
    created_at: datetime = Field(default_factory=utc_now)


class MemoryRecord(BaseConfigModel):
    memory_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    owner_user_id: str | None = None
    scope: str = Field(default="organism", min_length=1)
    kind: str = Field(default="observation", min_length=1)
    memory_type: MemoryType = MemoryType.EPISODIC
    payload: dict[str, Any] = Field(default_factory=dict)
    source_signal_id: str | None = None
    source_run_id: str | None = None
    source_protein_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0, le=1)
    importance: float = Field(default=0.5, ge=0, le=1)
    data_class: DataClass = DataClass.INTERNAL
    trace_context: TraceContext | None = None
    admission_status: MemoryAdmissionStatus = MemoryAdmissionStatus.ADMITTED
    promotion_reason: str = "operator_admission"
    content_hash: str = Field(default="", min_length=0)
    ttl_seconds: int | None = Field(default=None, ge=1)
    last_accessed_at: datetime | None = None
    access_count: int = Field(default=0, ge=0)
    supersedes_memory_id: str | None = None
    superseded_by_memory_id: str | None = None
    storage_resource_id: str | None = None
    admission_policy_version_id: str | None = None
    status: RecordStatus = RecordStatus.ACTIVE
    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Capability(BaseConfigModel):
    capability_id: str = Field(min_length=1)
    owner_user_id: str | None = None
    name: str = Field(min_length=1)
    description: str = ""
    capability_schema: dict[str, Any] = Field(default_factory=dict, alias="schema", serialization_alias="schema")
    status: RecordStatus = RecordStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class GenomeVersion(BaseConfigModel):
    version_id: str = Field(min_length=1)
    genome_id: str = Field(min_length=1)
    owner_user_id: str | None = None
    version: int = Field(ge=1)
    genome: Genome
    status: Literal["draft", "active", "deprecated"] = "draft"
    created_at: datetime = Field(default_factory=utc_now)
    activated_at: datetime | None = None


class ReplayRun(BaseConfigModel):
    replay_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    signal_id: str = Field(min_length=1)
    original_protein: Protein | None = None
    replay_protein: Protein | None = None
    events: list[RuntimeEvent] = Field(default_factory=list)
    divergence_report: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class PolicyVersion(BaseConfigModel):
    policy_version_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    version: int = Field(ge=1)
    policies: PolicySet
    created_by: str | None = None
    status: Literal["active", "superseded"] = "active"
    created_at: datetime = Field(default_factory=utc_now)


class MaintenanceJobRun(BaseConfigModel):
    run_id: str = Field(min_length=1)
    status: Literal["completed", "failed"] = "completed"
    results: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class RuntimeAlert(BaseConfigModel):
    alert_id: str = Field(min_length=1)
    organism_id: str | None = None
    severity: Literal["info", "warning", "critical"] = "warning"
    source: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    status: Literal["active", "resolved"] = "active"
    related_event_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class ReviewRequest(BaseConfigModel):
    review_id: str = Field(min_length=1)
    owner_user_id: str | None = None
    resource_type: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""
    status: Literal["pending", "approved", "rejected"] = "pending"
    reviewer_id: str | None = None
    decision_reason: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    decided_at: datetime | None = None


class GameteRecord(BaseConfigModel):
    gamete_id: str = Field(min_length=1)
    source_organism_id: str = Field(min_length=1)
    role: Literal["mother", "father"]
    projection: dict[str, Any] = Field(default_factory=dict)
    emphasis: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class ZygoteGenome(BaseConfigModel):
    genome_id: str = Field(min_length=1)
    zygote_dna: dict[str, Any] = Field(default_factory=dict)
    organ_cell_dna: dict[str, dict[str, Any]] = Field(default_factory=dict)
    mother_gamete: GameteRecord
    father_gamete: GameteRecord
    merge_report: dict[str, Any] = Field(default_factory=dict)


class ZygoteRecord(BaseConfigModel):
    zygote_id: str = Field(min_length=1)
    owner_user_id: str | None = None
    mother_organism_id: str = Field(min_length=1)
    father_organism_id: str = Field(min_length=1)
    genome: ZygoteGenome
    stage: DevelopmentStage = DevelopmentStage.ZYGOTE
    oxygen_restricted: bool = True
    food_log: list[dict[str, Any]] = Field(default_factory=list)
    founder_plan: dict[str, Any] = Field(default_factory=dict)
    born_organism_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class OrganRecord(BaseConfigModel):
    organ_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    target_cell_count: int = Field(default=1, ge=0)
    status: RecordStatus = RecordStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)


class TissueRecord(BaseConfigModel):
    tissue_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    organ_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    target_cell_count: int = Field(default=1, ge=0)
    created_at: datetime = Field(default_factory=utc_now)


class CellDivisionRecord(BaseConfigModel):
    division_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    parent_cell_id: str = Field(min_length=1)
    daughter_cell_ids: list[str] = Field(default_factory=list)
    mode: DivisionMode = DivisionMode.SYMMETRIC
    genome_copied: bool = True
    organelles_duplicated: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class FoodIntake(BaseConfigModel):
    food_id: str = Field(min_length=1)
    organism_id: str | None = None
    zygote_id: str | None = None
    food_type: str = Field(default="task", min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    routed_to: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class OxygenProfile(BaseConfigModel):
    oxygen_id: str = Field(min_length=1)
    organism_id: str | None = None
    zygote_id: str | None = None
    compute_units: int = Field(default=1, ge=0)
    memory_units: int = Field(default=1, ge=0)
    storage_units: int = Field(default=1, ge=0)
    gpu_units: int = Field(default=0, ge=0)
    restricted: bool = True
    updated_at: datetime = Field(default_factory=utc_now)


class UmbilicalCord(BaseConfigModel):
    cord_id: str = Field(min_length=1)
    zygote_id: str = Field(min_length=1)
    mother_organism_id: str = Field(min_length=1)
    oxygen_profile_id: str | None = None
    status: Literal["connected", "blocked", "delivered"] = "connected"
    created_at: datetime = Field(default_factory=utc_now)


class SoulSnapshot(BaseConfigModel):
    soul_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    snapshot: dict[str, Any] = Field(default_factory=dict)
    reincarnated_organism_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class BoneStructureRecord(BaseConfigModel):
    bone_id: str = Field(min_length=1)
    organism_id: str | None = None
    owner_user_id: str | None = None
    name: str = Field(min_length=1)
    structure_type: Literal[
        "schema",
        "adapter",
        "capability",
        "contract",
        "bone_contract",
        "enzyme",
        "database_schema",
        "table",
        "index",
        "blob_store",
        "object_prefix",
        "queue",
        "topic",
        "service_contract",
    ] = "schema"
    definition: dict[str, Any] = Field(default_factory=dict)
    provider: str = "memory"
    provider_resource_ref: str | None = None
    observed_state: dict[str, Any] = Field(default_factory=dict)
    generation: int = Field(default=1, ge=1)
    health: ResourceHealth = ResourceHealth.UNKNOWN
    created_by_cell_id: str | None = None
    status: RecordStatus = RecordStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class StructureProposal(BaseConfigModel):
    proposal_id: str = Field(min_length=1)
    organism_id: str | None = None
    owner_user_id: str | None = None
    requested_by: str | None = None
    proposed_by_cell_id: str | None = None
    name: str = Field(min_length=1)
    structure_type: Literal[
        "schema",
        "adapter",
        "capability",
        "contract",
        "bone_contract",
        "enzyme",
        "database_schema",
        "table",
        "index",
        "blob_store",
        "object_prefix",
        "queue",
        "topic",
        "service_contract",
    ] = "schema"
    operation: StructuralOperation = StructuralOperation.GROW
    provider: str = "memory"
    definition: dict[str, Any] = Field(default_factory=dict)
    plan: dict[str, Any] = Field(default_factory=dict)
    plan_digest: str | None = None
    idempotency_key: str | None = None
    target_resource_id: str | None = None
    target_cell_id: str | None = None
    requested_permissions: list[str] = Field(default_factory=list)
    status: Literal["pending", "approved", "rejected"] = "pending"
    apply_status: Literal["pending", "queued", "processing", "applied", "failed", "not_applicable"] = "pending"
    resulting_bone_id: str | None = None
    source_run_id: str | None = None
    source_protein_ids: list[str] = Field(default_factory=list)
    decision_reason: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    decided_at: datetime | None = None
    applied_at: datetime | None = None


class StructuralEffect(BaseConfigModel):
    effect_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    organism_id: str | None = None
    owner_user_id: str | None = None
    provider: str
    plan_digest: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    status: StructuralEffectStatus = StructuralEffectStatus.PENDING
    attempt_count: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=5, ge=1)
    next_attempt_at: datetime = Field(default_factory=utc_now)
    lease_owner: str | None = None
    lease_expires_at: datetime | None = None
    last_error: str | None = None
    source_run_id: str | None = None
    source_protein_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None


class MemoryPolicyVersion(BaseConfigModel):
    policy_version_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    owner_user_id: str | None = None
    version: int = Field(ge=1)
    min_confidence: float = Field(default=0.75, ge=0, le=1)
    min_importance: float = Field(default=0.5, ge=0, le=1)
    default_ttl_seconds: int | None = Field(default=None, ge=1)
    context_token_budget: int = Field(default=1024, ge=128, le=131072)
    low_value_importance: float = Field(default=0.25, ge=0, le=1)
    low_value_age_days: int = Field(default=90, ge=1)
    allow_baseline_substrate_growth: bool = True
    status: MemoryPolicyStatus = MemoryPolicyStatus.ACTIVE
    created_by: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class ResourceGrant(BaseConfigModel):
    grant_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    owner_user_id: str | None = None
    resource_id: str = Field(min_length=1)
    cell_id: str = Field(min_length=1)
    permissions: list[str] = Field(default_factory=list)
    namespace: str | None = None
    provider: str = "memory"
    credential_ref: str | None = None
    status: Literal["active", "revoked"] = "active"
    created_by_cell_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    revoked_at: datetime | None = None


class OrganellePipeline(BaseConfigModel):
    pipeline_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    cell_id: str = Field(min_length=1)
    stages: list[str] = Field(default_factory=lambda: ["nucleus", "er", "golgi", "vesicle", "membrane"])
    status: Literal["planned", "completed", "failed"] = "planned"
    created_at: datetime = Field(default_factory=utc_now)


class VesicleMessage(BaseConfigModel):
    vesicle_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    source_cell_id: str = Field(min_length=1)
    target_cell_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    status: Literal["queued", "delivered", "dropped"] = "queued"
    created_at: datetime = Field(default_factory=utc_now)


class CytoskeletonTopology(BaseConfigModel):
    topology_id: str = Field(min_length=1)
    organism_id: str = Field(min_length=1)
    organ_edges: list[dict[str, str]] = Field(default_factory=list)
    tissue_edges: list[dict[str, str]] = Field(default_factory=list)
    cell_edges: list[dict[str, str]] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utc_now)


class CreateOrganismRequest(BaseConfigModel):
    identity_profile: IdentityProfile = Field(default_factory=IdentityProfile)
    goals: list[str] = Field(default_factory=list)
    policies: PolicySet = Field(default_factory=PolicySet)


class CreateContractRequest(BaseConfigModel):
    name: str = Field(min_length=1)
    contract_schema: dict[str, Any] = Field(default_factory=dict, alias="schema", serialization_alias="schema")
    allowed_actions: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=lambda: ["operator"])
    rate_limits: dict[str, int] = Field(default_factory=lambda: {"per_minute": 60})
    dependencies: list[str] = Field(default_factory=list)
    adapter_id: str | None = None
    input_mapping: dict[str, str] = Field(default_factory=dict)
    output_mapping: dict[str, str] = Field(default_factory=dict)
    capability_ids: list[str] = Field(default_factory=list)
    test_vectors: list[dict[str, Any]] = Field(default_factory=list)


class SubmitSignalRequest(BaseConfigModel):
    type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    context_refs: list[str] = Field(default_factory=list)
    priority: int = Field(default=5, ge=0, le=10)
    data_class: DataClass = DataClass.INTERNAL
    deadline_ms: int | None = Field(default=None, ge=1, le=300_000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResolveStructureRequestRequest(BaseConfigModel):
    contract_id: str | None = None


class BlockStructureRequestRequest(BaseConfigModel):
    reason: str = Field(default="Blocked by operator policy", min_length=1)


class CreateCellRequest(BaseConfigModel):
    organ_id: str = Field(default="core", min_length=1)
    tissue_id: str = Field(default="executive", min_length=1)
    cell_type: str = Field(default="worker", min_length=1)
    cell_genome_id: str | None = None
    expression_profile: dict[str, float] = Field(default_factory=dict)
    resource_budget: ResourceBudget = Field(default_factory=ResourceBudget)


class UpdateCellRequest(BaseConfigModel):
    organ_id: str | None = None
    tissue_id: str | None = None
    cell_type: str | None = None
    cell_genome_id: str | None = None
    expression_profile: dict[str, float] | None = None
    resource_budget: ResourceBudget | None = None
    lifecycle_state: LifecycleState | None = None
    health_state: CellHealthState | None = None
    health_score: float | None = Field(default=None, ge=0, le=1)


class CreateMemoryRequest(BaseConfigModel):
    scope: str = Field(default="organism", min_length=1)
    kind: str = Field(default="observation", min_length=1)
    memory_type: MemoryType = MemoryType.EPISODIC
    payload: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0, le=1)
    importance: float = Field(default=0.5, ge=0, le=1)
    data_class: DataClass = DataClass.INTERNAL
    ttl_seconds: int | None = Field(default=None, ge=1)
    supersedes_memory_id: str | None = None


class CreateCapabilityRequest(BaseConfigModel):
    name: str = Field(min_length=1)
    description: str = ""
    capability_schema: dict[str, Any] = Field(default_factory=dict, alias="schema", serialization_alias="schema")


class AdapterTestRequest(BaseConfigModel):
    payload: dict[str, Any] = Field(default_factory=dict)


class PolicySimulationRequest(BaseConfigModel):
    policies: PolicySet | None = None
    signal: SubmitSignalRequest


class PolicyUpdateRequest(BaseConfigModel):
    policies: PolicySet


class CreateGenomeVersionRequest(BaseConfigModel):
    genome: Genome


class GenomePreviewRequest(BaseConfigModel):
    signal_type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    cell_id: str | None = None


class CreateReviewRequest(BaseConfigModel):
    resource_type: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""


class DecideReviewRequest(BaseConfigModel):
    reason: str = Field(default="Reviewed", min_length=1)


class ReproductionNegotiateRequest(BaseConfigModel):
    mother_organism_id: str = Field(min_length=1)
    father_organism_id: str = Field(min_length=1)


class CreateZygoteRequest(BaseConfigModel):
    mother_organism_id: str = Field(min_length=1)
    father_organism_id: str = Field(min_length=1)


class DevelopZygoteRequest(BaseConfigModel):
    target_stage: DevelopmentStage | None = None
    food_payload: dict[str, Any] = Field(default_factory=dict)


class DivideCellRequest(BaseConfigModel):
    mode: DivisionMode = DivisionMode.SYMMETRIC


class UpdateDivisionPolicyRequest(BaseConfigModel):
    policy: DivisionPolicy


class ApplyGrowthTemplateRequest(BaseConfigModel):
    template_name: str = Field(default="human_minimal_v3", min_length=1)


class FoodIntakeRequest(BaseConfigModel):
    food_type: str = Field(default="task", min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class OxygenGrantRequest(BaseConfigModel):
    compute_units: int = Field(default=10, ge=0)
    memory_units: int = Field(default=10, ge=0)
    storage_units: int = Field(default=10, ge=0)
    gpu_units: int = Field(default=0, ge=0)
    restricted: bool = False


class CreateBoneProposalRequest(BaseConfigModel):
    organism_id: str | None = None
    name: str = Field(min_length=1)
    structure_type: Literal[
        "schema",
        "adapter",
        "capability",
        "contract",
        "database_schema",
        "table",
        "index",
        "blob_store",
        "object_prefix",
        "queue",
        "topic",
        "service_contract",
    ] = "schema"
    operation: StructuralOperation = StructuralOperation.GROW
    provider: str = "memory"
    definition: dict[str, Any] = Field(default_factory=dict)
    requested_by: str | None = None
    idempotency_key: str | None = None
    target_resource_id: str | None = None
    target_cell_id: str | None = None
    requested_permissions: list[str] = Field(default_factory=list)


class DecideProposalRequest(BaseConfigModel):
    reason: str = Field(default="Reviewed", min_length=1)
    plan_digest: str | None = None


class UpdateMemoryPolicyRequest(BaseConfigModel):
    min_confidence: float = Field(default=0.75, ge=0, le=1)
    min_importance: float = Field(default=0.5, ge=0, le=1)
    default_ttl_seconds: int | None = Field(default=None, ge=1)
    context_token_budget: int = Field(default=1024, ge=128, le=131072)
    low_value_importance: float = Field(default=0.25, ge=0, le=1)
    low_value_age_days: int = Field(default=90, ge=1)
    allow_baseline_substrate_growth: bool = True


class SubmitSignalResponse(BaseConfigModel):
    signal: Signal
    membrane_decision: MembraneDecision
    cell: CellRecord | None = None
    protein: Protein | None = None
    execution_run: CellExecutionRun | None = None
    events: list[RuntimeEvent] = Field(default_factory=list)
    structure_request: StructureRequest | None = None


class OrganismDetailResponse(BaseConfigModel):
    organism: OrganismRecord
    genome: Genome
    cells: list[CellRecord]
    events: list[RuntimeEvent]
    proteins: list[Protein]
    structure_requests: list[StructureRequest]
    memory_records: list[MemoryRecord] = Field(default_factory=list)


class GenomeValidationRequest(BaseConfigModel):
    genome: Genome


class GenomeValidationResponse(BaseConfigModel):
    genome_id: str
    report: ValidationReport


class HealthResponse(BaseConfigModel):
    status: str = "ok"
    runtime: str = "organism"
    storage: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def ensure_storage(self) -> "HealthResponse":
        if not self.storage:
            self.storage = {"mode": "memory", "primary": "postgres", "fallback": "memory", "degraded": True}
        return self
