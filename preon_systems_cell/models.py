from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

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
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


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


class Actor(BaseConfigModel):
    actor_id: str = Field(min_length=1)
    roles: list[str] = Field(default_factory=lambda: ["operator"])


class IdentityProfile(BaseConfigModel):
    name: str = Field(default="Preon Organism", min_length=1)
    purpose: str = "Deterministic organism runtime"


class PolicySet(BaseConfigModel):
    allowed_signal_types: list[str] = Field(default_factory=lambda: ["query", "calculate", "contract.call"])
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
    protein_type: str | None = None        # reasoning|retrieval|transformation|aggregation|evaluation
    allowed_providers: list[str] = Field(default_factory=list)    # empty = all registered
    min_reasoning_depth: str | None = None  # shallow|moderate|deep
    max_cost_tier: str | None = None        # cheap|balanced|premium
    data_class_allowed: list[str] = Field(default_factory=list)   # public|internal|confidential|restricted
    model_routing_policy: str = "emergent_local_first"  # emergent_local_first|explicit_override|organism_required
    token_budget: int | None = None
    latency_budget_ms: int | None = None
    llm_fallback_chain: list[tuple[str, str, str | None]] = Field(default_factory=list)


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
    validation_report: ValidationReport = Field(default_factory=lambda: ValidationReport(valid=True))
    created_at: datetime = Field(default_factory=utc_now)


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
    scope: str = Field(default="organism", min_length=1)
    kind: str = Field(default="observation", min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    source_signal_id: str | None = None
    confidence: float = Field(default=1.0, ge=0, le=1)
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
    owner_user_id: str | None = None
    name: str = Field(min_length=1)
    structure_type: Literal["schema", "adapter", "capability", "contract", "bone_contract", "enzyme"] = "schema"
    definition: dict[str, Any] = Field(default_factory=dict)
    status: RecordStatus = RecordStatus.ACTIVE
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class StructureProposal(BaseConfigModel):
    proposal_id: str = Field(min_length=1)
    owner_user_id: str | None = None
    requested_by: str | None = None
    name: str = Field(min_length=1)
    structure_type: Literal["schema", "adapter", "capability", "contract", "bone_contract", "enzyme"] = "schema"
    definition: dict[str, Any] = Field(default_factory=dict)
    status: Literal["pending", "approved", "rejected"] = "pending"
    decision_reason: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    decided_at: datetime | None = None


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
    payload: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0, le=1)


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
    name: str = Field(min_length=1)
    structure_type: Literal["schema", "adapter", "capability", "contract"] = "schema"
    definition: dict[str, Any] = Field(default_factory=dict)
    requested_by: str | None = None


class DecideProposalRequest(BaseConfigModel):
    reason: str = Field(default="Reviewed", min_length=1)


class SubmitSignalResponse(BaseConfigModel):
    signal: Signal
    membrane_decision: MembraneDecision
    cell: CellRecord | None = None
    protein: Protein | None = None
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
