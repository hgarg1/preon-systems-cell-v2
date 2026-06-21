from __future__ import annotations

import ast
from copy import deepcopy
import operator
import re
from dataclasses import dataclass, field
from uuid import uuid4

from preon_systems_cell.models import (
    BoneStructureRecord,
    CellRecord,
    CellDivisionRecord,
    CellHealthState,
    Capability,
    Contract,
    ContractStatus,
    CytoskeletonTopology,
    DevelopmentStage,
    DivisionMode,
    ExecutionStrategy,
    FoodIntake,
    GameteRecord,
    Genome,
    GenomeModule,
    LifecycleState,
    MaintenanceJobRun,
    MembraneDecision,
    MembraneDecisionAction,
    MemoryRecord,
    MisfoldingType,
    OrganRecord,
    OrganellePipeline,
    OrganismRecord,
    OxygenProfile,
    Protein,
    ProteinStatus,
    ReplayRun,
    ReviewRequest,
    DivisionReadinessResult,
    GateResult,
    RuntimeAlert,
    RuntimeEvent,
    RuntimeEventType,
    Signal,
    SoulSnapshot,
    StructureProposal,
    StructureRequest,
    TissueRecord,
    UmbilicalCord,
    ValidationReport,
    VesicleMessage,
    ZygoteGenome,
    ZygoteRecord,
    GenomeVersion,
    PolicySet,
    PolicyVersion,
    RecordStatus,
    utc_now,
)


ENGINE_VERSION = "1.0.0-organism"


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


@dataclass
class RuntimeStores:
    organisms: dict[str, OrganismRecord] = field(default_factory=dict)
    genomes: dict[str, Genome] = field(default_factory=dict)
    cells: dict[str, list[CellRecord]] = field(default_factory=dict)
    signals: dict[str, list[Signal]] = field(default_factory=dict)
    proteins: dict[str, list[Protein]] = field(default_factory=dict)
    contracts: dict[str, Contract] = field(default_factory=dict)
    events: dict[str, list[RuntimeEvent]] = field(default_factory=dict)
    structure_requests: dict[str, list[StructureRequest]] = field(default_factory=dict)
    memory_records: dict[str, list[MemoryRecord]] = field(default_factory=dict)
    capabilities: dict[str, Capability] = field(default_factory=dict)
    genome_versions: dict[str, list[GenomeVersion]] = field(default_factory=dict)
    replay_runs: dict[str, ReplayRun] = field(default_factory=dict)
    policy_versions: dict[str, list[PolicyVersion]] = field(default_factory=dict)
    maintenance_runs: list[MaintenanceJobRun] = field(default_factory=list)
    alerts: dict[str, RuntimeAlert] = field(default_factory=dict)
    reviews: dict[str, ReviewRequest] = field(default_factory=dict)
    zygotes: dict[str, ZygoteRecord] = field(default_factory=dict)
    organs: dict[str, list[OrganRecord]] = field(default_factory=dict)
    tissues: dict[str, list[TissueRecord]] = field(default_factory=dict)
    cell_divisions: dict[str, list[CellDivisionRecord]] = field(default_factory=dict)
    food_intakes: dict[str, list[FoodIntake]] = field(default_factory=dict)
    oxygen_profiles: dict[str, OxygenProfile] = field(default_factory=dict)
    umbilical_cords: dict[str, UmbilicalCord] = field(default_factory=dict)
    souls: dict[str, SoulSnapshot] = field(default_factory=dict)
    bone_structures: dict[str, BoneStructureRecord] = field(default_factory=dict)
    structure_proposals: dict[str, StructureProposal] = field(default_factory=dict)
    organelle_pipelines: dict[str, list[OrganellePipeline]] = field(default_factory=dict)
    vesicle_messages: dict[str, list[VesicleMessage]] = field(default_factory=dict)
    cytoskeleton: dict[str, CytoskeletonTopology] = field(default_factory=dict)
    actor_counts: dict[tuple[str, str], int] = field(default_factory=dict)


def runtime_event(
    event_type: RuntimeEventType,
    message: str,
    *,
    organism_id: str | None = None,
    cell_id: str | None = None,
    signal_id: str | None = None,
    protein_id: str | None = None,
    contract_id: str | None = None,
    **values: object,
) -> RuntimeEvent:
    return RuntimeEvent(
        event_id=new_id("event"),
        organism_id=organism_id,
        cell_id=cell_id,
        signal_id=signal_id,
        protein_id=protein_id,
        contract_id=contract_id,
        type=event_type,
        message=message,
        values=dict(values),
    )


class Membrane:
    def __init__(self, stores: RuntimeStores) -> None:
        self.stores = stores

    def admit(self, organism: OrganismRecord, genome: Genome, signal: Signal) -> MembraneDecision:
        count_key = (organism.organism_id, signal.actor.actor_id)
        self.stores.actor_counts[count_key] = self.stores.actor_counts.get(count_key, 0) + 1
        if self.stores.actor_counts[count_key] > organism.policies.rate_limit_per_actor:
            return MembraneDecision(action=MembraneDecisionAction.REJECT, code="RATE_LIMITED", reason="Actor exceeded membrane rate limit")
        if not signal.actor.actor_id:
            return MembraneDecision(action=MembraneDecisionAction.REJECT, code="UNAUTHENTICATED", reason="Signal actor is not authenticated")
        if signal.type not in organism.policies.allowed_signal_types:
            return MembraneDecision(action=MembraneDecisionAction.REJECT, code="WRONG_CELL_TYPE", reason="Signal type is outside organism policy")
        if not any(signal.type in module.signal_types for module in genome.modules):
            return MembraneDecision(action=MembraneDecisionAction.REJECT, code="IRRELEVANT_SIGNAL", reason="No expressed genome module can process this signal")
        if not set(organism.policies.required_roles).intersection(signal.actor.roles):
            return MembraneDecision(action=MembraneDecisionAction.REJECT, code="UNAUTHORIZED", reason="Actor lacks required role")
        text = str(signal.payload).lower()
        if any(term in text for term in organism.policies.forbidden_terms):
            return MembraneDecision(action=MembraneDecisionAction.REJECT, code="UNSAFE_INPUT", reason="Signal failed safety filter")
        if signal.type == "calculate" and "expression" not in signal.payload:
            return MembraneDecision(action=MembraneDecisionAction.REJECT, code="INVALID_STRUCTURE", reason="Calculate signal requires expression")
        if signal.type == "contract.call" and ("contract" not in signal.payload or "action" not in signal.payload):
            return MembraneDecision(action=MembraneDecisionAction.REJECT, code="INVALID_STRUCTURE", reason="Contract call requires contract and action")
        return MembraneDecision(action=MembraneDecisionAction.ACCEPT, code="ACCEPTED", reason="Signal admitted through membrane")


class Cytoplasm:
    def __init__(self, stores: RuntimeStores) -> None:
        self.stores = stores

    def select_cell(self, organism_id: str, signal: Signal, genome: Genome) -> tuple[CellRecord, list[dict[str, object]]]:
        cells = self.stores.cells.setdefault(organism_id, [])
        if not cells:
            cells.append(CellRecord(cell_id=new_id("cell"), organism_id=organism_id))
        candidates: list[tuple[float, CellRecord]] = []
        skipped: list[dict[str, object]] = []
        relevant_modules = [module for module in genome.modules if signal.type in module.signal_types]
        for cell in cells:
            if cell.resource_budget.compute_units < 1:
                skipped.append({"cell_id": cell.cell_id, "reason": "compute_exhausted"})
                continue
            score = max(
                (
                    cell.expression_profile.get(module.module_id, 0.0)
                    + cell.expression_profile.get(module.deterministic_tool or "", 0.0)
                    for module in relevant_modules
                ),
                default=cell.expression_profile.get(signal.type, 0.0),
            )
            tissue_bonus = 0.1 if cell.tissue_id in signal.context_refs else 0.0
            priority_bonus = signal.priority / 100
            candidates.append((score + tissue_bonus + priority_bonus, cell))
        if not candidates:
            cell = cells[0]
            skipped.append({"cell_id": cell.cell_id, "reason": "fallback_no_available_budget"})
        else:
            cell = max(candidates, key=lambda item: (item[0], item[1].last_active_at is None))[1]
        updated = cell.model_copy(update={"lifecycle_state": LifecycleState.ACTIVE, "last_active_at": utc_now()})
        self.stores.cells[organism_id] = [updated if item.cell_id == cell.cell_id else item for item in cells]
        return updated, skipped


_MATH_EXPR_RE = re.compile(r"^\s*[\d\s\.\+\-\*/\(\)\^%]+\s*$")
_DECOMPOSE_RE = re.compile(r"\b(plan|steps?\s+to|how\s+do\s+i|first\s+.{1,40}\s+then|break\s*down|decompose|sub.?tasks?)\b", re.I)


class SignalClassifier:
    """Rule-based signal type classifier — no LLM required.

    Reclassifies ambiguous `query` signals based on payload heuristics so the
    nucleus can route them to the right module without burning LLM tokens.
    Only applies to type="query"; all other types are returned unchanged.
    """

    def reclassify(self, signal: Signal) -> str:
        if signal.type != "query":
            return signal.type

        prompt = signal.payload.get("prompt", "")
        if not isinstance(prompt, str):
            return signal.type

        # Explicit expression key takes priority
        expr = signal.payload.get("expression")
        if expr is not None and _MATH_EXPR_RE.match(str(expr)):
            return "calculate"

        # Pure math in the prompt text
        if _MATH_EXPR_RE.match(prompt):
            return "calculate"

        # Decomposition / planning language
        if _DECOMPOSE_RE.search(prompt):
            return "task.plan"

        return "query"


