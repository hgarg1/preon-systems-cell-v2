from __future__ import annotations

from uuid import uuid4

from preon_systems_cell.engine import ENGINE_VERSION, OrganismRuntime, new_id
from preon_systems_cell.models import (
    Actor,
    BlockStructureRequestRequest,
    AdapterTestRequest,
    ApplyGrowthTemplateRequest,
    Capability,
    CellRecord,
    Contract,
    CreateBoneProposalRequest,
    CreateCapabilityRequest,
    CreateCellRequest,
    CreateContractRequest,
    CreateGenomeVersionRequest,
    CreateMemoryRequest,
    CreateOrganismRequest,
    CreateReviewRequest,
    CreateZygoteRequest,
    DecideProposalRequest,
    DecideReviewRequest,
    DevelopZygoteRequest,
    DivideCellRequest,
    DivisionPolicy,
    DivisionReadinessResult,
    FoodIntakeRequest,
    Genome,
    GenomePreviewRequest,
    GenomeVersion,
    GenomeValidationResponse,
    MaintenanceJobRun,
    MemoryRecord,
    OrganismDetailResponse,
    OrganismRecord,
    OxygenGrantRequest,
    PolicySimulationRequest,
    PolicyUpdateRequest,
    PolicyVersion,
    ReproductionNegotiateRequest,
    ReplayRun,
    ResourceBudget,
    ReviewRequest,
    RuntimeAlert,
    RuntimeEvent,
    RuntimeEventType,
    Signal,
    StructureRequest,
    StructureProposal,
    ResolveStructureRequestRequest,
    SubmitSignalRequest,
    SubmitSignalResponse,
    UpdateCellRequest,
    ValidationReport,
    utc_now,
)


RUNTIME = OrganismRuntime()


def create_organism(request: CreateOrganismRequest, owner_user_id: str | None = None) -> OrganismRecord:
    organism = OrganismRecord(
        organism_id=new_id("organism"),
        owner_user_id=owner_user_id,
        identity_profile=request.identity_profile,
        goals=request.goals,
        policies=request.policies,
    )
    return RUNTIME.create_organism(organism)


def list_organisms(owner_user_id: str | None = None) -> list[OrganismRecord]:
    organisms = RUNTIME.stores.organisms.values()
    if owner_user_id is not None:
        organisms = [organism for organism in organisms if organism.owner_user_id == owner_user_id]
    return sorted(organisms, key=lambda organism: organism.created_at, reverse=True)


def get_organism_detail(organism_id: str, owner_user_id: str | None = None) -> OrganismDetailResponse | None:
    organism = RUNTIME.stores.organisms.get(organism_id)
    if organism is None or (owner_user_id is not None and organism.owner_user_id != owner_user_id):
        return None
    return OrganismDetailResponse(
        organism=organism,
        genome=RUNTIME.stores.genomes[organism.genome_id],
        cells=RUNTIME.stores.cells.get(organism_id, []),
        events=RUNTIME.stores.events.get(organism_id, []),
        proteins=RUNTIME.stores.proteins.get(organism_id, []),
        structure_requests=RUNTIME.stores.structure_requests.get(organism_id, []),
        memory_records=RUNTIME.stores.memory_records.get(organism_id, []),
    )


def wake_organism(organism_id: str, owner_user_id: str | None = None) -> OrganismRecord | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return RUNTIME.wake(organism_id)


def hibernate_organism(organism_id: str, owner_user_id: str | None = None) -> OrganismRecord | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return RUNTIME.hibernate(organism_id)


def list_cells(organism_id: str, owner_user_id: str | None = None) -> list[CellRecord] | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return RUNTIME.stores.cells.get(organism_id, [])


def create_cell(organism_id: str, request: CreateCellRequest, owner_user_id: str | None = None) -> CellRecord | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    cell = CellRecord(
        cell_id=new_id("cell"),
        organism_id=organism_id,
        organ_id=request.organ_id,
        tissue_id=request.tissue_id,
        cell_type=request.cell_type,
        cell_genome_id=request.cell_genome_id,
        expression_profile=request.expression_profile or {"reasoning": 0.5},
        resource_budget=request.resource_budget,
    )
    return RUNTIME.create_cell(cell)


