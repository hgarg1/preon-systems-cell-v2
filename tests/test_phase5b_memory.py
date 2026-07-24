from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from preon_systems_cell.engine import OrganismRuntime, RuntimeStores, new_id
from preon_systems_cell.memory import ContextBuilder, canonical_content_hash
from preon_systems_cell.models import (
    Actor,
    DataClass,
    MemoryRecord,
    OrganismRecord,
    Protein,
    ProteinStatus,
    Signal,
    TraceContext,
)
from preon_systems_cell.storage.postgres import PostgresRuntimeStore


def _runtime(*, owner: str = "owner-1") -> tuple[OrganismRuntime, OrganismRecord]:
    runtime = OrganismRuntime()
    organism = runtime.create_organism(
        OrganismRecord(organism_id=new_id("organism"), owner_user_id=owner)
    )
    return runtime, organism


def _signal(
    organism_id: str,
    *,
    prompt: str = "How should PostgreSQL backups be retained?",
    data_class: DataClass = DataClass.INTERNAL,
    memory: dict | None = None,
) -> Signal:
    return Signal(
        signal_id=new_id("signal"),
        organism_id=organism_id,
        actor=Actor(actor_id="owner-1", roles=["operator"]),
        type="query",
        payload={"prompt": prompt},
        data_class=data_class,
        trace_context=TraceContext(organism_id=organism_id),
        metadata={"memory": memory} if memory is not None else {},
    )


def _protein(organism_id: str, signal_id: str, *, confidence: float = 0.9) -> Protein:
    return Protein(
        protein_id=new_id("protein"),
        organism_id=organism_id,
        source_signal_id=signal_id,
        type="reasoning",
        payload={"answer": "Retain encrypted PostgreSQL backups for thirty days."},
        confidence=confidence,
        status=ProteinStatus.APPROVED,
    )


def test_routine_output_is_not_automatically_admitted() -> None:
    runtime, organism = _runtime()
    signal = _signal(organism.organism_id)
    protein = _protein(organism.organism_id, signal.signal_id)

    assert runtime.write_memory_from_protein(signal, protein) is None
    assert runtime.stores.memory_records.get(organism.organism_id, []) == []
    event = runtime.stores.events[organism.organism_id][-1]
    assert event.values["reason"] == "not_marked_as_memory_candidate"


def test_policy_admission_preserves_provenance_and_grows_storage() -> None:
    runtime, organism = _runtime()
    signal = _signal(
        organism.organism_id,
        memory={"admit": True, "importance": 0.8, "type": "semantic", "ttl_seconds": 3600},
    )
    protein = _protein(organism.organism_id, signal.signal_id)

    memory = runtime.write_memory_from_protein(signal, protein)

    assert memory is not None
    assert memory.memory_type == "semantic"
    assert memory.source_signal_id == signal.signal_id
    assert memory.source_protein_ids == [protein.protein_id]
    assert memory.trace_context == signal.trace_context
    assert memory.importance == 0.8
    assert memory.ttl_seconds == 3600
    assert memory.storage_resource_id in runtime.stores.bone_structures
    resource = runtime.stores.bone_structures[memory.storage_resource_id or ""]
    assert resource.name == "organism-memory"
    assert resource.organism_id == organism.organism_id
    assert any(
        grant.resource_id == resource.bone_id and grant.organism_id == organism.organism_id
        for grant in runtime.stores.resource_grants.values()
    )


def test_admission_rejects_low_confidence_duplicates_and_unreviewed_invalid_sources() -> None:
    runtime, organism = _runtime()
    candidate = {"admit": True, "importance": 0.9, "type": "semantic"}
    low_signal = _signal(organism.organism_id, memory=candidate)
    assert runtime.write_memory_from_protein(
        low_signal,
        _protein(organism.organism_id, low_signal.signal_id, confidence=0.2),
    ) is None

    accepted_signal = _signal(organism.organism_id, memory=candidate)
    accepted = runtime.write_memory_from_protein(
        accepted_signal,
        _protein(organism.organism_id, accepted_signal.signal_id),
    )
    assert accepted is not None

    duplicate_signal = _signal(organism.organism_id, memory=candidate)
    assert runtime.write_memory_from_protein(
        duplicate_signal,
        _protein(organism.organism_id, duplicate_signal.signal_id),
    ) is None

    invalidated = _signal(organism.organism_id, memory=candidate).model_copy(
        update={"metadata": {"memory": candidate, "source_invalidated": True}}
    )
    assert runtime.write_memory_from_protein(
        invalidated,
        Protein(
            **{
                **_protein(organism.organism_id, invalidated.signal_id).model_dump(),
                "payload": {"answer": "different invalid source"},
            }
        ),
    ) is None


