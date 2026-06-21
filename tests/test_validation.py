from pydantic import ValidationError

from preon_systems_cell.models import CellRecord, Genome, OrganismRecord, Signal


def test_core_runtime_models_validate_minimum_shapes():
    organism = OrganismRecord(organism_id="organism-1")
    cell = CellRecord(cell_id="cell-1", organism_id=organism.organism_id)
    signal = Signal(signal_id="signal-1", organism_id=organism.organism_id, type="query", payload={"prompt": "hello"})
    genome = Genome(genome_id=organism.genome_id)

    assert organism.lifecycle_state == "hibernated"
    assert cell.resource_budget.compute_units == 10
    assert signal.priority == 5
    assert genome.modules


def test_signal_requires_type():
    try:
        Signal(signal_id="signal-1", organism_id="organism-1", type="")
    except ValidationError as exc:
        assert "String should have at least 1 character" in str(exc)
    else:
        raise AssertionError("Signal accepted an empty type")
