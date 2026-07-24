from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from preon_systems_cell.engine import OrganismRuntime, new_id
from preon_systems_cell.models import (
    CellRecord,
    OrganismRecord,
    StructureProposal,
)
from preon_systems_cell.skeletal import OSTEOBLAST, OSTEOCLAST, OSTEOCYTE
from preon_systems_cell.storage.postgres import PostgresRuntimeStore


def _organism(runtime: OrganismRuntime, *, owner: str = "owner-1") -> OrganismRecord:
    return runtime.create_organism(
        OrganismRecord(organism_id=new_id("organism"), owner_user_id=owner)
    )


def _growth_proposal(
    organism: OrganismRecord,
    target: CellRecord,
    *,
    key: str = "memory-schema-v1",
) -> StructureProposal:
    return StructureProposal(
        proposal_id=new_id("proposal"),
        organism_id=organism.organism_id,
        owner_user_id=organism.owner_user_id,
        name="organism-memory",
        structure_type="database_schema",
        provider="postgres",
        definition={"schema": "organism_memory", "namespace": organism.organism_id},
        idempotency_key=key,
        target_cell_id=target.cell_id,
        requested_permissions=["read", "write"],
    )


def test_genesis_seeds_first_class_skeletal_cells() -> None:
    runtime = OrganismRuntime()
    organism = _organism(runtime)

    skeletal = [
        cell
        for cell in runtime.stores.cells[organism.organism_id]
        if cell.tissue_id == "skeletal"
    ]

    assert {cell.cell_type for cell in skeletal} == {OSTEOBLAST, OSTEOCLAST, OSTEOCYTE}
    assert all(cell.organism_id == organism.organism_id for cell in skeletal)
    assert all(cell.cell_genome_id for cell in skeletal)
    assert organism.tissue_templates["skeletal"]["cell_types"] == [OSTEOBLAST, OSTEOCLAST, OSTEOCYTE]


def test_osteoblast_grows_resource_and_scoped_grant() -> None:
    runtime = OrganismRuntime()
    organism = _organism(runtime)
    target = next(cell for cell in runtime.stores.cells[organism.organism_id] if cell.cell_type == "worker")

    proposal = runtime.create_bone_proposal(_growth_proposal(organism, target))
    osteoblast = next(
        cell
        for cell in runtime.stores.cells[organism.organism_id]
        if cell.cell_type == OSTEOBLAST
    )

    assert proposal.proposed_by_cell_id == osteoblast.cell_id
    assert proposal.plan_digest
    assert proposal.plan["provider"] == "postgres"

    approved = runtime.decide_structure_proposal(
        proposal.proposal_id,
        True,
        "memory needs durable structure",
        organism.owner_user_id,
        proposal.plan_digest,
    )
    resource = runtime.stores.bone_structures[approved.resulting_bone_id or ""]
    grant = next(iter(runtime.stores.resource_grants.values()))

    assert approved.apply_status == "applied"
    assert resource.organism_id == organism.organism_id
    assert resource.created_by_cell_id == osteoblast.cell_id
    assert resource.provider == "postgres"
    assert resource.observed_state["exists"] is True
    assert grant.resource_id == resource.bone_id
    assert grant.cell_id == target.cell_id
    assert grant.permissions == ["read", "write"]
    assert grant.namespace == organism.organism_id
    assert grant.credential_ref is None


def test_growth_is_idempotent_and_plan_digest_is_bound_to_approval() -> None:
    runtime = OrganismRuntime()
    organism = _organism(runtime)
    target = runtime.stores.cells[organism.organism_id][0]
    first = runtime.create_bone_proposal(_growth_proposal(organism, target))
    duplicate = runtime.create_bone_proposal(_growth_proposal(organism, target))

    assert duplicate.proposal_id == first.proposal_id
    assert len(runtime.stores.structure_proposals) == 1

    with pytest.raises(ValueError, match="plan digest"):
        runtime.decide_structure_proposal(
            first.proposal_id,
            True,
            "stale review",
            organism.owner_user_id,
            "wrong-digest",
        )
    assert runtime.stores.structure_proposals[first.proposal_id].status == "pending"
    assert not runtime.stores.bone_structures


