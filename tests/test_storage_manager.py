from preon_systems_cell.storage.repositories import GLOBAL_RUNTIME_STORES


def test_global_runtime_store_starts_empty():
    assert GLOBAL_RUNTIME_STORES.organisms == {}