class Nucleus:
    def __init__(self, classifier: SignalClassifier | None = None) -> None:
        self._classifier = classifier or SignalClassifier()

    def select_module(self, genome: Genome, cell: CellRecord, signal: Signal) -> GenomeModule:
        effective_type = self._classifier.reclassify(signal)
        candidates = [module for module in genome.modules if effective_type in module.signal_types]
        if not candidates:
            # fall back to original type before giving up
            candidates = [module for module in genome.modules if signal.type in module.signal_types]
        if not candidates:
            return genome.modules[0]
        disabled = {
            str(rule.get("module_id"))
            for rule in genome.regulatory_rules
            if rule.get("signal_type") == effective_type and rule.get("enabled") is False
        }
        candidates = [module for module in candidates if module.module_id not in disabled] or candidates
        return max(
            candidates,
            key=lambda module: (
                cell.expression_profile.get(module.module_id, 0.0),
                cell.expression_profile.get(module.deterministic_tool or "", 0.0),
                -candidates.index(module),
            ),
        )


class Mitochondria:
    def __init__(self, stores: RuntimeStores) -> None:
        self.stores = stores

    def reserve(self, cell: CellRecord, module: GenomeModule) -> tuple[CellRecord, bool, dict[str, int]]:
        requires_tool = module.execution_strategy == ExecutionStrategy.DETERMINISTIC_TOOL
        if cell.resource_budget.compute_units < 1 or (requires_tool and cell.resource_budget.tool_calls < 1):
            return cell, False, {
                "compute_units": cell.resource_budget.compute_units,
                "tool_calls": cell.resource_budget.tool_calls,
            }
        budget = cell.resource_budget.model_copy(
            update={
                "compute_units": cell.resource_budget.compute_units - 1,
                "tool_calls": cell.resource_budget.tool_calls - (1 if requires_tool else 0),
            }
        )
        updated = cell.model_copy(update={"resource_budget": budget, "last_active_at": utc_now()})
        cells = self.stores.cells.get(cell.organism_id, [])
        self.stores.cells[cell.organism_id] = [updated if item.cell_id == cell.cell_id else item for item in cells]
        return updated, True, {"compute_units": budget.compute_units, "tool_calls": budget.tool_calls}


class Skeleton:
    def __init__(self, stores: RuntimeStores) -> None:
        self.stores = stores

    def create_contract(self, contract: Contract) -> Contract:
        self.stores.contracts[contract.contract_id] = contract
        return contract

    def deprecate_contract(self, contract_id: str, reason: str = "Deprecated by osteoclast") -> Contract:
        contract = self.stores.contracts[contract_id]
        dependents = [
            item.contract_id
            for item in self.stores.contracts.values()
            if item.status == ContractStatus.ACTIVE and contract_id in item.dependencies
        ]
        if contract.usage_count > 0 or dependents:
            raise ValueError("contract has active dependencies")
        contract = contract.model_copy(
            update={"status": ContractStatus.DEPRECATED, "deprecated_reason": reason, "updated_at": utc_now()}
        )
        self.stores.contracts[contract_id] = contract
        return contract

    def evaluate_contract_call(self, signal: Signal) -> tuple[StructureRequest | None, Protein | None, str | None]:
        if signal.type != "contract.call":
            return None, None, None
        contract_name = str(signal.payload.get("contract", ""))
        action = str(signal.payload.get("action", ""))
        contract = next(
            (
                item
                for item in self.stores.contracts.values()
                if item.name == contract_name
                and item.status == ContractStatus.ACTIVE
                and (item.owner_user_id in {None, signal.actor.actor_id})
            ),
            None,
        )
        if contract is None:
            return (
                StructureRequest(
                    request_id=new_id("structure"),
                    organism_id=signal.organism_id,
                    signal_id=signal.signal_id,
                    requested_contract=contract_name or "unknown",
                    reason="No active contract exists for requested infrastructure access",
                ),
                None,
                None,
            )
        missing_dependency = next((dep for dep in contract.dependencies if dep not in self.stores.contracts), None)
        if missing_dependency is not None:
            return (
                StructureRequest(
                    request_id=new_id("structure"),
                    organism_id=signal.organism_id,
                    signal_id=signal.signal_id,
                    requested_contract=missing_dependency,
                    reason=f"Contract dependency {missing_dependency} is not registered",
                ),
                None,
                contract.contract_id,
            )
        if contract.allowed_actions and action not in contract.allowed_actions:
            return None, self._contract_error(signal, "semantic", f"Action {action} is not allowed by contract"), contract.contract_id
        if not set(contract.permissions).intersection(signal.actor.roles):
            return None, self._contract_error(signal, "context", "Actor lacks contract permission"), contract.contract_id
        self.stores.contracts[contract.contract_id] = contract.model_copy(update={"usage_count": contract.usage_count + 1, "updated_at": utc_now()})
        return None, None, contract.contract_id

    def resolve_structure_request(self, request: StructureRequest, contract_id: str | None = None) -> StructureRequest:
        updated = request.model_copy(
            update={
                "status": "resolved",
                "reason": f"Resolved by contract {contract_id}" if contract_id else "Resolved by operator",
            }
        )
        self._replace_structure_request(updated)
        return updated

    def block_structure_request(self, request: StructureRequest, reason: str) -> StructureRequest:
        updated = request.model_copy(update={"status": "blocked", "reason": reason})
        self._replace_structure_request(updated)
        return updated

    def _replace_structure_request(self, request: StructureRequest) -> None:
        requests = self.stores.structure_requests.get(request.organism_id, [])
        self.stores.structure_requests[request.organism_id] = [
            request if item.request_id == request.request_id else item for item in requests
        ]

    def _contract_error(self, signal: Signal, misfolding: str, message: str) -> Protein:
        misfolding_type = MisfoldingType(misfolding)
        return Protein(
            protein_id=new_id("protein"),
            organism_id=signal.organism_id,
            source_signal_id=signal.signal_id,
            type="contract_call.error",
            payload={"error": message},
            confidence=0.0,
            validation_report=ValidationReport(valid=False, errors=[message], misfolding_types=[misfolding_type]),
        )


class Ribosome:
    def execute(self, module: GenomeModule, signal: Signal) -> Protein:
        try:
            if module.execution_strategy == ExecutionStrategy.PRECOMPUTED:
                payload = {"result": "pong"} if signal.payload.get("message") == "ping" else {"result": signal.payload}
            elif module.deterministic_tool == "calculator":
                payload = {"result": safe_calculate(str(signal.payload["expression"])), "method": "deterministic_calculator"}
            elif module.deterministic_tool == "contract_gateway":
                payload = {"result": "contract_call_prepared", "contract": signal.payload.get("contract"), "action": signal.payload.get("action")}
            elif module.execution_strategy == ExecutionStrategy.LLM:
                payload = self._llm_execute(module, signal)
            else:
                payload = {"result": f"llm_stub:{signal.payload.get('prompt') or signal.payload}", "method": "llm_stub"}
        except Exception as exc:
            payload = {"error": str(exc)}
        live = module.execution_strategy == ExecutionStrategy.LLM and "method" in payload and payload.get("method") != "llm_stub"
        return Protein(
            protein_id=new_id("protein"),
            organism_id=signal.organism_id,
            source_signal_id=signal.signal_id,
            type=f"{module.module_id}.result",
            payload=payload,
            confidence=0.95 if module.execution_strategy == ExecutionStrategy.DETERMINISTIC_TOOL else (0.85 if live else 0.75),
        )

    def _llm_execute(self, module: GenomeModule, signal: Signal) -> dict:
        from preon_systems_cell.llm_providers import get_adapter

        provider = module.llm_provider or "anthropic"
        model_class = module.llm_model_class or "standard"
        adapter = get_adapter(str(provider), str(model_class), module.llm_model_id)

        prompt = signal.payload.get("prompt") or str(signal.payload)
        if adapter is None:
            return {"result": f"llm_stub:{prompt}", "method": "llm_stub", "provider": str(provider)}

        result = adapter.complete(prompt)
        return {"result": result, "method": "llm", "provider": str(provider), "model_class": str(model_class)}


class ProteinPipeline:
    def validate(self, protein: Protein, signal: Signal) -> Protein:
        if not protein.validation_report.valid and protein.validation_report.misfolding_types:
            status = (
                ProteinStatus.BLOCKED
                if MisfoldingType.TOXIC in protein.validation_report.misfolding_types
                else ProteinStatus.DROPPED
            )
            return protein.model_copy(update={"status": status})
        errors: list[str] = []
        misfolding_types: list[MisfoldingType] = []
        payload_text = str(protein.payload).lower()
        if not protein.payload:
            errors.append("protein payload is empty")
            misfolding_types.append(MisfoldingType.STRUCTURAL)
        if "error" in protein.payload:
            errors.append(str(protein.payload["error"]))
            misfolding_types.append(MisfoldingType.EXECUTION)
        if signal.type == "calculate" and "result" not in protein.payload:
            errors.append("calculation protein is missing result")
            misfolding_types.append(MisfoldingType.STRUCTURAL)
        if signal.type == "calculate" and "result" in protein.payload and not isinstance(protein.payload["result"], (int, float)):
            try:
                repaired_payload = protein.payload | {"result": float(protein.payload["result"])}
                return protein.model_copy(
                    update={
                        "payload": repaired_payload,
                        "status": ProteinStatus.REPAIRED,
                        "validation_report": ValidationReport(valid=True, repaired=True),
                    }
                )
            except (TypeError, ValueError):
                errors.append("calculation result is not numeric")
                misfolding_types.append(MisfoldingType.SEMANTIC)
        if "delete all" in payload_text or "exfiltrate" in payload_text or "bypass policy" in payload_text:
            errors.append("protein is toxic")
            misfolding_types.append(MisfoldingType.TOXIC)
        deduped = list(dict.fromkeys(misfolding_types))
        if MisfoldingType.TOXIC in deduped:
            status = ProteinStatus.BLOCKED
        elif errors:
            status = ProteinStatus.DROPPED
        else:
            status = ProteinStatus.APPROVED
        return protein.model_copy(
            update={
                "status": status,
                "validation_report": ValidationReport(valid=not errors, errors=errors, misfolding_types=deduped),
            }
        )