def test_remodeling_is_owned_by_osteoclast_and_cannot_cross_organisms() -> None:
    runtime = OrganismRuntime()
    first = _organism(runtime, owner="owner-1")
    second = _organism(runtime, owner="owner-2")
    target = runtime.stores.cells[first.organism_id][0]
    growth = runtime.create_bone_proposal(_growth_proposal(first, target))
    growth = runtime.decide_structure_proposal(
        growth.proposal_id,
        True,
        "grow",
        first.owner_user_id,
        growth.plan_digest,
    )
    original_provider_ref = runtime.stores.bone_structures[
        growth.resulting_bone_id or ""
    ].provider_resource_ref

    remodel = runtime.create_bone_proposal(
        StructureProposal(
            proposal_id=new_id("proposal"),
            organism_id=first.organism_id,
            owner_user_id=first.owner_user_id,
            name="organism-memory-v2",
            structure_type="database_schema",
            operation="remodel",
            provider="postgres",
            definition={"schema": "organism_memory", "version": 2},
            target_resource_id=growth.resulting_bone_id,
        )
    )
    osteoclast = next(
        cell
        for cell in runtime.stores.cells[first.organism_id]
        if cell.cell_type == OSTEOCLAST
    )
    assert remodel.proposed_by_cell_id == osteoclast.cell_id
    remodeled = runtime.decide_structure_proposal(
        remodel.proposal_id,
        True,
        "add versioned structure",
        first.owner_user_id,
        remodel.plan_digest,
    )
    remodeled_resource = runtime.stores.bone_structures[remodeled.resulting_bone_id or ""]
    assert remodeled_resource.generation == 2
    assert remodeled_resource.provider_resource_ref == original_provider_ref

    with pytest.raises(ValueError, match="does not belong"):
        runtime.create_bone_proposal(
            remodel.model_copy(
                update={
                    "proposal_id": new_id("proposal"),
                    "organism_id": second.organism_id,
                    "owner_user_id": second.owner_user_id,
                    "idempotency_key": None,
                    "proposed_by_cell_id": None,
                }
            )
        )


def test_resource_grant_revocation_is_owner_scoped() -> None:
    runtime = OrganismRuntime()
    organism = _organism(runtime)
    target = runtime.stores.cells[organism.organism_id][0]
    proposal = runtime.create_bone_proposal(_growth_proposal(organism, target))
    runtime.decide_structure_proposal(
        proposal.proposal_id,
        True,
        "grow",
        organism.owner_user_id,
        proposal.plan_digest,
    )
    grant = next(iter(runtime.stores.resource_grants.values()))

    with pytest.raises(KeyError):
        runtime.revoke_resource_grant(grant.grant_id, "different-owner")

    revoked = runtime.revoke_resource_grant(grant.grant_id, organism.owner_user_id)
    assert revoked.status == "revoked"
    assert revoked.revoked_at is not None


def test_postgres_reload_reconstructs_phase5a_control_plane() -> None:
    now = datetime.now(UTC)
    resource_row = {
        "bone_id": "bone-1",
        "organism_id": "organism-1",
        "owner_user_id": "owner-1",
        "name": "memory",
        "structure_type": "database_schema",
        "definition": {"schema": "memory"},
        "provider": "postgres",
        "provider_resource_ref": "postgres://organism-1/proposal-1",
        "observed_state": {"exists": True},
        "generation": 1,
        "health": "healthy",
        "created_by_cell_id": "osteoblast-1",
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    proposal_row = {
        "proposal_id": "proposal-1",
        "organism_id": "organism-1",
        "owner_user_id": "owner-1",
        "requested_by": "owner-1",
        "proposed_by_cell_id": "osteoblast-1",
        "name": "memory",
        "structure_type": "database_schema",
        "operation": "grow",
        "provider": "postgres",
        "definition": {"schema": "memory"},
        "plan": {"operation": "grow"},
        "plan_digest": "digest",
        "idempotency_key": "memory-v1",
        "target_resource_id": None,
        "target_cell_id": "worker-1",
        "requested_permissions": ["read"],
        "status": "approved",
        "apply_status": "applied",
        "resulting_bone_id": "bone-1",
        "decision_reason": "approved",
        "created_at": now,
        "decided_at": now,
        "applied_at": now,
    }
    grant_row = {
        "grant_id": "grant-1",
        "organism_id": "organism-1",
        "owner_user_id": "owner-1",
        "resource_id": "bone-1",
        "cell_id": "worker-1",
        "permissions": ["read"],
        "namespace": "organism-1",
        "provider": "postgres",
        "credential_ref": None,
        "status": "active",
        "created_by_cell_id": "osteoblast-1",
        "created_at": now,
        "revoked_at": None,
    }

    class Connection:
        async def fetch(self, query, *_args):
            if "FROM bone_structures" in query:
                return [resource_row]
            if "FROM structure_proposals" in query:
                return [proposal_row]
            if "FROM resource_grants" in query:
                return [grant_row]
            return []

    class Acquire:
        async def __aenter__(self):
            return Connection()

        async def __aexit__(self, *_args):
            return None

    class Pool:
        def acquire(self):
            return Acquire()

    stores = asyncio.run(PostgresRuntimeStore(Pool()).load_stores())

    assert stores.bone_structures["bone-1"].health == "healthy"
    assert stores.structure_proposals["proposal-1"].apply_status == "applied"
    assert stores.resource_grants["grant-1"].permissions == ["read"]
