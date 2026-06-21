from preon_systems_cell.api import create_organism, submit_signal
from preon_systems_cell.models import CreateOrganismRequest, SubmitSignalRequest


def test_runtime_events_are_the_primary_analytics_stream():
    organism = create_organism(CreateOrganismRequest())
    response = submit_signal(organism.organism_id, SubmitSignalRequest(type="calculate", payload={"expression": "3+4"}))

    assert response is not None
    assert [event.type for event in response.events] == [
        "membrane",
        "lifecycle",
        "cytoplasm",
        "nucleus",
        "mitochondria",
        "ribosome",
        "bone",       # Osteocyte records bone execution after ribosome
        "protein",
        "golgi",
        "lysosome",
        "vacuole",
        "memory",
    ]