def update_cell(organism_id: str, cell_id: str, request: UpdateCellRequest, owner_user_id: str | None = None) -> CellRecord | None:
    detail = get_organism_detail(organism_id, owner_user_id)
    if detail is None:
        return None
    cell = next((item for item in detail.cells if item.cell_id == cell_id), None)
    if cell is None:
        return None
    update = {}
    for field in ("organ_id", "tissue_id", "cell_type", "cell_genome_id", "expression_profile", "resource_budget", "lifecycle_state", "health_state", "health_score"):
        value = getattr(request, field)
        if value is not None:
            update[field] = value
    return RUNTIME.update_cell(cell.model_copy(update=update))


def hibernate_cell(organism_id: str, cell_id: str, owner_user_id: str | None = None) -> CellRecord | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    try:
        return RUNTIME.hibernate_cell(organism_id, cell_id)
    except KeyError:
        return None


def list_memory(organism_id: str, owner_user_id: str | None = None) -> list[MemoryRecord] | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return sorted(RUNTIME.stores.memory_records.get(organism_id, []), key=lambda item: item.created_at, reverse=True)


def create_memory(organism_id: str, request: CreateMemoryRequest, owner_user_id: str | None = None) -> MemoryRecord | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return RUNTIME.create_memory(
        MemoryRecord(
            memory_id=new_id("memory"),
            organism_id=organism_id,
            scope=request.scope,
            kind=request.kind,
            payload=request.payload,
            confidence=request.confidence,
        )
    )


def get_memory(organism_id: str, memory_id: str, owner_user_id: str | None = None) -> MemoryRecord | None:
    memories = list_memory(organism_id, owner_user_id)
    if memories is None:
        return None
    return next((item for item in memories if item.memory_id == memory_id), None)


def deprecate_memory(organism_id: str, memory_id: str, owner_user_id: str | None = None) -> MemoryRecord | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    try:
        return RUNTIME.deprecate_memory(organism_id, memory_id)
    except KeyError:
        return None


def submit_signal(
    organism_id: str,
    request: SubmitSignalRequest,
    owner_user_id: str | None = None,
    actor: Actor | None = None,
) -> SubmitSignalResponse | None:
    detail = get_organism_detail(organism_id, owner_user_id)
    if detail is None:
        return None
    signal = Signal(
        signal_id=f"signal-{uuid4().hex[:12]}",
        organism_id=organism_id,
        actor=actor or Actor(actor_id=owner_user_id or "operator"),
        type=request.type,
        payload=request.payload,
        context_refs=request.context_refs,
        priority=request.priority,
        metadata=request.metadata,
    )
    decision, cell, protein, events, structure_request = RUNTIME.submit_signal(signal)
    return SubmitSignalResponse(
        signal=signal,
        membrane_decision=decision,
        cell=cell,
        protein=protein,
        events=events,
        structure_request=structure_request,
    )


def create_contract(request: CreateContractRequest, owner_user_id: str | None = None) -> Contract:
    contract = Contract(
        contract_id=new_id("contract"),
        owner_user_id=owner_user_id,
        name=request.name,
        schema=request.contract_schema,
        allowed_actions=request.allowed_actions,
        permissions=request.permissions,
        rate_limits=request.rate_limits,
        dependencies=request.dependencies,
        adapter_id=request.adapter_id,
        input_mapping=request.input_mapping,
        output_mapping=request.output_mapping,
        capability_ids=request.capability_ids,
        test_vectors=request.test_vectors,
        created_by=owner_user_id,
    )
    return RUNTIME.create_contract(contract)


def list_contracts(owner_user_id: str | None = None) -> list[Contract]:
    contracts = RUNTIME.stores.contracts.values()
    if owner_user_id is not None:
        contracts = [contract for contract in contracts if contract.owner_user_id == owner_user_id]
    return sorted(contracts, key=lambda contract: contract.created_at, reverse=True)


def deprecate_contract(contract_id: str, owner_user_id: str | None = None) -> Contract | None:
    contract = RUNTIME.stores.contracts.get(contract_id)
    if contract is None or (owner_user_id is not None and contract.owner_user_id != owner_user_id):
        return None
    return RUNTIME.deprecate_contract(contract_id)


def list_capabilities(owner_user_id: str | None = None) -> list[Capability]:
    capabilities = RUNTIME.stores.capabilities.values()
    if owner_user_id is not None:
        capabilities = [item for item in capabilities if item.owner_user_id == owner_user_id]
    return sorted(capabilities, key=lambda item: item.created_at, reverse=True)


