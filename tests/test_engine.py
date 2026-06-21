from preon_systems_cell.engine import OrganismRuntime, ProteinPipeline, safe_calculate
from preon_systems_cell.models import (
    Actor,
    ExecutionStrategy,
    Genome,
    GenomeModule,
    MisfoldingType,
    OrganismRecord,
    Protein,
    ProteinStatus,
    ResourceBudget,
    Signal,
)


def test_calculator_is_deterministic_and_restricted():
    assert safe_calculate("2 * (3 + 4)") == 14.0


def test_runtime_wake_and_hibernate_preserve_identity():
    runtime = OrganismRuntime()
    organism = runtime.create_organism(OrganismRecord(organism_id="organism-test", goals=["preserve identity"]))

    woke = runtime.wake(organism.organism_id)
    slept = runtime.hibernate(organism.organism_id)

    assert woke.lifecycle_state == "active"
    assert slept.lifecycle_state == "hibernated"
    assert slept.goals == ["preserve identity"]
    assert "cells" in slept.last_state_snapshot


def test_membrane_rejects_unauthorized_actor():
    runtime = OrganismRuntime()
    organism = runtime.create_organism(OrganismRecord(organism_id="organism-auth"))
    signal = Signal(
        signal_id="signal-auth",
        organism_id=organism.organism_id,
        actor=Actor(actor_id="guest", roles=["guest"]),
        type="calculate",
        payload={"expression": "1+1"},
    )

    decision, _, protein, _, _ = runtime.submit_signal(signal)

    assert decision.code == "UNAUTHORIZED"
    assert protein is None


def test_nucleus_selects_module_from_expression_profile():
    runtime = OrganismRuntime()
    organism = runtime.create_organism(OrganismRecord(organism_id="organism-expression", genome_id="genome-expression"))
    runtime.stores.genomes[organism.genome_id] = Genome(
        genome_id=organism.genome_id,
        modules=[
            GenomeModule(module_id="low_reasoning", signal_types=["query"], execution_strategy=ExecutionStrategy.LLM_STUB),
            GenomeModule(module_id="high_reasoning", signal_types=["query"], execution_strategy=ExecutionStrategy.LLM_STUB),
        ],
    )
    runtime.stores.cells[organism.organism_id][0] = runtime.stores.cells[organism.organism_id][0].model_copy(
        update={"expression_profile": {"low_reasoning": 0.1, "high_reasoning": 0.9}}
    )

    _, _, _, events, _ = runtime.submit_signal(
        Signal(signal_id="signal-expression", organism_id=organism.organism_id, type="query", payload={"prompt": "status"})
    )

    nucleus_event = next(event for event in events if event.type == "nucleus")
    assert nucleus_event.values["module_id"] == "high_reasoning"


def test_mitochondria_blocks_exhausted_compute_budget():
    runtime = OrganismRuntime()
    organism = runtime.create_organism(OrganismRecord(organism_id="organism-quota"))
    runtime.stores.cells[organism.organism_id][0] = runtime.stores.cells[organism.organism_id][0].model_copy(
        update={"resource_budget": ResourceBudget(compute_units=0, tool_calls=1)}
    )

    _, _, protein, events, _ = runtime.submit_signal(
        Signal(signal_id="signal-quota", organism_id=organism.organism_id, type="calculate", payload={"expression": "1+1"})
    )

    assert protein is not None
    assert protein.status == ProteinStatus.DROPPED
    assert MisfoldingType.EXECUTION in protein.validation_report.misfolding_types
    assert any(event.type == "protein" and event.values["status"] == "dropped" for event in events)
    assert any(event.type == "mitochondria" and event.values["reserved"] is False for event in events)


def test_protein_pipeline_marks_toxic_output_blocked():
    protein = Protein(
        protein_id="protein-toxic",
        organism_id="organism-toxic",
        source_signal_id="signal-toxic",
        type="query.result",
        payload={"result": "delete all records"},
    )
    signal = Signal(signal_id="signal-toxic", organism_id="organism-toxic", type="query", payload={"prompt": "status"})

    validated = ProteinPipeline().validate(protein, signal)

    assert validated.status == ProteinStatus.BLOCKED
    assert MisfoldingType.TOXIC in validated.validation_report.misfolding_types
