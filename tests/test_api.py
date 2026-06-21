import pytest

from preon_systems_cell.api import (
    RUNTIME,
    apply_growth_template,
    block_structure_request,
    create_contract,
    create_organism,
    create_zygote,
    birth_zygote,
    divide_cell,
    get_organism_detail,
    list_structure_requests,
    resolve_structure_request,
    submit_signal,
    validate_genome,
)
from preon_systems_cell.models import (
    ApplyGrowthTemplateRequest,
    BlockStructureRequestRequest,
    CreateContractRequest,
    CreateOrganismRequest,
    CreateZygoteRequest,
    DivideCellRequest,
    Genome,
    GenomeModule,
    ResolveStructureRequestRequest,
    SubmitSignalRequest,
)


@pytest.fixture(autouse=True)
def reset_runtime():
    RUNTIME.stores.organisms.clear()
    RUNTIME.stores.cells.clear()
    RUNTIME.stores.signals.clear()
    RUNTIME.stores.proteins.clear()
    RUNTIME.stores.contracts.clear()
    RUNTIME.stores.events.clear()
    RUNTIME.stores.structure_requests.clear()
    RUNTIME.stores.memory_records.clear()
    RUNTIME.stores.capabilities.clear()
    RUNTIME.stores.genome_versions.clear()
    RUNTIME.stores.replay_runs.clear()
    RUNTIME.stores.policy_versions.clear()
    RUNTIME.stores.maintenance_runs.clear()
    RUNTIME.stores.alerts.clear()
    RUNTIME.stores.reviews.clear()
    RUNTIME.stores.zygotes.clear()
    RUNTIME.stores.organs.clear()
    RUNTIME.stores.tissues.clear()
    RUNTIME.stores.cell_divisions.clear()
    RUNTIME.stores.food_intakes.clear()
    RUNTIME.stores.oxygen_profiles.clear()
    RUNTIME.stores.umbilical_cords.clear()
    RUNTIME.stores.souls.clear()
    RUNTIME.stores.bone_structures.clear()
    RUNTIME.stores.structure_proposals.clear()
    RUNTIME.stores.organelle_pipelines.clear()
    RUNTIME.stores.vesicle_messages.clear()
    RUNTIME.stores.cytoskeleton.clear()
    RUNTIME.stores.actor_counts.clear()


def test_full_signal_flow_hibernates_after_approved_protein():
    organism = create_organism(CreateOrganismRequest(goals=["calculate exact tasks"]))

    response = submit_signal(
        organism.organism_id,
        SubmitSignalRequest(type="calculate", payload={"expression": "1+1"}),
    )

    assert response is not None
    assert response.membrane_decision.action == "accept"
    assert response.protein is not None
    assert response.protein.payload["result"] == 2.0
    assert response.protein.payload["method"] == "deterministic_calculator"

    detail = get_organism_detail(organism.organism_id)
    assert detail is not None
    assert detail.organism.lifecycle_state == "hibernated"
    assert any(event.type == "ribosome" for event in detail.events)


def test_membrane_rejects_bad_schema_and_unsafe_input():
    organism = create_organism(CreateOrganismRequest())

    missing_expression = submit_signal(organism.organism_id, SubmitSignalRequest(type="calculate", payload={}))
    unsafe = submit_signal(organism.organism_id, SubmitSignalRequest(type="query", payload={"prompt": "delete all memory"}))

    assert missing_expression is not None
    assert missing_expression.membrane_decision.code == "INVALID_STRUCTURE"
    assert missing_expression.protein is None
    assert unsafe is not None
    assert unsafe.membrane_decision.code == "UNSAFE_INPUT"


