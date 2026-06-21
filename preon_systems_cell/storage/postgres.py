from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
from typing import Any

from preon_systems_cell.engine import RuntimeStores
from preon_systems_cell.models import (
    BoneStructureRecord,
    CellDivisionRecord,
    CellRecord,
    Contract,
    CytoskeletonTopology,
    FoodIntake,
    Genome,
    OrganRecord,
    OrganellePipeline,
    OrganismRecord,
    OxygenProfile,
    Protein,
    RuntimeEvent,
    Signal,
    SoulSnapshot,
    StructureProposal,
    StructureRequest,
    TissueRecord,
    UmbilicalCord,
    VesicleMessage,
    ZygoteRecord,
)

try:
    import asyncpg
except ImportError:  # pragma: no cover - optional dependency guard
    asyncpg = None  # type: ignore[assignment]


SQL_DIR = Path(__file__).resolve().parent / "sql"
SCHEMA_PATH = SQL_DIR / "schema.sql"
logger = logging.getLogger("preon_systems_cell.storage.postgres")


@dataclass(frozen=True)
class PostgresSettings:
    database_url: str | None = None
    min_pool_size: int = 1
    max_pool_size: int = 8
    command_timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "PostgresSettings":
        return cls(
            database_url=os.getenv("PREON_DATABASE_URL") or os.getenv("DATABASE_URL"),
            min_pool_size=int(os.getenv("PREON_DB_POOL_MIN", "1")),
            max_pool_size=int(os.getenv("PREON_DB_POOL_MAX", "8")),
            command_timeout=float(os.getenv("PREON_DB_COMMAND_TIMEOUT", "30")),
        )


class PostgresUnavailableError(RuntimeError):
    pass


