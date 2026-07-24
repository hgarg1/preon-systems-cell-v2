from __future__ import annotations

from dataclasses import dataclass, field

from preon_systems_cell.models import (
    BoneStructureRecord,
    Capability,
    CellDivisionRecord,
    CellExecutionRun,
    CellRecord,
    Contract,
    CytoskeletonTopology,
    FoodIntake,
    Genome,
    GenomeVersion,
    MaintenanceJobRun,
    MemoryPolicyVersion,
    MemoryRecord,
    OrganRecord,
    OrganellePipeline,
    OrganismRecord,
    OxygenProfile,
    PolicyVersion,
    Protein,
    ReplayRun,
    ResourceGrant,
    ReviewRequest,
    RuntimeAlert,
    RuntimeEvent,
    Signal,
    SoulSnapshot,
    StructuralEffect,
    StructureProposal,
    StructureRequest,
    TissueRecord,
    UmbilicalCord,
    VesicleMessage,
    ZygoteRecord,
)


@dataclass
class RuntimeStores:
    """In-memory adapter backing the runtime repository ports."""

    organisms: dict[str, OrganismRecord] = field(default_factory=dict)
    genomes: dict[str, Genome] = field(default_factory=dict)
    cells: dict[str, list[CellRecord]] = field(default_factory=dict)
    signals: dict[str, list[Signal]] = field(default_factory=dict)
    proteins: dict[str, list[Protein]] = field(default_factory=dict)
    contracts: dict[str, Contract] = field(default_factory=dict)
    events: dict[str, list[RuntimeEvent]] = field(default_factory=dict)
    structure_requests: dict[str, list[StructureRequest]] = field(default_factory=dict)
    memory_records: dict[str, list[MemoryRecord]] = field(default_factory=dict)
    memory_policy_versions: dict[str, list[MemoryPolicyVersion]] = field(default_factory=dict)
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
    resource_grants: dict[str, ResourceGrant] = field(default_factory=dict)
    structural_effects: dict[str, StructuralEffect] = field(default_factory=dict)
    organelle_pipelines: dict[str, list[OrganellePipeline]] = field(default_factory=dict)
    vesicle_messages: dict[str, list[VesicleMessage]] = field(default_factory=dict)
    cytoskeleton: dict[str, CytoskeletonTopology] = field(default_factory=dict)
    cell_execution_runs: dict[str, list[CellExecutionRun]] = field(default_factory=dict)
    skeletal_execution_runs: dict[str, list[CellExecutionRun]] = field(default_factory=dict)
    actor_counts: dict[tuple[str, str], int] = field(default_factory=dict)
