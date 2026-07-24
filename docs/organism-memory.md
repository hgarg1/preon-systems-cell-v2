# Durable Organism Memory and Context Construction

Phase 5B separates valid execution output from durable organism memory. Execution state remains in `CellWorkingState` and the execution-run ledger. Only explicitly admitted information crosses activation boundaries as `MemoryRecord`.

## Admission

An approved or repaired protein is necessary but not sufficient for automatic retention. The signal or protein must mark the output as a memory candidate, and the deterministic admission policy checks:

- confidence of at least `0.75`;
- importance of at least `0.50`;
- novelty against active memory content hashes;
- valid source state;
- reviewed override for redacted or invalidated sources.

A signal requests admission with metadata:

```json
{
  "memory": {
    "admit": true,
    "importance": 0.8,
    "type": "semantic",
    "ttl_seconds": 86400
  }
}
```

Operator-created memory is explicit manual admission and uses `promotion_reason="operator_admission"`.

## Memory model

Memory types are:

- `episodic`: an event or experience;
- `semantic`: durable facts or learned concepts;
- `procedural`: instructions, policy, or repeatable method.

Each record carries signal/run/protein and trace provenance, owner, data classification, confidence, importance, admission reason, canonical content hash, TTL, last access, access count, version, supersession links, and structural storage resource.

The first memory operation asks the Phase 5A skeleton to grow an `organism-memory` resource and issue a scoped read/write grant. Memory rows are organism state inside that structural resource; they are not bone records.

## Context construction

Before a protein invocation, `ContextBuilder`:

1. includes cell-local shared state;
2. filters for active, admitted, unexpired, owner-matching records;
3. blocks memory above the invocation's data classification;
4. scores keyword overlap, explicit references, kind, recency, importance, and confidence;
5. deduplicates content and applies stable ordering;
6. stops when the context token budget is exhausted.

Only injected records receive an incremented `access_count` and `last_accessed_at`. The selected context and budget are reported in a memory runtime event and included in an LLM prompt as supporting context, never as instructions.

Keyword retrieval is the accepted first mode. Embedding/vector retrieval is deferred.

## Lifecycle

- TTL changes active memory to `expired`.
- Manual replacement links versions and changes the previous record to `superseded`.
- Duplicate consolidation keeps the strongest active record and marks duplicates as superseded.
- A record may age into `deprecated` only when age and low importance accompany zero access; zero access alone never evicts memory.
- Maintenance never physically deletes records in Phase 5B.

## Versioned policy and invocation safety

Each organism has one active immutable memory-policy version. Admission,
retention, context budget, and baseline substrate authority come from that
version; admitted records retain its identifier.

Provider invocations keep instructions, user input, working state, and recalled
memory distinct. Admitted memory remains untrusted supporting data.

## API

- `GET /api/organisms/{organism_id}/memory`
- `POST /api/organisms/{organism_id}/memory`
- `GET /api/organisms/{organism_id}/memory/{memory_id}`
- `POST /api/organisms/{organism_id}/memory/{memory_id}/deprecate`
- `POST /api/organisms/{organism_id}/memory/maintenance`

All endpoints are owner-scoped. The organism detail and Memory inspector show provenance, admission, lifecycle, and access metadata.