class OrganismRuntime:
    def __init__(self, stores: RuntimeStores | None = None) -> None:
        self.stores = stores or RuntimeStores()
        default = Genome(genome_id="genome-default")
        self.stores.genomes.setdefault(default.genome_id, default)
        self._bind_services()

    def _bind_services(self) -> None:
        self.membrane = Membrane(self.stores)
        self.cytoplasm = Cytoplasm(self.stores)
        self.nucleus = Nucleus()
        self.mitochondria = Mitochondria(self.stores)
        self.skeleton = Skeleton(self.stores)
        self.ribosome = Ribosome()
        self.protein_pipeline = ProteinPipeline()

    def create_organism(self, organism: OrganismRecord) -> OrganismRecord:
        self.stores.organisms[organism.organism_id] = organism
        self.stores.cells[organism.organism_id] = [
            CellRecord(cell_id=new_id("cell"), organism_id=organism.organism_id, lifecycle_state=LifecycleState.HIBERNATED)
        ]
        self._append_event(
            runtime_event(RuntimeEventType.ORGANISM_CREATED, "Organism identity created", organism_id=organism.organism_id)
        )
        return organism

    def wake(self, organism_id: str) -> OrganismRecord:
        organism = self._organism(organism_id)
        organism = organism.model_copy(update={"lifecycle_state": LifecycleState.ACTIVE, "updated_at": utc_now()})
        self.stores.organisms[organism_id] = organism
        cells = [
            cell.model_copy(update={"lifecycle_state": LifecycleState.ACTIVE, "last_active_at": utc_now()})
            for cell in self.stores.cells.get(organism_id, [])
        ]
        self.stores.cells[organism_id] = cells
        self._append_event(runtime_event(RuntimeEventType.LIFECYCLE, "Organism woke from hibernation", organism_id=organism_id))
        return organism

    def hibernate(self, organism_id: str) -> OrganismRecord:
        organism = self._organism(organism_id)
        snapshot = {
            "cells": [cell.model_dump(mode="json") for cell in self.stores.cells.get(organism_id, [])],
            "protein_count": len(self.stores.proteins.get(organism_id, [])),
        }
        organism = organism.model_copy(
            update={"lifecycle_state": LifecycleState.HIBERNATED, "last_state_snapshot": snapshot, "updated_at": utc_now()}
        )
        self.stores.organisms[organism_id] = organism
        self.stores.cells[organism_id] = [
            cell.model_copy(update={"lifecycle_state": LifecycleState.HIBERNATED}) for cell in self.stores.cells.get(organism_id, [])
        ]
        self._append_event(runtime_event(RuntimeEventType.LIFECYCLE, "Organism checkpointed and hibernated", organism_id=organism_id))
        return organism

    def create_contract(self, contract: Contract) -> Contract:
        self.skeleton.create_contract(contract)
        self._append_event(
            runtime_event(
                RuntimeEventType.SKELETON,
                "Osteoblast registered contract",
                contract_id=contract.contract_id,
                name=contract.name,
                capability_ids=contract.capability_ids,
                adapter_id=contract.adapter_id,
            )
        )
        return contract

    def deprecate_contract(self, contract_id: str) -> Contract:
        contract = self.skeleton.deprecate_contract(contract_id)
        self._append_event(runtime_event(RuntimeEventType.SKELETON, "Osteoclast deprecated contract", contract_id=contract_id))
        return contract

    def create_cell(self, cell: CellRecord) -> CellRecord:
        self.stores.cells.setdefault(cell.organism_id, []).append(cell)
        self._append_event(
            runtime_event(
                RuntimeEventType.CYTOPLASM,
                "Cell created for tissue runtime",
                organism_id=cell.organism_id,
                cell_id=cell.cell_id,
                tissue_id=cell.tissue_id,
                cell_type=cell.cell_type,
            )
        )
        return cell

    def update_cell(self, cell: CellRecord) -> CellRecord:
        cells = self.stores.cells.setdefault(cell.organism_id, [])
        self.stores.cells[cell.organism_id] = [cell if item.cell_id == cell.cell_id else item for item in cells]
        self._append_event(
            runtime_event(
                RuntimeEventType.CYTOPLASM,
                "Cell updated",
                organism_id=cell.organism_id,
                cell_id=cell.cell_id,
                tissue_id=cell.tissue_id,
                cell_type=cell.cell_type,
            )
        )
        return cell

    def hibernate_cell(self, organism_id: str, cell_id: str) -> CellRecord:
        cell = self._cell(organism_id, cell_id).model_copy(update={"lifecycle_state": LifecycleState.HIBERNATED})
        self.update_cell(cell)
        self._append_event(runtime_event(RuntimeEventType.LIFECYCLE, "Cell hibernated", organism_id=organism_id, cell_id=cell_id))
        return cell

    def create_memory(self, memory: MemoryRecord) -> MemoryRecord:
        self.stores.memory_records.setdefault(memory.organism_id, []).append(memory)
        self._append_event(
            runtime_event(
                RuntimeEventType.MEMORY,
                "Memory record created",
                organism_id=memory.organism_id,
                memory_id=memory.memory_id,
                kind=memory.kind,
                scope=memory.scope,
            )
        )
        return memory

    def deprecate_memory(self, organism_id: str, memory_id: str) -> MemoryRecord:
        memory = self._memory(organism_id, memory_id).model_copy(update={"status": RecordStatus.DEPRECATED, "updated_at": utc_now()})
        memories = self.stores.memory_records.get(organism_id, [])
        self.stores.memory_records[organism_id] = [memory if item.memory_id == memory_id else item for item in memories]
        self._append_event(runtime_event(RuntimeEventType.MEMORY, "Memory record deprecated", organism_id=organism_id, memory_id=memory_id))
        return memory

    def recall_memory(self, signal: Signal) -> list[MemoryRecord]:
        memories = self.stores.memory_records.get(signal.organism_id, [])
        recalled = [
            memory
            for memory in memories
            if memory.status == RecordStatus.ACTIVE
            and (
                memory.kind == signal.type
                or memory.scope in signal.context_refs
                or any(ref in str(memory.payload) for ref in signal.context_refs)
            )
        ]
        return recalled[:5]

    def write_memory_from_protein(self, signal: Signal, protein: Protein) -> MemoryRecord | None:
        if protein.status not in {ProteinStatus.APPROVED, ProteinStatus.REPAIRED}:
            return None
        memory = MemoryRecord(
            memory_id=new_id("memory"),
            organism_id=signal.organism_id,
            scope="organism",
            kind=signal.type,
            payload={"protein_type": protein.type, "payload": protein.payload},
            source_signal_id=signal.signal_id,
            confidence=protein.confidence,
        )
        self.stores.memory_records.setdefault(signal.organism_id, []).append(memory)
        return memory

    def create_capability(self, capability: Capability) -> Capability:
        self.stores.capabilities[capability.capability_id] = capability
        self._append_event(
            runtime_event(
                RuntimeEventType.SKELETON,
                "Capability registered",
                contract_id=None,
                capability_id=capability.capability_id,
                name=capability.name,
            )
        )
        return capability

    def validate_contract_adapter(self, contract_id: str) -> ValidationReport:
        contract = self.stores.contracts[contract_id]
        errors: list[str] = []
        missing = [capability_id for capability_id in contract.capability_ids if capability_id not in self.stores.capabilities]
        if missing:
            errors.append(f"missing capabilities: {', '.join(missing)}")
        if contract.adapter_id and not contract.input_mapping:
            errors.append("adapter requires input_mapping")
        for vector in contract.test_vectors:
            if not isinstance(vector.get("input", {}), dict):
                errors.append("test vector input must be an object")
            if "expected" in vector and not isinstance(vector["expected"], dict):
                errors.append("test vector expected must be an object")
        report = ValidationReport(valid=not errors, errors=errors)
        self._append_event(
            runtime_event(
                RuntimeEventType.SKELETON,
                "Contract adapter validated",
                contract_id=contract_id,
                valid=report.valid,
                errors=report.errors,
            )
        )
        return report

    def test_contract_adapter(self, contract_id: str, payload: dict[str, object]) -> dict[str, object]:
        contract = self.stores.contracts[contract_id]
        mapped = self._map_payload(payload, contract.input_mapping)
        output = self._map_payload(mapped, contract.output_mapping) if contract.output_mapping else mapped
        result = {"input": payload, "mapped_input": mapped, "output": output}
        self._append_event(runtime_event(RuntimeEventType.SKELETON, "Contract adapter test executed", contract_id=contract_id, result=result))
        return result

    def replay_signal(self, organism_id: str, signal_id: str) -> ReplayRun:
        signal = next(item for item in self.stores.signals.get(organism_id, []) if item.signal_id == signal_id)
        original_protein = next(
            (protein for protein in reversed(self.stores.proteins.get(organism_id, [])) if protein.source_signal_id == signal_id),
            None,
        )
        cloned = deepcopy(self.stores)
        replay_runtime = OrganismRuntime(cloned)
        decision, _cell, replay_protein, events, _structure = replay_runtime.submit_signal(signal)
        divergence = {
            "membrane_match": decision.action == MembraneDecisionAction.ACCEPT,
            "protein_payload_match": (original_protein.payload if original_protein else None) == (replay_protein.payload if replay_protein else None),
            "protein_status_match": (original_protein.status if original_protein else None) == (replay_protein.status if replay_protein else None),
        }
        replay = ReplayRun(
            replay_id=new_id("replay"),
            organism_id=organism_id,
            signal_id=signal_id,
            original_protein=original_protein,
            replay_protein=replay_protein,
            events=events,
            divergence_report=divergence,
        )
        self.stores.replay_runs[replay.replay_id] = replay
        self._append_event(runtime_event(RuntimeEventType.REPLAY, "Signal replay completed", organism_id=organism_id, signal_id=signal_id, replay_id=replay.replay_id, divergence_report=divergence))
        return replay

    def validate_policy(self, policies: PolicySet) -> ValidationReport:
        errors: list[str] = []
        if not policies.allowed_signal_types:
            errors.append("allowed_signal_types cannot be empty")
        if not policies.required_roles:
            errors.append("required_roles cannot be empty")
        if policies.rate_limit_per_actor < 1:
            errors.append("rate_limit_per_actor must be positive")
        return ValidationReport(valid=not errors, errors=errors)

    def update_policy(self, organism_id: str, policies: PolicySet, created_by: str | None = None) -> PolicyVersion:
        organism = self._organism(organism_id)
        current_versions = self.stores.policy_versions.setdefault(organism_id, [])
        self.stores.policy_versions[organism_id] = [version.model_copy(update={"status": "superseded"}) for version in current_versions]
        updated = organism.model_copy(update={"policies": policies, "updated_at": utc_now()})
        self.stores.organisms[organism_id] = updated
        version = PolicyVersion(
            policy_version_id=new_id("policy"),
            organism_id=organism_id,
            version=len(current_versions) + 1,
            policies=policies,
            created_by=created_by,
        )
        self.stores.policy_versions[organism_id].append(version)
        self._append_event(runtime_event(RuntimeEventType.POLICY, "Policy version activated", organism_id=organism_id, version=version.version))
        return version

    def simulate_policy(self, organism_id: str, policies: PolicySet, signal: Signal) -> MembraneDecision:
        organism = self._organism(organism_id).model_copy(update={"policies": policies})
        decision = Membrane(RuntimeStores(actor_counts=dict(self.stores.actor_counts))).admit(
            organism,
            self.stores.genomes[organism.genome_id],
            signal,
        )
        self._append_event(runtime_event(RuntimeEventType.POLICY, "Policy admission simulation completed", organism_id=organism_id, signal_type=signal.type, decision=decision.model_dump(mode="json")))
        return decision

    def create_genome_version(self, genome: Genome, owner_user_id: str | None = None) -> GenomeVersion:
        versions = self.stores.genome_versions.setdefault(genome.genome_id, [])
        version = GenomeVersion(
            version_id=new_id("genver"),
            genome_id=genome.genome_id,
            owner_user_id=owner_user_id,
            version=len(versions) + 1,
            genome=genome,
        )
        versions.append(version)
        self._append_event(runtime_event(RuntimeEventType.GENOME, "Genome version created", genome_id=genome.genome_id, version=version.version))
        return version

    def activate_genome_version(self, genome_id: str, version: int) -> GenomeVersion:
        versions = self.stores.genome_versions.get(genome_id, [])
        selected = next(item for item in versions if item.version == version)
        self.stores.genome_versions[genome_id] = [
            item.model_copy(update={"status": "deprecated"}) if item.status == "active" else item for item in versions
        ]
        selected = selected.model_copy(update={"status": "active", "activated_at": utc_now()})
        self.stores.genome_versions[genome_id] = [selected if item.version_id == selected.version_id else item for item in self.stores.genome_versions[genome_id]]
        self.stores.genomes[genome_id] = selected.genome
        self._append_event(runtime_event(RuntimeEventType.GENOME, "Genome version activated", genome_id=genome_id, version=version))
        return selected

    def preview_genome(self, organism_id: str, signal: Signal, cell_id: str | None = None) -> dict[str, object]:
        organism = self._organism(organism_id)
        genome = self.stores.genomes[organism.genome_id]
        cell = self._cell(organism_id, cell_id) if cell_id else self.stores.cells[organism_id][0]
        module = self.nucleus.select_module(genome, cell, signal)
        result = {"cell_id": cell.cell_id, "module_id": module.module_id, "strategy": module.execution_strategy.value}
        self._append_event(runtime_event(RuntimeEventType.GENOME, "Genome expression preview completed", organism_id=organism_id, result=result))
        return result

    def run_maintenance(self) -> MaintenanceJobRun:
        open_requests = [
            request.model_dump(mode="json")
            for requests in self.stores.structure_requests.values()
            for request in requests
            if request.status == "open"
        ]
        stale_contracts = [
            contract.contract_id for contract in self.stores.contracts.values() if contract.status == ContractStatus.ACTIVE and contract.usage_count == 0
        ]
        results = {
            "open_structure_requests": len(open_requests),
            "stale_contracts": stale_contracts,
            "event_count": sum(len(events) for events in self.stores.events.values()),
            "memory_count": sum(len(records) for records in self.stores.memory_records.values()),
        }
        run = MaintenanceJobRun(run_id=new_id("maint"), results=results)
        self.stores.maintenance_runs.append(run)
        self._append_event(runtime_event(RuntimeEventType.MAINTENANCE, "Maintenance run completed", **results))
        if open_requests:
            self.create_alert(None, "warning", "structure_requests", f"{len(open_requests)} open structure requests")
        return run

    def runtime_metrics(self, organism_id: str | None = None) -> dict[str, object]:
        events = []
        if organism_id:
            events = self.stores.events.get(organism_id, [])
        else:
            for organism_events in self.stores.events.values():
                events.extend(organism_events)
        proteins = self.stores.proteins.get(organism_id, []) if organism_id else [protein for values in self.stores.proteins.values() for protein in values]
        return {
            "events": len(events),
            "signals": len(self.stores.signals.get(organism_id, [])) if organism_id else sum(len(items) for items in self.stores.signals.values()),
            "proteins": len(proteins),
            "protein_statuses": {status.value: sum(1 for protein in proteins if protein.status == status) for status in ProteinStatus},
            "alerts": len([alert for alert in self.stores.alerts.values() if alert.status == "active" and (organism_id is None or alert.organism_id == organism_id)]),
            "structure_requests": len(self.stores.structure_requests.get(organism_id, [])) if organism_id else sum(len(items) for items in self.stores.structure_requests.values()),
        }

    def create_alert(self, organism_id: str | None, severity: str, source: str, reason: str) -> RuntimeAlert:
        alert = RuntimeAlert(alert_id=new_id("alert"), organism_id=organism_id, severity=severity, source=source, reason=reason)
        self.stores.alerts[alert.alert_id] = alert
        self._append_event(runtime_event(RuntimeEventType.ALERT, "Runtime alert created", organism_id=organism_id, alert_id=alert.alert_id, severity=severity, source=source, reason=reason))
        return alert

    def export_organism(self, organism_id: str) -> dict[str, object]:
        organism = self._organism(organism_id)
        return {
            "organism": organism.model_dump(mode="json"),
            "cells": [cell.model_dump(mode="json") for cell in self.stores.cells.get(organism_id, [])],
            "genome": self.stores.genomes[organism.genome_id].model_dump(mode="json"),
            "contracts": [contract.model_dump(mode="json") for contract in self.stores.contracts.values() if contract.owner_user_id in {None, organism.owner_user_id}],
            "memory_records": [memory.model_dump(mode="json") for memory in self.stores.memory_records.get(organism_id, [])],
            "structure_requests": [request.model_dump(mode="json") for request in self.stores.structure_requests.get(organism_id, [])],
            "events": [event.model_dump(mode="json") for event in self.stores.events.get(organism_id, [])[-100:]],
            "proteins": [protein.model_dump(mode="json") for protein in self.stores.proteins.get(organism_id, [])],
        }

    def debug_bundle(self, organism_id: str) -> dict[str, object]:
        bundle = self.export_organism(organism_id)
        bundle["redaction"] = {"auth": "excluded", "sessions": "excluded", "tokens": "excluded"}
        return bundle

    def growth_template(self) -> dict[str, dict[str, object]]:
        return {
            "brain": {"name": "Brain", "tissues": {"brain-tissue-1": 2, "brain-tissue-2": 2, "brain-tissue-3": 1}},
            "heart": {"name": "Heart", "tissues": {"heart-tissue-1": 2, "heart-tissue-2": 2, "heart-tissue-3": 1}},
            "left-arm": {"name": "Left Arm", "tissues": {"left-arm-tissue-1": 2, "left-arm-tissue-2": 1}},
            "right-arm": {"name": "Right Arm", "tissues": {"right-arm-tissue-1": 2, "right-arm-tissue-2": 1}},
            "left-leg": {"name": "Left Leg", "tissues": {"left-leg-tissue-1": 2, "left-leg-tissue-2": 1}},
            "right-leg": {"name": "Right Leg", "tissues": {"right-leg-tissue-1": 2, "right-leg-tissue-2": 1}},
        }

    def negotiate_reproduction(self, mother_organism_id: str, father_organism_id: str) -> dict[str, object]:
        mother = self._organism(mother_organism_id)
        father = self._organism(father_organism_id)
        report = {
            "mother": {
                "organism_id": mother.organism_id,
                "score": 0.7 + min(len(mother.long_term_memory), 3) * 0.05,
                "emphasis": ["memory", "environment", "safety", "infrastructure"],
            },
            "father": {
                "organism_id": father.organism_id,
                "score": 0.7 + min(len(father.goals), 3) * 0.05,
                "emphasis": ["reasoning", "optimization", "exploration", "mutation"],
            },
            "selected": True,
        }
        self._append_event(
            runtime_event(
                RuntimeEventType.REPRODUCTION,
                "Reproduction negotiation completed",
                mother_organism_id=mother.organism_id,
                father_organism_id=father.organism_id,
                report=report,
            )
        )
        return report

    def create_zygote(self, mother_organism_id: str, father_organism_id: str, owner_user_id: str | None = None) -> ZygoteRecord:
        mother = self._organism(mother_organism_id)
        father = self._organism(father_organism_id)
        mother_gamete = GameteRecord(
            gamete_id=new_id("gamete"),
            source_organism_id=mother.organism_id,
            role="mother",
            emphasis=["memory", "environment", "safety", "infrastructure"],
            projection={
                "identity": mother.identity_profile.model_dump(mode="json"),
                "memory": mother.long_term_memory,
                "policies": mother.policies.model_dump(mode="json"),
            },
        )
        father_gamete = GameteRecord(
            gamete_id=new_id("gamete"),
            source_organism_id=father.organism_id,
            role="father",
            emphasis=["reasoning", "optimization", "exploration", "mutation"],
            projection={
                "identity": father.identity_profile.model_dump(mode="json"),
                "goals": father.goals,
                "genome_id": father.genome_id,
            },
        )
        template = self.growth_template()
        organ_cell_dna = {
            organ_id: {
                "organ": organ["name"],
                "cell_genome_id": f"{organ_id}-cell-genome",
                "tissues": organ["tissues"],
                "organelles": [
                    "nucleus",
                    "mitochondria",
                    "er",
                    "golgi",
                    "vesicles",
                    "cytoplasm",
                    "membrane",
                    "peroxisome",
                    "vacuole",
                    "lysosome",
                ],
            }
            for organ_id, organ in template.items()
        }
        genome = ZygoteGenome(
            genome_id=new_id("zygote-genome"),
            zygote_dna={"division_rule": "copy_genome_and_duplicate_organelles", "oxygen": "restricted_until_birth"},
            organ_cell_dna=organ_cell_dna,
            mother_gamete=mother_gamete,
            father_gamete=father_gamete,
            merge_report={"strategy": "structured_merge", "deterministic": True},
        )
        zygote = ZygoteRecord(
            zygote_id=new_id("zygote"),
            owner_user_id=owner_user_id,
            mother_organism_id=mother.organism_id,
            father_organism_id=father.organism_id,
            genome=genome,
            founder_plan={"template": "human_minimal_v3", "organs": template},
        )
        self.stores.zygotes[zygote.zygote_id] = zygote
        oxygen = OxygenProfile(oxygen_id=new_id("oxygen"), zygote_id=zygote.zygote_id, restricted=True)
        self.stores.oxygen_profiles[oxygen.oxygen_id] = oxygen
        self.stores.umbilical_cords[zygote.zygote_id] = UmbilicalCord(
            cord_id=new_id("cord"),
            zygote_id=zygote.zygote_id,
            mother_organism_id=mother.organism_id,
            oxygen_profile_id=oxygen.oxygen_id,
        )
        self._append_event(
            runtime_event(
                RuntimeEventType.GROWTH,
                "Zygote genome created from structured gamete merge",
                zygote_id=zygote.zygote_id,
                genome_id=genome.genome_id,
                stage=zygote.stage.value,
            )
        )
        return zygote

    def develop_zygote(self, zygote_id: str, target_stage: DevelopmentStage | None = None, food_payload: dict[str, object] | None = None) -> ZygoteRecord:
        zygote = self._zygote(zygote_id)
        sequence = [DevelopmentStage.ZYGOTE, DevelopmentStage.EMBRYO, DevelopmentStage.FETUS]
        target = target_stage or (sequence[min(sequence.index(zygote.stage) + 1, len(sequence) - 1)] if zygote.stage in sequence else zygote.stage)
        if target not in sequence:
            target = DevelopmentStage.FETUS
        food_log = list(zygote.food_log)
        if food_payload:
            food_log.append({"payload": food_payload, "stage": target.value, "created_at": utc_now().isoformat()})
        zygote = zygote.model_copy(update={"stage": target, "food_log": food_log, "updated_at": utc_now()})
        self.stores.zygotes[zygote_id] = zygote
        self._append_event(runtime_event(RuntimeEventType.GROWTH, "Zygote developed", zygote_id=zygote_id, stage=target.value))
        return zygote

    def birth_zygote(self, zygote_id: str) -> OrganismRecord:
        zygote = self._zygote(zygote_id)
        if zygote.born_organism_id:
            return self._organism(zygote.born_organism_id)
        mother = self._organism(zygote.mother_organism_id)
        father = self._organism(zygote.father_organism_id)
        organism = OrganismRecord(
            organism_id=new_id("organism"),
            owner_user_id=zygote.owner_user_id or mother.owner_user_id,
            identity_profile=deepcopy(mother.identity_profile),
            lifecycle_state=LifecycleState.HIBERNATED,
            long_term_memory=deepcopy(mother.long_term_memory),
            goals=list(dict.fromkeys(mother.goals + father.goals + ["Grow from zygote blueprint"])),
            policies=deepcopy(mother.policies),
            genome_id="genome-default",
            development_stage=DevelopmentStage.BORN,
            growth_state={
                "zygote_id": zygote.zygote_id,
                "mother_organism_id": mother.organism_id,
                "father_organism_id": father.organism_id,
                "zygote_genome_id": zygote.genome.genome_id,
            },
            lineage_log=[
                {"event": "birth", "zygote_id": zygote.zygote_id, "mother": mother.organism_id, "father": father.organism_id}
            ],
        )
        self.stores.organisms[organism.organism_id] = organism
        self.stores.genomes.setdefault(organism.genome_id, Genome(genome_id=organism.genome_id))
        self.stores.cells[organism.organism_id] = []
        self._append_event(runtime_event(RuntimeEventType.ORGANISM_CREATED, "Organism born from zygote", organism_id=organism.organism_id, zygote_id=zygote_id))
        for organ_id, dna in zygote.genome.organ_cell_dna.items():
            first_tissue = next(iter(dna["tissues"].keys()))
            self.create_cell(
                CellRecord(
                    cell_id=new_id("cell"),
                    organism_id=organism.organism_id,
                    organ_id=organ_id,
                    tissue_id=first_tissue,
                    cell_type=f"{organ_id}-founder",
                    cell_genome_id=str(dna["cell_genome_id"]),
                    expression_profile={organ_id: 1.0, "division": 0.8},
                    lifecycle_state=LifecycleState.HIBERNATED,
                    generation=0,
                    local_state={"organelles": dna["organelles"], "source": "zygote_founder"},
                )
            )
        zygote = zygote.model_copy(update={"stage": DevelopmentStage.BORN, "born_organism_id": organism.organism_id, "updated_at": utc_now()})
        self.stores.zygotes[zygote_id] = zygote
        self.apply_growth_template(organism.organism_id)
        return organism

    def apply_growth_template(self, organism_id: str) -> dict[str, object]:
        organism = self._organism(organism_id)
        template = self.growth_template()
        organs: list[OrganRecord] = []
        tissues: list[TissueRecord] = []
        for organ_id, organ in template.items():
            tissue_targets = organ["tissues"]
            target_cell_count = sum(tissue_targets.values())
            organs.append(
                OrganRecord(
                    organ_id=organ_id,
                    organism_id=organism_id,
                    name=str(organ["name"]),
                    target_cell_count=target_cell_count,
                )
            )
            for tissue_id, target in tissue_targets.items():
                tissues.append(TissueRecord(tissue_id=tissue_id, organism_id=organism_id, organ_id=organ_id, name=tissue_id.replace("-", " ").title(), target_cell_count=int(target)))
                existing = [
                    cell for cell in self.stores.cells.get(organism_id, []) if cell.organ_id == organ_id and cell.tissue_id == tissue_id
                ]
                for index in range(max(0, int(target) - len(existing))):
                    self.create_cell(
                        CellRecord(
                            cell_id=new_id("cell"),
                            organism_id=organism_id,
                            organ_id=organ_id,
                            tissue_id=tissue_id,
                            cell_type=f"{organ_id}-cell",
                            cell_genome_id=f"{organ_id}-cell-genome",
                            expression_profile={organ_id: 1.0, "division": 0.6},
                            lifecycle_state=LifecycleState.HIBERNATED,
                            generation=1,
                            local_state={"organelles": "duplicated_from_growth_template", "growth_index": index},
                        )
                    )
        self.stores.organs[organism_id] = organs
        self.stores.tissues[organism_id] = tissues
        topology = self.build_cytoskeleton_topology(organism_id)
        organism = organism.model_copy(
            update={
                "growth_state": {
                    **organism.growth_state,
                    "template": "human_minimal_v3",
                    "target_organs": len(organs),
                    "target_cells": sum(organ.target_cell_count for organ in organs),
                },
                "updated_at": utc_now(),
            }
        )
        self.stores.organisms[organism_id] = organism
        self._append_event(
            runtime_event(
                RuntimeEventType.GROWTH,
                "V3 organism growth template applied",
                organism_id=organism_id,
                organs=len(organs),
                tissues=len(tissues),
                target_cells=sum(organ.target_cell_count for organ in organs),
                topology_id=topology.topology_id,
            )
        )
        return {
            "organs": [organ.model_dump(mode="json") for organ in organs],
            "tissues": [tissue.model_dump(mode="json") for tissue in tissues],
            "cells": [cell.model_dump(mode="json") for cell in self.stores.cells.get(organism_id, [])],
            "cytoskeleton": topology.model_dump(mode="json"),
        }

    def check_division_readiness(self, organism_id: str, cell_id: str) -> DivisionReadinessResult:
        cell = self._cell(organism_id, cell_id)
        organism = self.stores.organisms.get(organism_id)
        genome = self.stores.genomes.get(organism.genome_id) if organism else None
        policy = genome.division_policy if genome else None

        bypass = GateResult(passed=True, reason="No policy — gate bypassed")
        if policy is None:
            return DivisionReadinessResult(
                cell_id=cell_id, organism_id=organism_id, eligible=True,
                load_gate=bypass, capability_gate=bypass, lifecycle_gate=bypass,
                recommended_mode=DivisionMode.SYMMETRIC, policy_applied=False,
            )

        if not policy.can_divide:
            blocked = GateResult(passed=False, reason="can_divide is False in genome policy")
            return DivisionReadinessResult(
                cell_id=cell_id, organism_id=organism_id, eligible=False,
                blocked_by="can_divide",
                load_gate=blocked, capability_gate=blocked, lifecycle_gate=blocked,
                recommended_mode=policy.preferred_mode, policy_applied=True,
            )

        proteins = self.stores.proteins.get(organism_id, [])
        gates = policy.gates

        # Load gate — minimum throughput before division is productive
        total_proteins = len(proteins)
        load_passed = total_proteins >= gates.load.min_protein_throughput
        load_gate = GateResult(
            passed=load_passed,
            reason=(
                f"Throughput {total_proteins} >= {gates.load.min_protein_throughput}"
                if load_passed
                else f"Insufficient throughput: {total_proteins} < {gates.load.min_protein_throughput}"
            ),
            measured={"total_proteins": total_proteins, "threshold": gates.load.min_protein_throughput},
        )

        # Capability gate — diversity and quality of successful outputs
        cap = gates.capability
        successful = [p for p in proteins if p.validation_report.valid and p.confidence >= cap.min_avg_confidence]
        distinct_types = len({p.type for p in successful})
        avg_conf = sum(p.confidence for p in successful) / len(successful) if successful else 0.0
        cap_passed = (
            len(successful) >= cap.min_successful_proteins
            and distinct_types >= cap.min_distinct_signal_types
            and avg_conf >= cap.min_avg_confidence
        )
        cap_gate = GateResult(
            passed=cap_passed,
            reason=(
                f"Capable: {len(successful)} proteins, {distinct_types} types, conf {avg_conf:.2f}"
                if cap_passed
                else f"Not ready: {len(successful)}/{cap.min_successful_proteins} proteins, "
                     f"{distinct_types}/{cap.min_distinct_signal_types} types, "
                     f"conf {avg_conf:.2f}/{cap.min_avg_confidence}"
            ),
            measured={"successful_proteins": len(successful), "distinct_types": distinct_types, "avg_confidence": round(avg_conf, 3)},
        )

        # Lifecycle gate — generation limit, state, cooldown
        life = gates.lifecycle
        gen_ok = cell.generation <= life.max_generation
        state_ok = cell.lifecycle_state.value == life.required_lifecycle_state
        cooldown_ok = True
        cooldown_detail = "no prior divisions"
        if policy.cooldown_ms > 0:
            prior = [d for d in self.stores.cell_divisions.get(organism_id, []) if d.parent_cell_id == cell_id]
            if prior:
                last = max(prior, key=lambda d: d.created_at)
                elapsed_ms = (utc_now() - last.created_at).total_seconds() * 1000
                cooldown_ok = elapsed_ms >= policy.cooldown_ms
                cooldown_detail = f"{elapsed_ms:.0f}ms elapsed / {policy.cooldown_ms}ms cooldown"
        life_passed = gen_ok and state_ok and cooldown_ok
        life_gate = GateResult(
            passed=life_passed,
            reason=(
                f"Lifecycle OK: gen {cell.generation}, {cell.lifecycle_state}, {cooldown_detail}"
                if life_passed
                else f"Blocked: gen {cell.generation}/{life.max_generation}, "
                     f"state {cell.lifecycle_state}/{life.required_lifecycle_state}, {cooldown_detail}"
            ),
            measured={"generation": cell.generation, "lifecycle_state": cell.lifecycle_state.value, "cooldown_ok": cooldown_ok},
        )

        eligible = load_gate.passed and cap_gate.passed and life_gate.passed
        blocked_by = ", ".join(
            name for name, gate in [("load", load_gate), ("capability", cap_gate), ("lifecycle", life_gate)]
            if not gate.passed
        ) or None
        recommended = (
            policy.preferred_mode if policy.preferred_mode in policy.allowed_modes
            else policy.allowed_modes[0]
        )
        return DivisionReadinessResult(
            cell_id=cell_id, organism_id=organism_id, eligible=eligible,
            blocked_by=blocked_by,
            load_gate=load_gate, capability_gate=cap_gate, lifecycle_gate=life_gate,
            recommended_mode=recommended, policy_applied=True,
        )

    def divide_cell(self, organism_id: str, cell_id: str, mode: DivisionMode = DivisionMode.SYMMETRIC) -> CellDivisionRecord:
        parent = self._cell(organism_id, cell_id)
        if parent.health_state == CellHealthState.DEAD:
            raise ValueError("dead cells cannot divide")

        organism = self.stores.organisms.get(organism_id)
        genome = self.stores.genomes.get(organism.genome_id) if organism else None
        if genome and genome.division_policy:
            policy = genome.division_policy
            if not policy.can_divide:
                raise ValueError("genome division policy prohibits cell division")
            if mode not in policy.allowed_modes:
                allowed = [m.value for m in policy.allowed_modes]
                raise ValueError(f"division mode '{mode.value}' not in allowed modes: {allowed}")
            readiness = self.check_division_readiness(organism_id, cell_id)
            if not readiness.eligible:
                raise ValueError(f"division gates not satisfied: {readiness.blocked_by}")
        daughters: list[CellRecord] = []
        for index in range(2):
            budget = parent.resource_budget.model_copy(
                update={
                    "compute_units": max(0, parent.resource_budget.compute_units // 2),
                    "memory_units": max(0, parent.resource_budget.memory_units // 2),
                    "tool_calls": max(0, parent.resource_budget.tool_calls // 2),
                }
            )
            daughters.append(
                parent.model_copy(
                    update={
                        "cell_id": new_id("cell"),
                        "parent_cell_id": parent.cell_id,
                        "generation": parent.generation + 1,
                        "resource_budget": budget,
                        "local_state": {
                            **parent.local_state,
                            "division_mode": mode.value,
                            "daughter_index": index,
                            "organelles": "duplicated",
                        },
                        "created_at": utc_now(),
                        "last_active_at": None,
                    }
                )
            )
        self.stores.cells.setdefault(organism_id, []).extend(daughters)
        division = CellDivisionRecord(
            division_id=new_id("division"),
            organism_id=organism_id,
            parent_cell_id=parent.cell_id,
            daughter_cell_ids=[cell.cell_id for cell in daughters],
            mode=mode,
        )
        self.stores.cell_divisions.setdefault(organism_id, []).append(division)
        topology = self.build_cytoskeleton_topology(organism_id)
        self._append_event(
            runtime_event(
                RuntimeEventType.CELL_DIVISION,
                "Cell divided with copied genome and duplicated organelles",
                organism_id=organism_id,
                cell_id=parent.cell_id,
                division_id=division.division_id,
                daughter_cell_ids=division.daughter_cell_ids,
                cell_genome_id=parent.cell_genome_id,
                mode=mode.value,
            )
        )
        self._append_event(runtime_event(RuntimeEventType.CYTOSKELETON, "Cytoskeleton topology updated after division", organism_id=organism_id, topology_id=topology.topology_id))
        return division

    def add_food(self, organism_id: str, food_type: str, payload: dict[str, object]) -> FoodIntake:
        self._organism(organism_id)
        routed_to = [cell.cell_id for cell in self.stores.cells.get(organism_id, [])[:5]]
        food = FoodIntake(food_id=new_id("food"), organism_id=organism_id, food_type=food_type, payload=payload, routed_to=routed_to)
        self.stores.food_intakes.setdefault(organism_id, []).append(food)
        self._append_event(runtime_event(RuntimeEventType.FOOD, "Food routed as information intake", organism_id=organism_id, food_id=food.food_id, food_type=food_type, routed_to=routed_to))
        return food

    def grant_oxygen(self, organism_id: str, compute_units: int, memory_units: int, storage_units: int, gpu_units: int, restricted: bool) -> OxygenProfile:
        self._organism(organism_id)
        oxygen = OxygenProfile(
            oxygen_id=new_id("oxygen"),
            organism_id=organism_id,
            compute_units=compute_units,
            memory_units=memory_units,
            storage_units=storage_units,
            gpu_units=gpu_units,
            restricted=restricted,
        )
        self.stores.oxygen_profiles[oxygen.oxygen_id] = oxygen
        self._append_event(runtime_event(RuntimeEventType.OXYGEN, "Oxygen resources granted", organism_id=organism_id, oxygen_id=oxygen.oxygen_id, restricted=restricted))
        return oxygen

    def health_report(self, organism_id: str) -> dict[str, object]:
        organism = self._organism(organism_id)
        cells = self.stores.cells.get(organism_id, [])
        states = {state.value: sum(1 for cell in cells if cell.health_state == state) for state in CellHealthState}
        average_health = sum(cell.health_score for cell in cells) / len(cells) if cells else 0.0
        report = {
            "organism_id": organism_id,
            "development_stage": organism.development_stage.value,
            "lifecycle_state": organism.lifecycle_state.value,
            "cell_count": len(cells),
            "average_cell_health": round(average_health, 3),
            "cell_states": states,
            "food_intakes": len(self.stores.food_intakes.get(organism_id, [])),
            "cell_divisions": len(self.stores.cell_divisions.get(organism_id, [])),
        }
        self._append_event(runtime_event(RuntimeEventType.HEALTH, "Health report generated", organism_id=organism_id, report=report))
        return report

    def self_consume_cell(self, organism_id: str, cell_id: str) -> CellRecord:
        cell = self._cell(organism_id, cell_id).model_copy(
            update={"health_state": CellHealthState.SELF_CONSUMING, "health_score": max(0.0, self._cell(organism_id, cell_id).health_score - 0.3)}
        )
        self.update_cell(cell)
        self._append_event(runtime_event(RuntimeEventType.LYSOSOME, "Cell entered self-consumption cleanup", organism_id=organism_id, cell_id=cell_id))
        return cell

    def mark_cell_dead(self, organism_id: str, cell_id: str) -> CellRecord:
        cell = self._cell(organism_id, cell_id).model_copy(update={"health_state": CellHealthState.DEAD, "health_score": 0.0, "lifecycle_state": LifecycleState.TERMINATED})
        self.update_cell(cell)
        self._append_event(runtime_event(RuntimeEventType.HEALTH, "Cell marked dead", organism_id=organism_id, cell_id=cell_id))
        return cell

    def die_organism(self, organism_id: str) -> SoulSnapshot:
        organism = self._organism(organism_id)
        snapshot = {
            "organism": organism.model_dump(mode="json"),
            "cells": [cell.model_dump(mode="json") for cell in self.stores.cells.get(organism_id, [])],
            "memory_records": [record.model_dump(mode="json") for record in self.stores.memory_records.get(organism_id, [])],
            "growth_state": organism.growth_state,
        }
        soul = SoulSnapshot(soul_id=new_id("soul"), organism_id=organism_id, snapshot=snapshot)
        self.stores.souls[soul.soul_id] = soul
        organism = organism.model_copy(update={"lifecycle_state": LifecycleState.TERMINATED, "development_stage": DevelopmentStage.DEAD, "last_state_snapshot": snapshot, "updated_at": utc_now()})
        self.stores.organisms[organism_id] = organism
        self.stores.cells[organism_id] = [
            cell.model_copy(update={"health_state": CellHealthState.DEAD, "health_score": 0.0, "lifecycle_state": LifecycleState.TERMINATED})
            for cell in self.stores.cells.get(organism_id, [])
        ]
        self._append_event(runtime_event(RuntimeEventType.SOUL, "Soul snapshot persisted from last organism state", organism_id=organism_id, soul_id=soul.soul_id))
        return soul

    def reincarnate_soul(self, soul_id: str, owner_user_id: str | None = None) -> OrganismRecord:
        soul = self.stores.souls[soul_id]
        source = soul.snapshot.get("organism", {})
        organism = OrganismRecord(
            **{
                **source,
                "organism_id": new_id("organism"),
                "owner_user_id": owner_user_id or source.get("owner_user_id"),
                "lifecycle_state": LifecycleState.HIBERNATED,
                "development_stage": DevelopmentStage.BORN,
                "growth_state": {**source.get("growth_state", {}), "reincarnated_from_soul_id": soul_id},
                "updated_at": utc_now(),
            }
        )
        self.stores.organisms[organism.organism_id] = organism
        self.stores.cells[organism.organism_id] = [
            CellRecord(**{**cell, "organism_id": organism.organism_id, "cell_id": new_id("cell"), "lifecycle_state": LifecycleState.HIBERNATED, "health_state": CellHealthState.ALIVE, "health_score": 1.0})
            for cell in soul.snapshot.get("cells", [])
        ]
        self.stores.souls[soul_id] = soul.model_copy(update={"reincarnated_organism_id": organism.organism_id})
        self._append_event(runtime_event(RuntimeEventType.SOUL, "Soul snapshot reincarnated into new organism", organism_id=organism.organism_id, soul_id=soul_id))
        return organism

    def create_bone_proposal(self, proposal: StructureProposal) -> StructureProposal:
        self.stores.structure_proposals[proposal.proposal_id] = proposal
        self._append_event(runtime_event(RuntimeEventType.BONE, "Osteoblast structure proposal created", proposal_id=proposal.proposal_id, structure_type=proposal.structure_type))
        return proposal

    def decide_structure_proposal(self, proposal_id: str, approved: bool, reason: str, owner_user_id: str | None = None) -> StructureProposal:
        proposal = self.stores.structure_proposals[proposal_id]
        if owner_user_id is not None and proposal.owner_user_id != owner_user_id:
            raise KeyError(proposal_id)
        proposal = proposal.model_copy(
            update={"status": "approved" if approved else "rejected", "decision_reason": reason, "decided_at": utc_now()}
        )
        self.stores.structure_proposals[proposal_id] = proposal
        if approved:
            bone = BoneStructureRecord(
                bone_id=new_id("bone"),
                owner_user_id=proposal.owner_user_id,
                name=proposal.name,
                structure_type=proposal.structure_type,
                definition=proposal.definition,
            )
            self.stores.bone_structures[bone.bone_id] = bone
        self._append_event(runtime_event(RuntimeEventType.BONE, "Osteocyte proposal decision recorded", proposal_id=proposal_id, status=proposal.status, reason=reason))
        return proposal

    def build_cytoskeleton_topology(self, organism_id: str) -> CytoskeletonTopology:
        organs = self.stores.organs.get(organism_id, [])
        tissues = self.stores.tissues.get(organism_id, [])
        cells = self.stores.cells.get(organism_id, [])
        topology = CytoskeletonTopology(
            topology_id=new_id("topology"),
            organism_id=organism_id,
            organ_edges=[{"from": "organism", "to": organ.organ_id} for organ in organs],
            tissue_edges=[{"from": tissue.organ_id, "to": tissue.tissue_id} for tissue in tissues],
            cell_edges=[{"from": cell.tissue_id, "to": cell.cell_id} for cell in cells if cell.organ_id != "core"],
        )
        self.stores.cytoskeleton[organism_id] = topology
        return topology

    def create_review(self, review: ReviewRequest) -> ReviewRequest:
        self.stores.reviews[review.review_id] = review
        self._append_event(runtime_event(RuntimeEventType.REVIEW, "Review requested", review_id=review.review_id, resource_type=review.resource_type, resource_id=review.resource_id, action=review.action))
        return review

    def decide_review(self, review_id: str, approved: bool, reviewer_id: str | None, reason: str) -> ReviewRequest:
        review = self.stores.reviews[review_id].model_copy(
            update={
                "status": "approved" if approved else "rejected",
                "reviewer_id": reviewer_id,
                "decision_reason": reason,
                "decided_at": utc_now(),
            }
        )
        self.stores.reviews[review_id] = review
        self._append_event(runtime_event(RuntimeEventType.REVIEW, "Review decided", review_id=review.review_id, status=review.status, reviewer_id=reviewer_id))
        return review

    def submit_signal(self, signal: Signal) -> tuple[MembraneDecision, CellRecord | None, Protein | None, list[RuntimeEvent], StructureRequest | None]:
        organism = self._organism(signal.organism_id)
        genome = self.stores.genomes[organism.genome_id]
        self.stores.signals.setdefault(signal.organism_id, []).append(signal)
        events: list[RuntimeEvent] = []

        decision = self.membrane.admit(organism, genome, signal)
        events.append(
            runtime_event(
                RuntimeEventType.MEMBRANE,
                decision.reason,
                organism_id=signal.organism_id,
                signal_id=signal.signal_id,
                code=decision.code,
                action=decision.action.value,
                actor_id=signal.actor.actor_id,
            )
        )
        if decision.action == MembraneDecisionAction.REJECT:
            self._extend_events(events)
            return decision, None, None, events, None

        if organism.lifecycle_state != LifecycleState.ACTIVE:
            organism = self.wake(signal.organism_id)
            events.append(runtime_event(RuntimeEventType.LIFECYCLE, "Signal caused organism wake", organism_id=signal.organism_id, signal_id=signal.signal_id))

        recalled_memory = self.recall_memory(signal)
        if recalled_memory:
            events.append(
                runtime_event(
                    RuntimeEventType.MEMORY,
                    "Cytoplasm recalled scoped memory",
                    organism_id=signal.organism_id,
                    signal_id=signal.signal_id,
                    memory_ids=[memory.memory_id for memory in recalled_memory],
                    count=len(recalled_memory),
                )
            )
        cell, skipped_cells = self.cytoplasm.select_cell(signal.organism_id, signal, genome)
        events.append(
            runtime_event(
                RuntimeEventType.CYTOPLASM,
                "Context loaded and signal routed",
                organism_id=signal.organism_id,
                cell_id=cell.cell_id,
                signal_id=signal.signal_id,
                context_refs=signal.context_refs,
                priority=signal.priority,
                selected_cell_id=cell.cell_id,
                skipped_cells=skipped_cells,
            )
        )
        module = self.nucleus.select_module(genome, cell, signal)
        events.append(
            runtime_event(
                RuntimeEventType.NUCLEUS,
                "Genome module selected from expression profile",
                organism_id=signal.organism_id,
                cell_id=cell.cell_id,
                signal_id=signal.signal_id,
                module_id=module.module_id,
                expression=cell.expression_profile,
            )
        )

        cell, reserved, remaining_budget = self.mitochondria.reserve(cell, module)
        events.append(
            runtime_event(
                RuntimeEventType.MITOCHONDRIA,
                "Resource budget evaluated",
                organism_id=signal.organism_id,
                cell_id=cell.cell_id,
                signal_id=signal.signal_id,
                reserved=reserved,
                remaining_budget=remaining_budget,
            )
        )
        if not reserved:
            protein = Protein(
                protein_id=new_id("protein"),
                organism_id=signal.organism_id,
                source_signal_id=signal.signal_id,
                type=f"{module.module_id}.quota",
                payload={"error": "resource budget exhausted"},
                confidence=0.0,
            )
            protein = self.protein_pipeline.validate(protein, signal)
            events.extend(self._protein_events(signal, cell, protein, module))
            self.stores.proteins.setdefault(signal.organism_id, []).append(protein)
            self._extend_events(events)
            self.hibernate(signal.organism_id)
            return decision, cell, protein, events, None

        structure_request, contract_error, contract_id = self.skeleton.evaluate_contract_call(signal)
        if structure_request is not None:
            self.stores.structure_requests.setdefault(signal.organism_id, []).append(structure_request)
            events.append(
                runtime_event(
                    RuntimeEventType.STRUCTURE_REQUEST,
                    "Cell requested missing contract",
                    organism_id=signal.organism_id,
                    cell_id=cell.cell_id,
                    signal_id=signal.signal_id,
                    contract_id=contract_id,
                    requested_contract=structure_request.requested_contract,
                    status=structure_request.status,
                )
            )
            events.append(
                runtime_event(
                    RuntimeEventType.SKELETON,
                    "Osteocyte queued structure request for review",
                    organism_id=signal.organism_id,
                    cell_id=cell.cell_id,
                    signal_id=signal.signal_id,
                    contract_id=contract_id,
                    request_id=structure_request.request_id,
                    requested_contract=structure_request.requested_contract,
                    status=structure_request.status,
                )
            )
            self._extend_events(events)
            self.hibernate(signal.organism_id)
            return decision, cell, None, events, structure_request

        if contract_error is not None:
            protein = self.protein_pipeline.validate(contract_error, signal)
        else:
            protein = self.ribosome.execute(module, signal)
            events.append(
                runtime_event(
                    RuntimeEventType.RIBOSOME,
                    "Execution strategy selected",
                    organism_id=signal.organism_id,
                    cell_id=cell.cell_id,
                    signal_id=signal.signal_id,
                    protein_id=protein.protein_id,
                    strategy=module.execution_strategy.value,
                    deterministic_tool=module.deterministic_tool,
                )
            )
            protein = self.protein_pipeline.validate(protein, signal)
        events.extend(self._protein_events(signal, cell, protein, module))
        self.stores.proteins.setdefault(signal.organism_id, []).append(protein)
        written_memory = self.write_memory_from_protein(signal, protein)
        if written_memory is not None:
            events.append(
                runtime_event(
                    RuntimeEventType.MEMORY,
                    "Approved protein persisted as memory",
                    organism_id=signal.organism_id,
                    signal_id=signal.signal_id,
                    protein_id=protein.protein_id,
                    memory_id=written_memory.memory_id,
                    kind=written_memory.kind,
                )
            )
        self._extend_events(events)
        self.hibernate(signal.organism_id)
        return decision, cell, protein, events, None

    def validate_genome(self, genome: Genome) -> ValidationReport:
        errors: list[str] = []
        if not genome.modules:
            errors.append("genome must define at least one module")
        module_ids = [module.module_id for module in genome.modules]
        if len(module_ids) != len(set(module_ids)):
            errors.append("module ids must be unique")
        for module in genome.modules:
            if module.execution_strategy == ExecutionStrategy.DETERMINISTIC_TOOL and not module.deterministic_tool:
                errors.append(f"{module.module_id} requires deterministic_tool")
        return ValidationReport(valid=not errors, errors=errors)

    def _protein_events(self, signal: Signal, cell: CellRecord, protein: Protein, module: GenomeModule) -> list[RuntimeEvent]:
        events = [
            runtime_event(
                RuntimeEventType.PROTEIN,
                "Protein validation completed",
                organism_id=signal.organism_id,
                cell_id=cell.cell_id,
                signal_id=signal.signal_id,
                protein_id=protein.protein_id,
                protein_type=protein.type,
                status=protein.status.value,
                confidence=protein.confidence,
                misfolding_types=[item.value for item in protein.validation_report.misfolding_types],
            ),
            runtime_event(
                RuntimeEventType.GOLGI,
                "Protein shaped and validation report attached",
                organism_id=signal.organism_id,
                cell_id=cell.cell_id,
                signal_id=signal.signal_id,
                protein_id=protein.protein_id,
                status=protein.status.value,
                validation_report=protein.validation_report.model_dump(mode="json"),
            )
        ]
        if MisfoldingType.TOXIC in protein.validation_report.misfolding_types:
            events.append(
                runtime_event(
                    RuntimeEventType.PEROXISOME,
                    "Toxic protein blocked by safety organelle",
                    organism_id=signal.organism_id,
                    cell_id=cell.cell_id,
                    signal_id=signal.signal_id,
                    protein_id=protein.protein_id,
                )
            )
        if protein.validation_report.misfolding_types:
            events.append(
                runtime_event(
                    RuntimeEventType.LYSOSOME,
                    "Misfolded temporary state cleaned",
                    organism_id=signal.organism_id,
                    cell_id=cell.cell_id,
                    signal_id=signal.signal_id,
                    protein_id=protein.protein_id,
                    misfolding_types=[item.value for item in protein.validation_report.misfolding_types],
                )
            )
        else:
            events.append(
                runtime_event(
                    RuntimeEventType.LYSOSOME,
                    "Temporary execution state cleaned",
                    organism_id=signal.organism_id,
                    cell_id=cell.cell_id,
                    signal_id=signal.signal_id,
                )
            )
        events.append(
            runtime_event(
                RuntimeEventType.VACUOLE,
                "Protein cached as runtime artifact",
                organism_id=signal.organism_id,
                cell_id=cell.cell_id,
                protein_id=protein.protein_id,
                module_id=module.module_id,
            )
        )
        return events

    def _organism(self, organism_id: str) -> OrganismRecord:
        if organism_id not in self.stores.organisms:
            raise KeyError(organism_id)
        return self.stores.organisms[organism_id]

    def _cell(self, organism_id: str, cell_id: str | None) -> CellRecord:
        for cell in self.stores.cells.get(organism_id, []):
            if cell_id is None or cell.cell_id == cell_id:
                return cell
        raise KeyError(cell_id or organism_id)

    def _memory(self, organism_id: str, memory_id: str) -> MemoryRecord:
        for memory in self.stores.memory_records.get(organism_id, []):
            if memory.memory_id == memory_id:
                return memory
        raise KeyError(memory_id)

    def _zygote(self, zygote_id: str) -> ZygoteRecord:
        if zygote_id not in self.stores.zygotes:
            raise KeyError(zygote_id)
        return self.stores.zygotes[zygote_id]

    def _map_payload(self, payload: dict[str, object], mapping: dict[str, str]) -> dict[str, object]:
        if not mapping:
            return dict(payload)
        mapped: dict[str, object] = {}
        for source, target in mapping.items():
            current: object = payload
            for part in source.split("."):
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    current = None
                    break
            mapped[target] = current
        return mapped

    def _append_event(self, event: RuntimeEvent) -> None:
        key = event.organism_id or "global"
        self.stores.events.setdefault(key, []).append(event)

    def _extend_events(self, events: list[RuntimeEvent]) -> None:
        for event in events:
            self._append_event(event)


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def safe_calculate(expression: str) -> float:
    if not re.fullmatch(r"[0-9+\-*/().\s]+", expression):
        raise ValueError("expression contains unsupported characters")
    return float(_eval_node(ast.parse(expression, mode="eval").body))


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return float(_OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right)))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return float(_OPERATORS[type(node.op)](_eval_node(node.operand)))
    raise ValueError("unsupported expression")
