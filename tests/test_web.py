from fastapi.testclient import TestClient
import pytest

from preon_systems_cell.api import RUNTIME
from preon_systems_cell.auth import _attempts
from preon_systems_cell.web import app


client = TestClient(app)
PASSWORD = "Correct-Horse-Battery-42!"


@pytest.fixture(autouse=True)
def reset_runtime_and_auth():
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
    _attempts.clear()
    client.cookies.clear()
    response = client.post("/auth/signup", json={"email": "primary@example.com", "password": PASSWORD})
    assert response.status_code in {200, 409}
    if response.status_code == 409:
        assert client.post("/auth/login", json={"email": "primary@example.com", "password": PASSWORD}).status_code == 200


def test_health_reports_organism_runtime():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["runtime"] == "organism"


def test_full_organism_api_flow():
    created = client.post(
        "/api/organisms",
        json={"identity_profile": {"name": "Sales Organism", "purpose": "Drive safe go-to-market tasks"}, "goals": ["qualify leads"]},
    )
    organism_id = created.json()["organism"]["organism_id"]

    wake = client.post(f"/api/organisms/{organism_id}/wake")
    signal = client.post(f"/api/organisms/{organism_id}/signals", json={"type": "calculate", "payload": {"expression": "40+2"}})
    detail = client.get(f"/api/organisms/{organism_id}")
    hibernate = client.post(f"/api/organisms/{organism_id}/hibernate")

    assert created.status_code == 200
    assert wake.json()["organism"]["lifecycle_state"] == "active"
    assert signal.json()["protein"]["payload"]["result"] == 42.0
    assert signal.json()["signal"]["actor"]["actor_id"] == client.get("/auth/me").json()["user"]["id"]
    assert detail.json()["proteins"]
    assert hibernate.json()["organism"]["lifecycle_state"] == "hibernated"


def test_contract_flow_and_auth_boundary():
    created = client.post("/api/organisms", json={})
    organism_id = created.json()["organism"]["organism_id"]
    contract = client.post(
        "/api/contracts",
        json={"name": "CustomerProfileService.getByUserId", "allowed_actions": ["read_customer_profile"]},
    )

    signal = client.post(
        f"/api/organisms/{organism_id}/signals",
        json={"type": "contract.call", "payload": {"contract": "CustomerProfileService.getByUserId", "action": "read_customer_profile"}},
    )
    blocked_deprecation = client.post(f"/api/contracts/{contract.json()['contract']['contract_id']}/deprecate")

    other = TestClient(app)
    assert other.post("/auth/signup", json={"email": "other@example.com", "password": PASSWORD}).status_code == 200
    forbidden_detail = other.get(f"/api/organisms/{organism_id}")

    assert signal.status_code == 200
    assert signal.json()["protein"]["payload"]["contract"] == "CustomerProfileService.getByUserId"
    assert blocked_deprecation.status_code == 409
    assert forbidden_detail.status_code == 404


def test_structure_request_routes_resolve_and_block():
    created = client.post("/api/organisms", json={})
    organism_id = created.json()["organism"]["organism_id"]

    missing = client.post(
        f"/api/organisms/{organism_id}/signals",
        json={"type": "contract.call", "payload": {"contract": "MissingContract", "action": "read"}},
    )
    request_id = missing.json()["structure_request"]["request_id"]

    listed = client.get("/api/structure-requests")
    resolved = client.post(f"/api/structure-requests/{request_id}/resolve", json={"contract_id": "contract-created"})

    missing_again = client.post(
        f"/api/organisms/{organism_id}/signals",
        json={"type": "contract.call", "payload": {"contract": "BlockedContract", "action": "read"}},
    )
    blocked = client.post(
        f"/api/structure-requests/{missing_again.json()['structure_request']['request_id']}/block",
        json={"reason": "not approved"},
    )

    assert listed.status_code == 200
    assert listed.json()["structure_requests"][0]["requested_contract"] == "MissingContract"
    assert resolved.json()["structure_request"]["status"] == "resolved"
    assert blocked.json()["structure_request"]["status"] == "blocked"