class PostgresRuntimeStore:
    def __init__(self, pool: Any) -> None:
        self._pool = pool

    @classmethod
    async def create(cls, settings: PostgresSettings) -> "PostgresRuntimeStore":
        if not settings.database_url:
            raise PostgresUnavailableError("PREON_DATABASE_URL is not configured")
        if asyncpg is None:
            raise PostgresUnavailableError('asyncpg is not installed; run python -m pip install -e ".[postgres]"')
        pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=settings.min_pool_size,
            max_size=settings.max_pool_size,
            command_timeout=settings.command_timeout,
        )
        store = cls(pool)
        try:
            await store.apply_schema()
        except Exception:
            await pool.close()
            raise
        return store

    async def close(self) -> None:
        await self._pool.close()

    async def apply_schema(self) -> None:
        async with self._pool.acquire() as connection:
            await connection.execute(SCHEMA_PATH.read_text(encoding="utf-8"))

    async def load_stores(self) -> RuntimeStores:
        stores = RuntimeStores()
        async with self._pool.acquire() as connection:
            for row in await connection.fetch("SELECT * FROM genomes"):
                genome = Genome(
                    genome_id=row["genome_id"],
                    version=row["version"],
                    core_instruction_set=_decode_json(row["core_instruction_set"]),
                    modules=_decode_json(row["modules"]),
                    regulatory_rules=_decode_json(row["regulatory_rules"]),
                    capability_registry=_decode_json(row["capability_registry"]),
                    constraints=_decode_json(row["constraints"]),
                )
                stores.genomes[genome.genome_id] = genome

            for row in await connection.fetch("SELECT * FROM organisms"):
                row_data = dict(row)
                organism = OrganismRecord(
                    organism_id=row["organism_id"],
                    owner_user_id=row["owner_user_id"],
                    lifecycle_state=row["lifecycle_state"],
                    identity_profile=_decode_json(row["identity_profile"]),
                    long_term_memory=_decode_json(row["long_term_memory"]),
                    goals=_decode_json(row["goals"]),
                    policies=_decode_json(row["policies"]),
                    organ_registry=_decode_json(row["organ_registry"]),
                    tissue_templates=_decode_json(row["tissue_templates"]),
                    cell_blueprints=_decode_json(row["cell_blueprints"]),
                    genome_id=row["genome_id"],
                    development_stage=row_data.get("development_stage", "born"),
                    growth_state=_decode_json(row_data.get("growth_state", "{}")),
                    lineage_log=_decode_json(row["lineage_log"]),
                    last_state_snapshot=_decode_json(row["last_state_snapshot"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                stores.organisms[organism.organism_id] = organism

            for row in await connection.fetch("SELECT * FROM cells ORDER BY created_at"):
                row_data = dict(row)
                cell = CellRecord(
                    cell_id=row["cell_id"],
                    organism_id=row["organism_id"],
                    organ_id=row_data.get("organ_id", "core"),
                    tissue_id=row["tissue_id"],
                    cell_type=row["cell_type"],
                    cell_genome_id=row_data.get("cell_genome_id"),
                    expression_profile=_decode_json(row["expression_profile"]),
                    local_state=_decode_json(row["local_state"]),
                    lifecycle_state=row["lifecycle_state"],
                    health_state=row_data.get("health_state", "alive"),
                    health_score=row_data.get("health_score", 1.0),
                    parent_cell_id=row_data.get("parent_cell_id"),
                    generation=row_data.get("generation", 0),
                    resource_budget=_decode_json(row["resource_budget"]),
                    created_at=row["created_at"],
                    last_active_at=row["last_active_at"],
                )
                stores.cells.setdefault(cell.organism_id, []).append(cell)

            for row in await connection.fetch("SELECT * FROM signals ORDER BY created_at"):
                signal = Signal(
                    signal_id=row["signal_id"],
                    organism_id=row["organism_id"],
                    actor=_decode_json(row["actor"]),
                    type=row["type"],
                    payload=_decode_json(row["payload"]),
                    context_refs=_decode_json(row["context_refs"]),
                    priority=row["priority"],
                    metadata=_decode_json(row["metadata"]),
                    created_at=row["created_at"],
                )
                stores.signals.setdefault(signal.organism_id, []).append(signal)

            for row in await connection.fetch("SELECT * FROM proteins ORDER BY created_at"):
                protein = Protein(
                    protein_id=row["protein_id"],
                    organism_id=row["organism_id"],
                    source_signal_id=row["source_signal_id"],
                    type=row["type"],
                    payload=_decode_json(row["payload"]),
                    confidence=row["confidence"],
                    status=row["status"],
                    validation_report=_decode_json(row["validation_report"]),
                    created_at=row["created_at"],
                )
                stores.proteins.setdefault(protein.organism_id, []).append(protein)

            for row in await connection.fetch("SELECT * FROM contracts ORDER BY created_at"):
                row_data = dict(row)
                contract = Contract(
                    contract_id=row["contract_id"],
                    owner_user_id=row["owner_user_id"],
                    name=row["name"],
                    schema=_decode_json(row["schema"]),
                    allowed_actions=_decode_json(row["allowed_actions"]),
                    permissions=_decode_json(row["permissions"]),
                    rate_limits=_decode_json(row["rate_limits"]),
                    dependencies=_decode_json(row_data.get("dependencies", "[]")),
                    created_by=row_data.get("created_by"),
                    deprecated_reason=row_data.get("deprecated_reason"),
                    status=row["status"],
                    usage_count=row["usage_count"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                stores.contracts[contract.contract_id] = contract

            for row in await connection.fetch("SELECT * FROM runtime_events ORDER BY created_at"):
                event = RuntimeEvent(
                    event_id=row["event_id"],
                    organism_id=row["organism_id"],
                    cell_id=row["cell_id"],
                    signal_id=row["signal_id"],
                    protein_id=row["protein_id"],
                    contract_id=row["contract_id"],
                    type=row["type"],
                    message=row["message"],
                    values=_decode_json(row["values"]),
                    created_at=row["created_at"],
                )
                stores.events.setdefault(event.organism_id or "global", []).append(event)

            for row in await connection.fetch("SELECT * FROM structure_requests ORDER BY created_at"):
                request = StructureRequest(
                    request_id=row["request_id"],
                    organism_id=row["organism_id"],
                    signal_id=row["signal_id"],
                    requested_contract=row["requested_contract"],
                    reason=row["reason"],
                    status=row["status"],
                    created_at=row["created_at"],
                )
                stores.structure_requests.setdefault(request.organism_id, []).append(request)

            for row in await connection.fetch("SELECT * FROM zygotes ORDER BY created_at"):
                zygote = ZygoteRecord(
                    zygote_id=row["zygote_id"],
                    owner_user_id=row["owner_user_id"],
                    mother_organism_id=row["mother_organism_id"],
                    father_organism_id=row["father_organism_id"],
                    genome=_decode_json(row["genome"]),
                    stage=row["stage"],
                    oxygen_restricted=row["oxygen_restricted"],
                    food_log=_decode_json(row["food_log"]),
                    founder_plan=_decode_json(row["founder_plan"]),
                    born_organism_id=row["born_organism_id"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                stores.zygotes[zygote.zygote_id] = zygote

            for row in await connection.fetch("SELECT * FROM organs ORDER BY created_at"):
                organ = OrganRecord(
                    organ_id=row["organ_id"],
                    organism_id=row["organism_id"],
                    name=row["name"],
                    target_cell_count=row["target_cell_count"],
                    status=row["status"],
                    created_at=row["created_at"],
                )
                stores.organs.setdefault(organ.organism_id, []).append(organ)

            for row in await connection.fetch("SELECT * FROM tissues ORDER BY created_at"):
                tissue = TissueRecord(
                    tissue_id=row["tissue_id"],
                    organism_id=row["organism_id"],
                    organ_id=row["organ_id"],
                    name=row["name"],
                    target_cell_count=row["target_cell_count"],
                    created_at=row["created_at"],
                )
                stores.tissues.setdefault(tissue.organism_id, []).append(tissue)

            for row in await connection.fetch("SELECT * FROM cell_divisions ORDER BY created_at"):
                division = CellDivisionRecord(
                    division_id=row["division_id"],
                    organism_id=row["organism_id"],
                    parent_cell_id=row["parent_cell_id"],
                    daughter_cell_ids=_decode_json(row["daughter_cell_ids"]),
                    mode=row["mode"],
                    genome_copied=row["genome_copied"],
                    organelles_duplicated=row["organelles_duplicated"],
                    created_at=row["created_at"],
                )
                stores.cell_divisions.setdefault(division.organism_id, []).append(division)

            for row in await connection.fetch("SELECT * FROM food_intakes ORDER BY created_at"):
                food = FoodIntake(
                    food_id=row["food_id"],
                    organism_id=row["organism_id"],
                    zygote_id=row["zygote_id"],
                    food_type=row["food_type"],
                    payload=_decode_json(row["payload"]),
                    routed_to=_decode_json(row["routed_to"]),
                    created_at=row["created_at"],
                )
                stores.food_intakes.setdefault(food.organism_id or food.zygote_id or "global", []).append(food)

            for row in await connection.fetch("SELECT * FROM oxygen_profiles"):
                oxygen = OxygenProfile(
                    oxygen_id=row["oxygen_id"],
                    organism_id=row["organism_id"],
                    zygote_id=row["zygote_id"],
                    compute_units=row["compute_units"],
                    memory_units=row["memory_units"],
                    storage_units=row["storage_units"],
                    gpu_units=row["gpu_units"],
                    restricted=row["restricted"],
                    updated_at=row["updated_at"],
                )
                stores.oxygen_profiles[oxygen.oxygen_id] = oxygen

            for row in await connection.fetch("SELECT * FROM umbilical_cords ORDER BY created_at"):
                cord = UmbilicalCord(
                    cord_id=row["cord_id"],
                    zygote_id=row["zygote_id"],
                    mother_organism_id=row["mother_organism_id"],
                    oxygen_profile_id=row["oxygen_profile_id"],
                    status=row["status"],
                    created_at=row["created_at"],
                )
                stores.umbilical_cords[cord.zygote_id] = cord

            for row in await connection.fetch("SELECT * FROM soul_snapshots ORDER BY created_at"):
                soul = SoulSnapshot(
                    soul_id=row["soul_id"],
                    organism_id=row["organism_id"],
                    snapshot=_decode_json(row["snapshot"]),
                    reincarnated_organism_id=row["reincarnated_organism_id"],
                    created_at=row["created_at"],
                )
                stores.souls[soul.soul_id] = soul

            for row in await connection.fetch("SELECT * FROM bone_structures ORDER BY created_at"):
                bone = BoneStructureRecord(
                    bone_id=row["bone_id"],
                    owner_user_id=row["owner_user_id"],
                    name=row["name"],
                    structure_type=row["structure_type"],
                    definition=_decode_json(row["definition"]),
                    status=row["status"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                stores.bone_structures[bone.bone_id] = bone

            for row in await connection.fetch("SELECT * FROM structure_proposals ORDER BY created_at"):
                proposal = StructureProposal(
                    proposal_id=row["proposal_id"],
                    owner_user_id=row["owner_user_id"],
                    requested_by=row["requested_by"],
                    name=row["name"],
                    structure_type=row["structure_type"],
                    definition=_decode_json(row["definition"]),
                    status=row["status"],
                    decision_reason=row["decision_reason"],
                    created_at=row["created_at"],
                    decided_at=row["decided_at"],
                )
                stores.structure_proposals[proposal.proposal_id] = proposal

            for row in await connection.fetch("SELECT * FROM organelle_pipelines ORDER BY created_at"):
                pipeline = OrganellePipeline(
                    pipeline_id=row["pipeline_id"],
                    organism_id=row["organism_id"],
                    cell_id=row["cell_id"],
                    stages=_decode_json(row["stages"]),
                    status=row["status"],
                    created_at=row["created_at"],
                )
                stores.organelle_pipelines.setdefault(pipeline.organism_id, []).append(pipeline)

            for row in await connection.fetch("SELECT * FROM vesicle_messages ORDER BY created_at"):
                message = VesicleMessage(
                    vesicle_id=row["vesicle_id"],
                    organism_id=row["organism_id"],
                    source_cell_id=row["source_cell_id"],
                    target_cell_id=row["target_cell_id"],
                    payload=_decode_json(row["payload"]),
                    status=row["status"],
                    created_at=row["created_at"],
                )
                stores.vesicle_messages.setdefault(message.organism_id, []).append(message)

            for row in await connection.fetch("SELECT * FROM cytoskeleton_topologies ORDER BY updated_at"):
                topology = CytoskeletonTopology(
                    topology_id=row["topology_id"],
                    organism_id=row["organism_id"],
                    organ_edges=_decode_json(row["organ_edges"]),
                    tissue_edges=_decode_json(row["tissue_edges"]),
                    cell_edges=_decode_json(row["cell_edges"]),
                    updated_at=row["updated_at"],
                )
                stores.cytoskeleton[topology.organism_id] = topology

        stores.genomes.setdefault("genome-default", Genome(genome_id="genome-default"))
        return stores

    async def save_stores(self, stores: RuntimeStores) -> None:
        async with self._pool.acquire() as connection:
            async with connection.transaction():
                for genome in stores.genomes.values():
                    await connection.execute(
                        """
                        INSERT INTO genomes (
                            genome_id, version, core_instruction_set, modules,
                            regulatory_rules, capability_registry, constraints
                        )
                        VALUES ($1, $2, $3::jsonb, $4::jsonb, $5::jsonb, $6::jsonb, $7::jsonb)
                        ON CONFLICT (genome_id) DO UPDATE SET
                            version = EXCLUDED.version,
                            core_instruction_set = EXCLUDED.core_instruction_set,
                            modules = EXCLUDED.modules,
                            regulatory_rules = EXCLUDED.regulatory_rules,
                            capability_registry = EXCLUDED.capability_registry,
                            constraints = EXCLUDED.constraints
                        """,
                        genome.genome_id,
                        genome.version,
                        _json(genome.core_instruction_set),
                        _json([module.model_dump(mode="json") for module in genome.modules]),
                        _json(genome.regulatory_rules),
                        _json(genome.capability_registry),
                        _json(genome.constraints),
                    )

                for organism in stores.organisms.values():
                    await connection.execute(
                        """
                        INSERT INTO organisms (
                            organism_id, owner_user_id, lifecycle_state, identity_profile,
                            long_term_memory, goals, policies, organ_registry, tissue_templates,
                            cell_blueprints, genome_id, development_stage, growth_state, lineage_log,
                            last_state_snapshot, created_at, updated_at
                        )
                        VALUES (
                            $1, $2, $3, $4::jsonb, $5::jsonb, $6::jsonb, $7::jsonb,
                            $8::jsonb, $9::jsonb, $10::jsonb, $11, $12, $13::jsonb, $14::jsonb, $15::jsonb, $16, $17
                        )
                        ON CONFLICT (organism_id) DO UPDATE SET
                            owner_user_id = EXCLUDED.owner_user_id,
                            lifecycle_state = EXCLUDED.lifecycle_state,
                            identity_profile = EXCLUDED.identity_profile,
                            long_term_memory = EXCLUDED.long_term_memory,
                            goals = EXCLUDED.goals,
                            policies = EXCLUDED.policies,
                            organ_registry = EXCLUDED.organ_registry,
                            tissue_templates = EXCLUDED.tissue_templates,
                            cell_blueprints = EXCLUDED.cell_blueprints,
                            genome_id = EXCLUDED.genome_id,
                            development_stage = EXCLUDED.development_stage,
                            growth_state = EXCLUDED.growth_state,
                            lineage_log = EXCLUDED.lineage_log,
                            last_state_snapshot = EXCLUDED.last_state_snapshot,
                            updated_at = EXCLUDED.updated_at
                        """,
                        organism.organism_id,
                        organism.owner_user_id,
                        organism.lifecycle_state.value,
                        _json(organism.identity_profile),
                        _json(organism.long_term_memory),
                        _json(organism.goals),
                        _json(organism.policies),
                        _json(organism.organ_registry),
                        _json(organism.tissue_templates),
                        _json(organism.cell_blueprints),
                        organism.genome_id,
                        organism.development_stage.value,
                        _json(organism.growth_state),
                        _json(organism.lineage_log),
                        _json(organism.last_state_snapshot),
                        organism.created_at,
                        organism.updated_at,
                    )

                for cells in stores.cells.values():
                    for cell in cells:
                        await connection.execute(
                            """
                            INSERT INTO cells (
                                cell_id, organism_id, organ_id, tissue_id, cell_type, cell_genome_id,
                                expression_profile, local_state, lifecycle_state, health_state,
                                health_score, parent_cell_id, generation, resource_budget, created_at, last_active_at
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9, $10, $11, $12, $13, $14::jsonb, $15, $16)
                            ON CONFLICT (cell_id) DO UPDATE SET
                                organism_id = EXCLUDED.organism_id,
                                organ_id = EXCLUDED.organ_id,
                                tissue_id = EXCLUDED.tissue_id,
                                cell_type = EXCLUDED.cell_type,
                                cell_genome_id = EXCLUDED.cell_genome_id,
                                expression_profile = EXCLUDED.expression_profile,
                                local_state = EXCLUDED.local_state,
                                lifecycle_state = EXCLUDED.lifecycle_state,
                                health_state = EXCLUDED.health_state,
                                health_score = EXCLUDED.health_score,
                                parent_cell_id = EXCLUDED.parent_cell_id,
                                generation = EXCLUDED.generation,
                                resource_budget = EXCLUDED.resource_budget,
                                last_active_at = EXCLUDED.last_active_at
                            """,
                            cell.cell_id,
                            cell.organism_id,
                            cell.organ_id,
                            cell.tissue_id,
                            cell.cell_type,
                            cell.cell_genome_id,
                            _json(cell.expression_profile),
                            _json(cell.local_state),
                            cell.lifecycle_state.value,
                            cell.health_state.value,
                            cell.health_score,
                            cell.parent_cell_id,
                            cell.generation,
                            _json(cell.resource_budget),
                            cell.created_at,
                            cell.last_active_at,
                        )

                for signals in stores.signals.values():
                    for signal in signals:
                        await connection.execute(
                            """
                            INSERT INTO signals (
                                signal_id, organism_id, actor, type, payload,
                                context_refs, priority, metadata, created_at
                            )
                            VALUES ($1, $2, $3::jsonb, $4, $5::jsonb, $6::jsonb, $7, $8::jsonb, $9)
                            ON CONFLICT (signal_id) DO UPDATE SET
                                actor = EXCLUDED.actor,
                                type = EXCLUDED.type,
                                payload = EXCLUDED.payload,
                                context_refs = EXCLUDED.context_refs,
                                priority = EXCLUDED.priority,
                                metadata = EXCLUDED.metadata
                            """,
                            signal.signal_id,
                            signal.organism_id,
                            _json(signal.actor),
                            signal.type,
                            _json(signal.payload),
                            _json(signal.context_refs),
                            signal.priority,
                            _json(signal.metadata),
                            signal.created_at,
                        )

                for proteins in stores.proteins.values():
                    for protein in proteins:
                        await connection.execute(
                            """
                            INSERT INTO proteins (
                                protein_id, organism_id, source_signal_id, type, payload,
                                confidence, status, validation_report, created_at
                            )
                            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8::jsonb, $9)
                            ON CONFLICT (protein_id) DO UPDATE SET
                                payload = EXCLUDED.payload,
                                confidence = EXCLUDED.confidence,
                                status = EXCLUDED.status,
                                validation_report = EXCLUDED.validation_report
                            """,
                            protein.protein_id,
                            protein.organism_id,
                            protein.source_signal_id,
                            protein.type,
                            _json(protein.payload),
                            protein.confidence,
                            protein.status.value,
                            _json(protein.validation_report),
                            protein.created_at,
                        )

                for contract in stores.contracts.values():
                    await connection.execute(
                        """
                        INSERT INTO contracts (
                            contract_id, owner_user_id, name, schema, allowed_actions,
                            permissions, rate_limits, dependencies, created_by, deprecated_reason,
                            status, usage_count, created_at, updated_at
                        )
                        VALUES (
                            $1, $2, $3, $4::jsonb, $5::jsonb, $6::jsonb, $7::jsonb,
                            $8::jsonb, $9, $10, $11, $12, $13, $14
                        )
                        ON CONFLICT (contract_id) DO UPDATE SET
                            owner_user_id = EXCLUDED.owner_user_id,
                            name = EXCLUDED.name,
                            schema = EXCLUDED.schema,
                            allowed_actions = EXCLUDED.allowed_actions,
                            permissions = EXCLUDED.permissions,
                            rate_limits = EXCLUDED.rate_limits,
                            dependencies = EXCLUDED.dependencies,
                            created_by = EXCLUDED.created_by,
                            deprecated_reason = EXCLUDED.deprecated_reason,
                            status = EXCLUDED.status,
                            usage_count = EXCLUDED.usage_count,
                            updated_at = EXCLUDED.updated_at
                        """,
                        contract.contract_id,
                        contract.owner_user_id,
                        contract.name,
                        _json(contract.contract_schema),
                        _json(contract.allowed_actions),
                        _json(contract.permissions),
                        _json(contract.rate_limits),
                        _json(contract.dependencies),
                        contract.created_by,
                        contract.deprecated_reason,
                        contract.status.value,
                        contract.usage_count,
                        contract.created_at,
                        contract.updated_at,
                    )

                for events in stores.events.values():
                    for event in events:
                        await connection.execute(
                            """
                            INSERT INTO runtime_events (
                                event_id, organism_id, cell_id, signal_id, protein_id,
                                contract_id, type, message, values, created_at
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10)
                            ON CONFLICT (event_id) DO NOTHING
                            """,
                            event.event_id,
                            event.organism_id,
                            event.cell_id,
                            event.signal_id,
                            event.protein_id,
                            event.contract_id,
                            event.type.value,
                            event.message,
                            _json(event.values),
                            event.created_at,
                        )

                for requests in stores.structure_requests.values():
                    for request in requests:
                        await connection.execute(
                            """
                            INSERT INTO structure_requests (
                                request_id, organism_id, signal_id, requested_contract,
                                reason, status, created_at
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            ON CONFLICT (request_id) DO UPDATE SET
                                signal_id = EXCLUDED.signal_id,
                                requested_contract = EXCLUDED.requested_contract,
                                reason = EXCLUDED.reason,
                                status = EXCLUDED.status
                            """,
                            request.request_id,
                            request.organism_id,
                            request.signal_id,
                            request.requested_contract,
                            request.reason,
                            request.status,
                            request.created_at,
                        )

                for zygote in stores.zygotes.values():
                    await connection.execute(
                        """
                        INSERT INTO zygotes (
                            zygote_id, owner_user_id, mother_organism_id, father_organism_id,
                            genome, stage, oxygen_restricted, food_log, founder_plan,
                            born_organism_id, created_at, updated_at
                        )
                        VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8::jsonb, $9::jsonb, $10, $11, $12)
                        ON CONFLICT (zygote_id) DO UPDATE SET
                            stage = EXCLUDED.stage,
                            oxygen_restricted = EXCLUDED.oxygen_restricted,
                            food_log = EXCLUDED.food_log,
                            founder_plan = EXCLUDED.founder_plan,
                            born_organism_id = EXCLUDED.born_organism_id,
                            updated_at = EXCLUDED.updated_at
                        """,
                        zygote.zygote_id,
                        zygote.owner_user_id,
                        zygote.mother_organism_id,
                        zygote.father_organism_id,
                        _json(zygote.genome),
                        zygote.stage.value,
                        zygote.oxygen_restricted,
                        _json(zygote.food_log),
                        _json(zygote.founder_plan),
                        zygote.born_organism_id,
                        zygote.created_at,
                        zygote.updated_at,
                    )

                for organs in stores.organs.values():
                    for organ in organs:
                        await connection.execute(
                            """
                            INSERT INTO organs (organ_id, organism_id, name, target_cell_count, status, created_at)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT (organism_id, organ_id) DO UPDATE SET
                                name = EXCLUDED.name,
                                target_cell_count = EXCLUDED.target_cell_count,
                                status = EXCLUDED.status
                            """,
                            organ.organ_id,
                            organ.organism_id,
                            organ.name,
                            organ.target_cell_count,
                            organ.status.value,
                            organ.created_at,
                        )

                for tissues in stores.tissues.values():
                    for tissue in tissues:
                        await connection.execute(
                            """
                            INSERT INTO tissues (tissue_id, organism_id, organ_id, name, target_cell_count, created_at)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            ON CONFLICT (organism_id, tissue_id) DO UPDATE SET
                                organ_id = EXCLUDED.organ_id,
                                name = EXCLUDED.name,
                                target_cell_count = EXCLUDED.target_cell_count
                            """,
                            tissue.tissue_id,
                            tissue.organism_id,
                            tissue.organ_id,
                            tissue.name,
                            tissue.target_cell_count,
                            tissue.created_at,
                        )

                for divisions in stores.cell_divisions.values():
                    for division in divisions:
                        await connection.execute(
                            """
                            INSERT INTO cell_divisions (
                                division_id, organism_id, parent_cell_id, daughter_cell_ids,
                                mode, genome_copied, organelles_duplicated, created_at
                            )
                            VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8)
                            ON CONFLICT (division_id) DO UPDATE SET
                                daughter_cell_ids = EXCLUDED.daughter_cell_ids,
                                mode = EXCLUDED.mode,
                                genome_copied = EXCLUDED.genome_copied,
                                organelles_duplicated = EXCLUDED.organelles_duplicated
                            """,
                            division.division_id,
                            division.organism_id,
                            division.parent_cell_id,
                            _json(division.daughter_cell_ids),
                            division.mode.value,
                            division.genome_copied,
                            division.organelles_duplicated,
                            division.created_at,
                        )

                for foods in stores.food_intakes.values():
                    for food in foods:
                        await connection.execute(
                            """
                            INSERT INTO food_intakes (food_id, organism_id, zygote_id, food_type, payload, routed_to, created_at)
                            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7)
                            ON CONFLICT (food_id) DO UPDATE SET
                                payload = EXCLUDED.payload,
                                routed_to = EXCLUDED.routed_to
                            """,
                            food.food_id,
                            food.organism_id,
                            food.zygote_id,
                            food.food_type,
                            _json(food.payload),
                            _json(food.routed_to),
                            food.created_at,
                        )

                for oxygen in stores.oxygen_profiles.values():
                    await connection.execute(
                        """
                        INSERT INTO oxygen_profiles (
                            oxygen_id, organism_id, zygote_id, compute_units, memory_units,
                            storage_units, gpu_units, restricted, updated_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (oxygen_id) DO UPDATE SET
                            compute_units = EXCLUDED.compute_units,
                            memory_units = EXCLUDED.memory_units,
                            storage_units = EXCLUDED.storage_units,
                            gpu_units = EXCLUDED.gpu_units,
                            restricted = EXCLUDED.restricted,
                            updated_at = EXCLUDED.updated_at
                        """,
                        oxygen.oxygen_id,
                        oxygen.organism_id,
                        oxygen.zygote_id,
                        oxygen.compute_units,
                        oxygen.memory_units,
                        oxygen.storage_units,
                        oxygen.gpu_units,
                        oxygen.restricted,
                        oxygen.updated_at,
                    )

                for cord in stores.umbilical_cords.values():
                    await connection.execute(
                        """
                        INSERT INTO umbilical_cords (cord_id, zygote_id, mother_organism_id, oxygen_profile_id, status, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (cord_id) DO UPDATE SET
                            oxygen_profile_id = EXCLUDED.oxygen_profile_id,
                            status = EXCLUDED.status
                        """,
                        cord.cord_id,
                        cord.zygote_id,
                        cord.mother_organism_id,
                        cord.oxygen_profile_id,
                        cord.status,
                        cord.created_at,
                    )

                for soul in stores.souls.values():
                    await connection.execute(
                        """
                        INSERT INTO soul_snapshots (soul_id, organism_id, snapshot, reincarnated_organism_id, created_at)
                        VALUES ($1, $2, $3::jsonb, $4, $5)
                        ON CONFLICT (soul_id) DO UPDATE SET
                            snapshot = EXCLUDED.snapshot,
                            reincarnated_organism_id = EXCLUDED.reincarnated_organism_id
                        """,
                        soul.soul_id,
                        soul.organism_id,
                        _json(soul.snapshot),
                        soul.reincarnated_organism_id,
                        soul.created_at,
                    )

                for bone in stores.bone_structures.values():
                    await connection.execute(
                        """
                        INSERT INTO bone_structures (bone_id, owner_user_id, name, structure_type, definition, status, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8)
                        ON CONFLICT (bone_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            definition = EXCLUDED.definition,
                            status = EXCLUDED.status,
                            updated_at = EXCLUDED.updated_at
                        """,
                        bone.bone_id,
                        bone.owner_user_id,
                        bone.name,
                        bone.structure_type,
                        _json(bone.definition),
                        bone.status.value,
                        bone.created_at,
                        bone.updated_at,
                    )

                for proposal in stores.structure_proposals.values():
                    await connection.execute(
                        """
                        INSERT INTO structure_proposals (
                            proposal_id, owner_user_id, requested_by, name, structure_type,
                            definition, status, decision_reason, created_at, decided_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9, $10)
                        ON CONFLICT (proposal_id) DO UPDATE SET
                            definition = EXCLUDED.definition,
                            status = EXCLUDED.status,
                            decision_reason = EXCLUDED.decision_reason,
                            decided_at = EXCLUDED.decided_at
                        """,
                        proposal.proposal_id,
                        proposal.owner_user_id,
                        proposal.requested_by,
                        proposal.name,
                        proposal.structure_type,
                        _json(proposal.definition),
                        proposal.status,
                        proposal.decision_reason,
                        proposal.created_at,
                        proposal.decided_at,
                    )

                for pipelines in stores.organelle_pipelines.values():
                    for pipeline in pipelines:
                        await connection.execute(
                            """
                            INSERT INTO organelle_pipelines (pipeline_id, organism_id, cell_id, stages, status, created_at)
                            VALUES ($1, $2, $3, $4::jsonb, $5, $6)
                            ON CONFLICT (pipeline_id) DO UPDATE SET
                                stages = EXCLUDED.stages,
                                status = EXCLUDED.status
                            """,
                            pipeline.pipeline_id,
                            pipeline.organism_id,
                            pipeline.cell_id,
                            _json(pipeline.stages),
                            pipeline.status,
                            pipeline.created_at,
                        )

                for messages in stores.vesicle_messages.values():
                    for message in messages:
                        await connection.execute(
                            """
                            INSERT INTO vesicle_messages (vesicle_id, organism_id, source_cell_id, target_cell_id, payload, status, created_at)
                            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7)
                            ON CONFLICT (vesicle_id) DO UPDATE SET
                                target_cell_id = EXCLUDED.target_cell_id,
                                payload = EXCLUDED.payload,
                                status = EXCLUDED.status
                            """,
                            message.vesicle_id,
                            message.organism_id,
                            message.source_cell_id,
                            message.target_cell_id,
                            _json(message.payload),
                            message.status,
                            message.created_at,
                        )

                for topology in stores.cytoskeleton.values():
                    await connection.execute(
                        """
                        INSERT INTO cytoskeleton_topologies (topology_id, organism_id, organ_edges, tissue_edges, cell_edges, updated_at)
                        VALUES ($1, $2, $3::jsonb, $4::jsonb, $5::jsonb, $6)
                        ON CONFLICT (topology_id) DO UPDATE SET
                            organ_edges = EXCLUDED.organ_edges,
                            tissue_edges = EXCLUDED.tissue_edges,
                            cell_edges = EXCLUDED.cell_edges,
                            updated_at = EXCLUDED.updated_at
                        """,
                        topology.topology_id,
                        topology.organism_id,
                        _json(topology.organ_edges),
                        _json(topology.tissue_edges),
                        _json(topology.cell_edges),
                        topology.updated_at,
                    )


def _json(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, separators=(",", ":"))


def _decode_json(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value
