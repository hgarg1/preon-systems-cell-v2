from pathlib import Path


SCHEMA_PATH = Path("preon_systems_cell/storage/sql/schema.sql")


def test_postgres_schema_defines_organism_runtime_tables():
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    for table in [
        "organisms",
        "cells",
        "genomes",
        "signals",
        "proteins",
        "contracts",
        "runtime_events",
        "memory_records",
        "structure_requests",
        "capabilities",
        "genome_versions",
        "replay_runs",
        "policy_versions",
        "maintenance_runs",
        "runtime_alerts",
        "review_requests",
    ]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in schema
