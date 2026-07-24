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
        "cell_execution_runs",
        "cell_execution_step_results",
        "bone_structures",
        "structure_proposals",
        "resource_grants",
    ]:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in schema
    for memory_column in [
        "memory_type",
        "source_run_id",
        "source_protein_ids",
        "importance",
        "admission_status",
        "content_hash",
        "ttl_seconds",
        "last_accessed_at",
        "access_count",
        "storage_resource_id",
    ]:
        assert memory_column in schema