def create_capability(request: CreateCapabilityRequest, owner_user_id: str | None = None) -> Capability:
    return RUNTIME.create_capability(
        Capability(
            capability_id=new_id("capability"),
            owner_user_id=owner_user_id,
            name=request.name,
            description=request.description,
            schema=request.capability_schema,
        )
    )


def validate_contract_adapter(contract_id: str, owner_user_id: str | None = None) -> ValidationReport | None:
    contract = RUNTIME.stores.contracts.get(contract_id)
    if contract is None or (owner_user_id is not None and contract.owner_user_id != owner_user_id):
        return None
    return RUNTIME.validate_contract_adapter(contract_id)


def test_contract_adapter(contract_id: str, request: AdapterTestRequest, owner_user_id: str | None = None) -> dict[str, object] | None:
    contract = RUNTIME.stores.contracts.get(contract_id)
    if contract is None or (owner_user_id is not None and contract.owner_user_id != owner_user_id):
        return None
    return RUNTIME.test_contract_adapter(contract_id, request.payload)


def list_structure_requests(owner_user_id: str | None = None) -> list[StructureRequest]:
    requests: list[StructureRequest] = []
    for organism_id, organism_requests in RUNTIME.stores.structure_requests.items():
        organism = RUNTIME.stores.organisms.get(organism_id)
        if owner_user_id is None or (organism is not None and organism.owner_user_id == owner_user_id):
            requests.extend(organism_requests)
    return sorted(requests, key=lambda item: item.created_at, reverse=True)


def resolve_structure_request(
    request_id: str,
    payload: ResolveStructureRequestRequest,
    owner_user_id: str | None = None,
) -> StructureRequest | None:
    request = _owned_structure_request(request_id, owner_user_id)
    if request is None:
        return None
    updated = RUNTIME.skeleton.resolve_structure_request(request, payload.contract_id)
    RUNTIME._append_event(
        runtime_event_for_structure_request(updated, "Osteoblast resolved structure request", contract_id=payload.contract_id)
    )
    return updated


def block_structure_request(
    request_id: str,
    payload: BlockStructureRequestRequest,
    owner_user_id: str | None = None,
) -> StructureRequest | None:
    request = _owned_structure_request(request_id, owner_user_id)
    if request is None:
        return None
    updated = RUNTIME.skeleton.block_structure_request(request, payload.reason)
    RUNTIME._append_event(runtime_event_for_structure_request(updated, "Osteocyte blocked structure request"))
    return updated


def get_genome(genome_id: str) -> Genome | None:
    return RUNTIME.stores.genomes.get(genome_id)


def validate_genome(genome: Genome) -> GenomeValidationResponse:
    return GenomeValidationResponse(genome_id=genome.genome_id, report=RUNTIME.validate_genome(genome))


def replay_signal(organism_id: str, signal_id: str, owner_user_id: str | None = None) -> ReplayRun | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    try:
        return RUNTIME.replay_signal(organism_id, signal_id)
    except StopIteration:
        return None


def list_events(
    organism_id: str,
    owner_user_id: str | None = None,
    *,
    event_type: str | None = None,
    signal_id: str | None = None,
    limit: int = 100,
    cursor: int = 0,
) -> dict[str, object] | None:
    detail = get_organism_detail(organism_id, owner_user_id)
    if detail is None:
        return None
    events = detail.events
    if event_type:
        events = [event for event in events if event.type == event_type]
    if signal_id:
        events = [event for event in events if event.signal_id == signal_id]
    limit = max(1, min(limit, 500))
    page = events[cursor : cursor + limit]
    next_cursor = cursor + limit if cursor + limit < len(events) else None
    return {"events": [event.model_dump(mode="json") for event in page], "next_cursor": next_cursor}


def get_policies(organism_id: str, owner_user_id: str | None = None) -> PolicyVersion | None:
    detail = get_organism_detail(organism_id, owner_user_id)
    if detail is None:
        return None
    versions = RUNTIME.stores.policy_versions.get(organism_id, [])
    if versions:
        return versions[-1]
    version = PolicyVersion(policy_version_id=new_id("policy"), organism_id=organism_id, version=1, policies=detail.organism.policies)
    RUNTIME.stores.policy_versions.setdefault(organism_id, []).append(version)
    return version