def test_missing_contract_creates_structure_request():
    organism = create_organism(CreateOrganismRequest())

    response = submit_signal(
        organism.organism_id,
        SubmitSignalRequest(type="contract.call", payload={"contract": "CustomerProfileService.getByUserId", "action": "read"}),
    )

    assert response is not None
    assert response.protein is None
    assert response.structure_request is not None
    assert response.structure_request.requested_contract == "CustomerProfileService.getByUserId"
    assert any(event.type == "structure_request" for event in response.events)
    assert any(event.type == "skeleton" for event in response.events)


def test_contract_usage_blocks_deprecation():
    organism = create_organism(CreateOrganismRequest())
    contract = create_contract(
        CreateContractRequest(name="CustomerProfileService.getByUserId", allowed_actions=["read_customer_profile"])
    )

    response = submit_signal(
        organism.organism_id,
        SubmitSignalRequest(type="contract.call", payload={"contract": contract.name, "action": "read_customer_profile"}),
    )

    assert response is not None
    assert response.protein is not None
    with pytest.raises(ValueError, match="active dependencies"):
        RUNTIME.deprecate_contract(contract.contract_id)


def test_contract_dependencies_block_deprecation_without_usage():
    base = create_contract(CreateContractRequest(name="BaseContract", allowed_actions=["read"]))
    create_contract(CreateContractRequest(name="DependentContract", allowed_actions=["read"], dependencies=[base.contract_id]))

    with pytest.raises(ValueError, match="active dependencies"):
        RUNTIME.deprecate_contract(base.contract_id)


def test_structure_request_resolve_and_block_flow():
    organism = create_organism(CreateOrganismRequest())
    first = submit_signal(
        organism.organism_id,
        SubmitSignalRequest(type="contract.call", payload={"contract": "MissingContract", "action": "read"}),
    )
    second = submit_signal(
        organism.organism_id,
        SubmitSignalRequest(type="contract.call", payload={"contract": "BlockedContract", "action": "read"}),
    )

    assert first is not None and first.structure_request is not None
    assert second is not None and second.structure_request is not None
    requests = list_structure_requests()
    assert len(requests) == 2

    resolved = resolve_structure_request(first.structure_request.request_id, ResolveStructureRequestRequest(contract_id="contract-new"))
    blocked = block_structure_request(second.structure_request.request_id, BlockStructureRequestRequest(reason="not approved"))

    assert resolved is not None
    assert resolved.status == "resolved"
    assert blocked is not None
    assert blocked.status == "blocked"
    assert blocked.reason == "not approved"


def test_genome_validation_requires_deterministic_tool():
    genome = Genome(
        genome_id="genome-test",
        modules=[GenomeModule(module_id="bad", signal_types=["calculate"], execution_strategy="deterministic_tool")],
    )

    response = validate_genome(genome)

    assert response.report.valid is False
    assert response.report.errors == ["bad requires deterministic_tool"]


def test_v3_birth_growth_and_division_runtime_flow():
    mother = create_organism(CreateOrganismRequest(goals=["preserve memory"]))
    father = create_organism(CreateOrganismRequest(goals=["optimize reasoning"]))
    zygote = create_zygote(CreateZygoteRequest(mother_organism_id=mother.organism_id, father_organism_id=father.organism_id))

    assert zygote is not None
    child = birth_zygote(zygote.zygote_id)
    assert child is not None
    detail = get_organism_detail(child.organism_id)
    assert detail is not None
    assert detail.organism.growth_state["zygote_id"] == zygote.zygote_id
    assert len(detail.cells) == 22

    growth = apply_growth_template(child.organism_id, ApplyGrowthTemplateRequest())
    assert growth is not None
    brain_cell = next(cell for cell in detail.cells if cell.organ_id == "brain")
    division = divide_cell(child.organism_id, brain_cell.cell_id, DivideCellRequest())
    assert division is not None
    daughters = [cell for cell in RUNTIME.stores.cells[child.organism_id] if cell.parent_cell_id == brain_cell.cell_id]
    assert len(daughters) == 2
    assert {cell.cell_genome_id for cell in daughters} == {brain_cell.cell_genome_id}