def test_context_is_relevant_bounded_owner_scoped_and_class_aware() -> None:
    now = datetime.now(UTC)
    owner = "owner-1"
    relevant = MemoryRecord(
        memory_id="memory-relevant",
        organism_id="organism-1",
        owner_user_id=owner,
        kind="query",
        memory_type="semantic",
        payload={"topic": "PostgreSQL backup retention"},
        content_hash="relevant",
        importance=0.9,
        confidence=0.95,
        created_at=now,
    )
    irrelevant = relevant.model_copy(
        update={
            "memory_id": "memory-irrelevant",
            "kind": "note",
            "payload": {"topic": "orchid watering schedule"},
            "content_hash": "irrelevant",
        }
    )
    confidential = relevant.model_copy(
        update={
            "memory_id": "memory-confidential",
            "data_class": DataClass.CONFIDENTIAL,
            "content_hash": "confidential",
        }
    )
    other_owner = relevant.model_copy(
        update={"memory_id": "memory-other", "owner_user_id": "owner-2", "content_hash": "other"}
    )
    expired = relevant.model_copy(
        update={
            "memory_id": "memory-expired",
            "content_hash": "expired",
            "ttl_seconds": 1,
            "created_at": now - timedelta(seconds=5),
        }
    )
    signal = Signal(
        signal_id="signal-1",
        organism_id="organism-1",
        type="query",
        payload={"prompt": "PostgreSQL backup retention policy"},
        data_class=DataClass.INTERNAL,
    )

    snapshot = ContextBuilder().build(
        signal,
        [irrelevant, confidential, other_owner, expired, relevant],
        owner_user_id=owner,
        token_budget=256,
        now=now,
    )

    assert [memory.memory_id for memory in snapshot.memories] == ["memory-relevant"]
    assert snapshot.token_count <= snapshot.token_budget

    tiny = ContextBuilder().build(
        signal,
        [relevant],
        owner_user_id=owner,
        token_budget=1,
        now=now,
    )
    assert tiny.memories == []
    assert tiny.truncated is True


def test_context_access_is_recorded_only_for_injected_memory() -> None:
    runtime, organism = _runtime()
    relevant = runtime.create_memory(
        MemoryRecord(
            memory_id="memory-relevant",
            organism_id=organism.organism_id,
            kind="query",
            memory_type="semantic",
            payload={"topic": "PostgreSQL backup retention"},
            importance=0.9,
        )
    )
    irrelevant = runtime.create_memory(
        MemoryRecord(
            memory_id="memory-irrelevant",
            organism_id=organism.organism_id,
            kind="note",
            memory_type="semantic",
            payload={"topic": "orchid watering"},
            importance=0.9,
        )
    )

    snapshot = runtime.build_memory_context(_signal(organism.organism_id), token_budget=256)
    records = {item.memory_id: item for item in runtime.stores.memory_records[organism.organism_id]}

    assert [item.memory_id for item in snapshot.memories] == [relevant.memory_id]
    assert records[relevant.memory_id].access_count == 1
    assert records[relevant.memory_id].last_accessed_at is not None
    assert records[irrelevant.memory_id].access_count == 0
    assert records[irrelevant.memory_id].last_accessed_at is None


def test_manual_supersession_and_lifecycle_maintenance_are_auditable() -> None:
    runtime, organism = _runtime()
    original = runtime.create_memory(
        MemoryRecord(
            memory_id="memory-v1",
            organism_id=organism.organism_id,
            kind="policy",
            memory_type="procedural",
            payload={"retention_days": 7},
            importance=0.9,
        )
    )
    replacement = runtime.create_memory(
        MemoryRecord(
            memory_id="memory-v2",
            organism_id=organism.organism_id,
            kind="policy",
            memory_type="procedural",
            payload={"retention_days": 30},
            importance=0.9,
            supersedes_memory_id=original.memory_id,
        )
    )
    records = {item.memory_id: item for item in runtime.stores.memory_records[organism.organism_id]}
    assert replacement.version == 2
    assert records[original.memory_id].status == "superseded"
    assert records[original.memory_id].superseded_by_memory_id == replacement.memory_id

    expired = MemoryRecord(
        memory_id="memory-expired",
        organism_id=organism.organism_id,
        owner_user_id=organism.owner_user_id,
        payload={"temporary": True},
        content_hash="expired",
        ttl_seconds=1,
        created_at=datetime.now(UTC) - timedelta(seconds=2),
    )
    stale = MemoryRecord(
        memory_id="memory-stale",
        organism_id=organism.organism_id,
        owner_user_id=organism.owner_user_id,
        payload={"low_value": True},
        content_hash="stale",
        importance=0.1,
        created_at=datetime.now(UTC) - timedelta(days=100),
    )
    runtime.stores.memory_records[organism.organism_id].extend([expired, stale])
    result = runtime.maintain_memory(organism.organism_id)
    records = {item.memory_id: item for item in runtime.stores.memory_records[organism.organism_id]}

    assert result["expired"] == 1
    assert result["deprecated"] == 1
    assert result["deleted"] == 0
    assert records["memory-expired"].status == "expired"
    assert records["memory-stale"].status == "deprecated"