def update_policies(organism_id: str, request: PolicyUpdateRequest, owner_user_id: str | None = None) -> PolicyVersion | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    report = RUNTIME.validate_policy(request.policies)
    if not report.valid:
        raise ValueError("; ".join(report.errors))
    return RUNTIME.update_policy(organism_id, request.policies, owner_user_id)


def validate_policies(request: PolicyUpdateRequest) -> ValidationReport:
    return RUNTIME.validate_policy(request.policies)


def simulate_policy(organism_id: str, request: PolicySimulationRequest, owner_user_id: str | None = None) -> dict[str, object] | None:
    detail = get_organism_detail(organism_id, owner_user_id)
    if detail is None:
        return None
    signal = Signal(
        signal_id=new_id("simulation"),
        organism_id=organism_id,
        actor=Actor(actor_id=owner_user_id or "operator"),
        type=request.signal.type,
        payload=request.signal.payload,
        context_refs=request.signal.context_refs,
        priority=request.signal.priority,
        metadata=request.signal.metadata,
    )
    decision = RUNTIME.simulate_policy(organism_id, request.policies or detail.organism.policies, signal)
    return {"membrane_decision": decision.model_dump(mode="json")}


def list_genomes() -> list[Genome]:
    return sorted(RUNTIME.stores.genomes.values(), key=lambda item: item.genome_id)


def create_genome_version(request: CreateGenomeVersionRequest, owner_user_id: str | None = None) -> GenomeVersion:
    return RUNTIME.create_genome_version(request.genome, owner_user_id)


def list_genome_versions(genome_id: str, owner_user_id: str | None = None) -> list[GenomeVersion] | None:
    versions = RUNTIME.stores.genome_versions.get(genome_id, [])
    if owner_user_id is not None:
        versions = [version for version in versions if version.owner_user_id in {None, owner_user_id}]
    return versions


def activate_genome_version(genome_id: str, version: int, owner_user_id: str | None = None) -> GenomeVersion | None:
    versions = list_genome_versions(genome_id, owner_user_id)
    if not versions or not any(item.version == version for item in versions):
        return None
    return RUNTIME.activate_genome_version(genome_id, version)


def preview_genome(organism_id: str, request: GenomePreviewRequest, owner_user_id: str | None = None) -> dict[str, object] | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    signal = Signal(signal_id=new_id("preview"), organism_id=organism_id, type=request.signal_type, payload=request.payload)
    try:
        return RUNTIME.preview_genome(organism_id, signal, request.cell_id)
    except KeyError:
        return None


def maintenance_status() -> dict[str, object]:
    return {
        "runs": [run.model_dump(mode="json") for run in RUNTIME.stores.maintenance_runs[-10:]],
        "alerts": [alert.model_dump(mode="json") for alert in RUNTIME.stores.alerts.values() if alert.status == "active"],
    }


def run_maintenance() -> MaintenanceJobRun:
    return RUNTIME.run_maintenance()


def runtime_metrics(organism_id: str | None = None, owner_user_id: str | None = None) -> dict[str, object] | None:
    if organism_id and get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return RUNTIME.runtime_metrics(organism_id)


def export_organism(organism_id: str, owner_user_id: str | None = None) -> dict[str, object] | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return RUNTIME.export_organism(organism_id)


def debug_bundle(organism_id: str, owner_user_id: str | None = None) -> dict[str, object] | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return RUNTIME.debug_bundle(organism_id)


def import_organism(bundle: dict[str, object], owner_user_id: str | None = None) -> OrganismRecord:
    data = dict(bundle.get("organism", {}))
    data["organism_id"] = new_id("organism")
    data["owner_user_id"] = owner_user_id
    organism = OrganismRecord(**data)
    RUNTIME.create_organism(organism)
    return organism


def negotiate_reproduction(request: ReproductionNegotiateRequest, owner_user_id: str | None = None) -> dict[str, object] | None:
    if get_organism_detail(request.mother_organism_id, owner_user_id) is None:
        return None
    if get_organism_detail(request.father_organism_id, owner_user_id) is None:
        return None
    return RUNTIME.negotiate_reproduction(request.mother_organism_id, request.father_organism_id)