def test_removed_simulator_routes_return_404():
    assert client.get("/api/default-scenario").status_code == 404
    assert client.get("/api/runs").status_code == 404
    assert client.post("/api/runs").status_code == 404
    assert client.get("/api/runs/run-test").status_code == 404


def test_v2_cells_memory_replay_metrics_and_reviews():
    created = client.post("/api/organisms", json={})
    organism_id = created.json()["organism"]["organism_id"]

    cell = client.post(
        f"/api/organisms/{organism_id}/cells",
        json={"tissue_id": "analysis", "cell_type": "specialist", "expression_profile": {"arithmetic": 0.9}},
    )
    memory = client.post(
        f"/api/organisms/{organism_id}/memory",
        json={"scope": "organism", "kind": "calculate", "payload": {"note": "remember arithmetic"}},
    )
    signal = client.post(f"/api/organisms/{organism_id}/signals", json={"type": "calculate", "payload": {"expression": "5+5"}})
    signal_id = signal.json()["signal"]["signal_id"]
    replay = client.post(f"/api/organisms/{organism_id}/signals/{signal_id}/replay")
    metrics = client.get(f"/api/metrics/organisms/{organism_id}")
    bundle = client.get(f"/api/organisms/{organism_id}/debug-bundle")
    review = client.post(
        "/api/reviews",
        json={"resource_type": "organism", "resource_id": organism_id, "action": "review_v2", "reason": "test"},
    )
    approved = client.post(f"/api/reviews/{review.json()['review']['review_id']}/approve", json={"reason": "ok"})

    assert cell.status_code == 200
    assert cell.json()["cell"]["tissue_id"] == "analysis"
    assert memory.status_code == 200
    assert signal.json()["protein"]["payload"]["result"] == 10.0
    assert replay.status_code == 200
    assert replay.json()["replay"]["divergence_report"]["protein_payload_match"] is True
    assert metrics.json()["metrics"]["proteins"] >= 1
    assert bundle.json()["bundle"]["redaction"]["auth"] == "excluded"
    assert approved.json()["review"]["status"] == "approved"


def test_v2_capability_policy_genome_and_maintenance_routes():
    created = client.post("/api/organisms", json={})
    organism_id = created.json()["organism"]["organism_id"]

    capability = client.post("/api/capabilities", json={"name": "customer.profile.read", "schema": {"input": "object"}})
    contract = client.post(
        "/api/contracts",
        json={
            "name": "AdapterContract",
            "allowed_actions": ["read"],
            "adapter_id": "adapter.customer",
            "input_mapping": {"user_id": "id"},
            "capability_ids": [capability.json()["capability"]["capability_id"]],
            "test_vectors": [{"input": {"user_id": "u1"}, "expected": {"id": "u1"}}],
        },
    )
    adapter_report = client.post(f"/api/contracts/{contract.json()['contract']['contract_id']}/validate-adapter")
    policy_sim = client.post(
        f"/api/organisms/{organism_id}/policies/simulate",
        json={"signal": {"type": "calculate", "payload": {"expression": "1+1"}}},
    )
    genome_preview = client.post(
        f"/api/organisms/{organism_id}/genome/preview",
        json={"signal_type": "calculate", "payload": {"expression": "1+1"}},
    )
    maintenance = client.post("/api/maintenance/run")

    assert adapter_report.json()["report"]["valid"] is True
    assert policy_sim.json()["membrane_decision"]["action"] == "accept"
    assert genome_preview.json()["preview"]["module_id"] == "arithmetic"
    assert maintenance.json()["run"]["status"] == "completed"