def test_labeled_keyword_relevance_cases() -> None:
    now = datetime.now(UTC)
    cases = [
        ("postgres restore procedure", {"postgres", "restore"}, "memory-db"),
        ("customer refund policy", {"customer", "refund"}, "memory-refund"),
        ("rotate api credentials", {"api", "credentials"}, "memory-security"),
    ]
    memories = [
        MemoryRecord(
            memory_id=memory_id,
            organism_id="organism-1",
            owner_user_id="owner-1",
            kind="query",
            memory_type="procedural",
            payload={"keywords": sorted(keywords)},
            content_hash=memory_id,
            created_at=now,
        )
        for _query, keywords, memory_id in cases
    ]
    builder = ContextBuilder()

    for query, _keywords, expected_id in cases:
        snapshot = builder.build(
            Signal(
                signal_id=new_id("signal"),
                organism_id="organism-1",
                type="query",
                payload={"prompt": query},
            ),
            memories,
            owner_user_id="owner-1",
            token_budget=256,
            now=now,
        )
        assert snapshot.memories[0].memory_id == expected_id


def test_admitted_memory_is_injected_into_later_llm_execution() -> None:
    runtime, organism = _runtime()
    first = _signal(
        organism.organism_id,
        prompt="Remember the PostgreSQL backup policy",
        memory={"admit": True, "importance": 0.9, "type": "semantic"},
    )
    _decision, _cell, first_protein, _events, _structure = runtime.submit_signal(first)
    assert first_protein is not None
    assert len(runtime.stores.memory_records[organism.organism_id]) == 1

    later = _signal(organism.organism_id, prompt="What is the PostgreSQL backup policy?")
    _decision, _cell, later_protein, events, _structure = runtime.submit_signal(later)

    assert later_protein is not None
    assert "Relevant admitted organism context" in str(later_protein.payload["result"])
    context_event = next(
        event for event in events if event.message == "Deterministic context constructed"
    )
    assert context_event.values["count"] == 1
    assert context_event.values["token_count"] <= context_event.values["token_budget"]


def test_postgres_reload_reconstructs_phase5b_memory() -> None:
    now = datetime.now(UTC)
    row = {
        "memory_id": "memory-1",
        "organism_id": "organism-1",
        "owner_user_id": "owner-1",
        "scope": "organism",
        "kind": "policy",
        "memory_type": "semantic",
        "payload": {"retention": 30},
        "source_signal_id": "signal-1",
        "source_run_id": "run-1",
        "source_protein_ids": ["protein-1"],
        "confidence": 0.9,
        "importance": 0.8,
        "data_class": "confidential",
        "trace_context": {"request_id": "request-1", "organism_id": "organism-1"},
        "admission_status": "admitted",
        "promotion_reason": "policy_candidate_passed",
        "content_hash": canonical_content_hash({"retention": 30}),
        "ttl_seconds": 3600,
        "last_accessed_at": now,
        "access_count": 2,
        "supersedes_memory_id": None,
        "superseded_by_memory_id": None,
        "storage_resource_id": "bone-1",
        "status": "active",
        "version": 1,
        "updated_at": now,
        "created_at": now,
    }

    class Connection:
        async def fetch(self, query, *_args):
            return [row] if "FROM memory_records" in query else []

    class Acquire:
        async def __aenter__(self):
            return Connection()

        async def __aexit__(self, *_args):
            return None

    class Pool:
        def acquire(self):
            return Acquire()

    stores = asyncio.run(PostgresRuntimeStore(Pool()).load_stores())
    memory = stores.memory_records["organism-1"][0]

    assert memory.memory_type == "semantic"
    assert memory.source_run_id == "run-1"
    assert memory.source_protein_ids == ["protein-1"]
    assert memory.access_count == 2
    assert memory.data_class == DataClass.CONFIDENTIAL


def test_postgres_save_includes_full_phase5b_memory_shape() -> None:
    now = datetime.now(UTC)
    stores = RuntimeStores()
    stores.memory_records["organism-1"] = [
        MemoryRecord(
            memory_id="memory-1",
            organism_id="organism-1",
            owner_user_id="owner-1",
            kind="policy",
            memory_type="procedural",
            payload={"retention": 30},
            source_signal_id="signal-1",
            source_run_id="run-1",
            source_protein_ids=["protein-1"],
            confidence=0.9,
            importance=0.8,
            content_hash="hash-1",
            access_count=2,
            storage_resource_id="bone-1",
            created_at=now,
            updated_at=now,
        )
    ]
    calls: list[tuple[str, tuple]] = []

    class Transaction:
        async def __aenter__(self):
            return None

        async def __aexit__(self, *_args):
            return None

    class Connection:
        def transaction(self):
            return Transaction()

        async def execute(self, query, *args):
            calls.append((query, args))

    class Acquire:
        async def __aenter__(self):
            return Connection()

        async def __aexit__(self, *_args):
            return None

    class Pool:
        def acquire(self):
            return Acquire()

    asyncio.run(PostgresRuntimeStore(Pool()).save_stores(stores))
    query, args = next(item for item in calls if "INSERT INTO memory_records" in item[0])

    assert "source_run_id" in query
    assert "storage_resource_id" in query
    assert len(args) == 28
    assert args[8] == "run-1"
    assert args[22] == "bone-1"