def create_zygote(request: CreateZygoteRequest, owner_user_id: str | None = None):
    if get_organism_detail(request.mother_organism_id, owner_user_id) is None:
        return None
    if get_organism_detail(request.father_organism_id, owner_user_id) is None:
        return None
    return RUNTIME.create_zygote(request.mother_organism_id, request.father_organism_id, owner_user_id)


def list_zygotes(owner_user_id: str | None = None):
    zygotes = RUNTIME.stores.zygotes.values()
    if owner_user_id is not None:
        zygotes = [zygote for zygote in zygotes if zygote.owner_user_id == owner_user_id]
    return sorted(zygotes, key=lambda item: item.created_at, reverse=True)


def get_zygote(zygote_id: str, owner_user_id: str | None = None):
    zygote = RUNTIME.stores.zygotes.get(zygote_id)
    if zygote is None or (owner_user_id is not None and zygote.owner_user_id != owner_user_id):
        return None
    return zygote


def develop_zygote(zygote_id: str, request: DevelopZygoteRequest, owner_user_id: str | None = None):
    if get_zygote(zygote_id, owner_user_id) is None:
        return None
    return RUNTIME.develop_zygote(zygote_id, request.target_stage, request.food_payload)


def birth_zygote(zygote_id: str, owner_user_id: str | None = None) -> OrganismRecord | None:
    if get_zygote(zygote_id, owner_user_id) is None:
        return None
    return RUNTIME.birth_zygote(zygote_id)


def growth_template() -> dict[str, dict[str, object]]:
    return RUNTIME.growth_template()


def apply_growth_template(organism_id: str, request: ApplyGrowthTemplateRequest, owner_user_id: str | None = None) -> dict[str, object] | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    if request.template_name != "human_minimal_v3":
        raise ValueError("unknown growth template")
    return RUNTIME.apply_growth_template(organism_id)


def list_organs(organism_id: str, owner_user_id: str | None = None):
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return RUNTIME.stores.organs.get(organism_id, [])


def list_tissues(organism_id: str, owner_user_id: str | None = None):
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return RUNTIME.stores.tissues.get(organism_id, [])


def update_genome_division_policy(genome_id: str, policy: DivisionPolicy) -> Genome | None:
    genome = RUNTIME.stores.genomes.get(genome_id)
    if genome is None:
        return None
    updated = genome.model_copy(update={"division_policy": policy})
    RUNTIME.stores.genomes[genome_id] = updated
    return updated


def check_cell_division_readiness(organism_id: str, cell_id: str, owner_user_id: str | None = None) -> DivisionReadinessResult | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    try:
        return RUNTIME.check_division_readiness(organism_id, cell_id)
    except KeyError:
        return None


def divide_cell(organism_id: str, cell_id: str, request: DivideCellRequest, owner_user_id: str | None = None):
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    try:
        return RUNTIME.divide_cell(organism_id, cell_id, request.mode)
    except KeyError:
        return None


def list_cell_divisions(organism_id: str, owner_user_id: str | None = None):
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return RUNTIME.stores.cell_divisions.get(organism_id, [])


def add_food(organism_id: str, request: FoodIntakeRequest, owner_user_id: str | None = None):
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return RUNTIME.add_food(organism_id, request.food_type, request.payload)


def grant_oxygen(organism_id: str, request: OxygenGrantRequest, owner_user_id: str | None = None):
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return RUNTIME.grant_oxygen(
        organism_id,
        request.compute_units,
        request.memory_units,
        request.storage_units,
        request.gpu_units,
        request.restricted,
    )


def health_report(organism_id: str, owner_user_id: str | None = None) -> dict[str, object] | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return RUNTIME.health_report(organism_id)


def self_consume_cell(organism_id: str, cell_id: str, owner_user_id: str | None = None) -> CellRecord | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    try:
        return RUNTIME.self_consume_cell(organism_id, cell_id)
    except KeyError:
        return None


def mark_cell_dead(organism_id: str, cell_id: str, owner_user_id: str | None = None) -> CellRecord | None:
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    try:
        return RUNTIME.mark_cell_dead(organism_id, cell_id)
    except KeyError:
        return None


def die_organism(organism_id: str, owner_user_id: str | None = None):
    if get_organism_detail(organism_id, owner_user_id) is None:
        return None
    return RUNTIME.die_organism(organism_id)