def test_v3_zygote_birth_and_growth_template_routes():
    mother = client.post("/api/organisms", json={"identity_profile": {"name": "Mother", "purpose": "memory safety"}}).json()["organism"]
    father = client.post("/api/organisms", json={"identity_profile": {"name": "Father", "purpose": "reasoning optimization"}}).json()["organism"]

    negotiation = client.post(
        "/api/reproduction/negotiate",
        json={"mother_organism_id": mother["organism_id"], "father_organism_id": father["organism_id"]},
    )
    zygote = client.post(
        "/api/reproduction/zygote",
        json={"mother_organism_id": mother["organism_id"], "father_organism_id": father["organism_id"]},
    )
    zygote_id = zygote.json()["zygote"]["zygote_id"]
    developed = client.post(f"/api/zygotes/{zygote_id}/develop", json={"target_stage": "embryo", "food_payload": {"lesson": "cell fate"}})
    born = client.post(f"/api/zygotes/{zygote_id}/birth")
    child_id = born.json()["organism"]["organism_id"]
    detail = client.get(f"/api/organisms/{child_id}")

    assert negotiation.json()["negotiation"]["selected"] is True
    assert zygote.json()["zygote"]["genome"]["organ_cell_dna"]["brain"]["cell_genome_id"] == "brain-cell-genome"
    assert developed.json()["zygote"]["stage"] == "embryo"
    assert born.json()["organism"]["development_stage"] == "born"
    assert len(detail.json()["cells"]) == 22
    assert {cell["organ_id"] for cell in detail.json()["cells"] if cell["organ_id"] != "core"} == {
        "brain",
        "heart",
        "left-arm",
        "right-arm",
        "left-leg",
        "right-leg",
    }


def test_v3_cell_division_copies_cell_genome():
    organism = client.post("/api/organisms", json={}).json()["organism"]
    organism_id = organism["organism_id"]
    growth = client.post(f"/api/organisms/{organism_id}/growth/apply-template", json={"template_name": "human_minimal_v3"})
    parent = next(cell for cell in growth.json()["growth"]["cells"] if cell["organ_id"] == "brain")

    divided = client.post(f"/api/organisms/{organism_id}/cells/{parent['cell_id']}/divide", json={"mode": "symmetric"})
    detail = client.get(f"/api/organisms/{organism_id}")
    daughters = [cell for cell in detail.json()["cells"] if cell["parent_cell_id"] == parent["cell_id"]]

    assert divided.status_code == 200
    assert divided.json()["division"]["genome_copied"] is True
    assert len(daughters) == 2
    assert {cell["cell_genome_id"] for cell in daughters} == {parent["cell_genome_id"]}


def test_v3_food_oxygen_health_soul_and_bone_routes():
    organism = client.post("/api/organisms", json={}).json()["organism"]
    organism_id = organism["organism_id"]

    food = client.post(f"/api/organisms/{organism_id}/food", json={"food_type": "training_data", "payload": {"sample": "hello"}})
    oxygen = client.post(
        f"/api/organisms/{organism_id}/oxygen",
        json={"compute_units": 12, "memory_units": 8, "storage_units": 20, "gpu_units": 1, "restricted": False},
    )
    health = client.get(f"/api/organisms/{organism_id}/health")
    proposal = client.post("/api/bones/proposals", json={"name": "DurableAdapterSchema", "structure_type": "schema", "definition": {"input": "object"}})
    approved = client.post(f"/api/bones/proposals/{proposal.json()['proposal']['proposal_id']}/approve", json={"reason": "fits v3 bone layer"})
    bones = client.get("/api/bones")
    soul = client.post(f"/api/organisms/{organism_id}/die")
    reincarnated = client.post(f"/api/souls/{soul.json()['soul']['soul_id']}/reincarnate")

    assert food.json()["food"]["food_type"] == "training_data"
    assert oxygen.json()["oxygen"]["compute_units"] == 12
    assert health.json()["health"]["cell_count"] >= 1
    assert approved.json()["proposal"]["status"] == "approved"
    assert bones.json()["bones"][0]["name"] == "DurableAdapterSchema"
    assert soul.json()["soul"]["snapshot"]["organism"]["organism_id"] == organism_id
    assert reincarnated.json()["organism"]["growth_state"]["reincarnated_from_soul_id"] == soul.json()["soul"]["soul_id"]