def list_souls(owner_user_id: str | None = None):
    souls = RUNTIME.stores.souls.values()
    if owner_user_id is not None:
        owned_ids = {organism.organism_id for organism in RUNTIME.stores.organisms.values() if organism.owner_user_id == owner_user_id}
        souls = [soul for soul in souls if soul.organism_id in owned_ids]
    return sorted(souls, key=lambda item: item.created_at, reverse=True)


def get_soul(soul_id: str, owner_user_id: str | None = None):
    soul = RUNTIME.stores.souls.get(soul_id)
    if soul is None:
        return None
    if owner_user_id is not None:
        organism = RUNTIME.stores.organisms.get(soul.organism_id)
        if organism is None or organism.owner_user_id != owner_user_id:
            return None
    return soul


def reincarnate_soul(soul_id: str, owner_user_id: str | None = None) -> OrganismRecord | None:
    if get_soul(soul_id, owner_user_id) is None:
        return None
    return RUNTIME.reincarnate_soul(soul_id, owner_user_id)


def list_bones(owner_user_id: str | None = None):
    bones = RUNTIME.stores.bone_structures.values()
    if owner_user_id is not None:
        bones = [bone for bone in bones if bone.owner_user_id == owner_user_id]
    return sorted(bones, key=lambda item: item.created_at, reverse=True)


def list_structure_proposals(owner_user_id: str | None = None):
    proposals = RUNTIME.stores.structure_proposals.values()
    if owner_user_id is not None:
        proposals = [proposal for proposal in proposals if proposal.owner_user_id == owner_user_id]
    return sorted(proposals, key=lambda item: item.created_at, reverse=True)


def create_bone_proposal(request: CreateBoneProposalRequest, owner_user_id: str | None = None) -> StructureProposal:
    return RUNTIME.create_bone_proposal(
        StructureProposal(
            proposal_id=new_id("proposal"),
            owner_user_id=owner_user_id,
            requested_by=request.requested_by or owner_user_id,
            name=request.name,
            structure_type=request.structure_type,
            definition=request.definition,
        )
    )


def decide_structure_proposal(proposal_id: str, request: DecideProposalRequest, approved: bool, owner_user_id: str | None = None) -> StructureProposal | None:
    proposal = RUNTIME.stores.structure_proposals.get(proposal_id)
    if proposal is None or (owner_user_id is not None and proposal.owner_user_id != owner_user_id):
        return None
    return RUNTIME.decide_structure_proposal(proposal_id, approved, request.reason, owner_user_id)


def list_reviews(owner_user_id: str | None = None) -> list[ReviewRequest]:
    reviews = RUNTIME.stores.reviews.values()
    if owner_user_id is not None:
        reviews = [review for review in reviews if review.owner_user_id == owner_user_id]
    return sorted(reviews, key=lambda item: item.created_at, reverse=True)


def create_review(request: CreateReviewRequest, owner_user_id: str | None = None) -> ReviewRequest:
    return RUNTIME.create_review(
        ReviewRequest(
            review_id=new_id("review"),
            owner_user_id=owner_user_id,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            action=request.action,
            before=request.before,
            after=request.after,
            reason=request.reason,
        )
    )


def decide_review(review_id: str, request: DecideReviewRequest, approved: bool, owner_user_id: str | None = None) -> ReviewRequest | None:
    review = RUNTIME.stores.reviews.get(review_id)
    if review is None or (owner_user_id is not None and review.owner_user_id != owner_user_id):
        return None
    return RUNTIME.decide_review(review_id, approved, owner_user_id, request.reason)


def _owned_structure_request(request_id: str, owner_user_id: str | None = None) -> StructureRequest | None:
    for item in list_structure_requests(owner_user_id):
        if item.request_id == request_id:
            return item
    return None


def runtime_event_for_structure_request(
    request: StructureRequest,
    message: str,
    *,
    contract_id: str | None = None,
):
    from preon_systems_cell.engine import runtime_event
    from preon_systems_cell.models import RuntimeEventType

    return runtime_event(
        RuntimeEventType.SKELETON,
        message,
        organism_id=request.organism_id,
        signal_id=request.signal_id,
        contract_id=contract_id,
        request_id=request.request_id,
        requested_contract=request.requested_contract,
        status=request.status,
    )
